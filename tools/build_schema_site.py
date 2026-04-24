#!/usr/bin/env python3
"""
build_schema_site.py

Generate a static site tree suitable for publishing at https://schema.ion.id/.

Reads from:  schema/extensions/{layer}/{pack}/{version}/
Writes to:   dist/schema.ion.id/{layer}/{pack}/{version}/

Outputs per pack:
  - index.html           — human-readable rendering (docs + schema table)
  - context.jsonld       — verbatim copy
  - vocab.jsonld         — verbatim copy (if present)
  - attributes.yaml      — verbatim copy

Also generates:
  - dist/schema.ion.id/index.html       — top-level landing page, lists all packs
  - dist/schema.ion.id/sitemap.xml      — machine-discoverable list of URLs
  - dist/schema.ion.id/_headers         — content-negotiation hints for Cloudflare
                                          Pages / Netlify
  - dist/schema.ion.id/robots.txt       — opens the site to crawlers

URL CONVENTION (declared in ion.yaml x-ion-semantic-model.urlPattern):
  https://schema.ion.id/{layer}/{pack}/{version}/
  Example: https://schema.ion.id/logistics/offer/v1/

USAGE
  python3 tools/build_schema_site.py             # build into dist/schema.ion.id/
  python3 tools/build_schema_site.py --out <dir> # custom output directory
  python3 tools/build_schema_site.py --serve     # build + serve locally on :8080
"""

import argparse
import html
import http.server
import json
import shutil
import socketserver
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
EXT = ROOT / "schema" / "extensions"
SITE_ROOT = "https://schema.ion.id"


def iter_packs():
    for layer_dir in sorted(EXT.iterdir()):
        if not layer_dir.is_dir() or layer_dir.name.startswith("."):
            continue
        for pack_dir in sorted(layer_dir.iterdir()):
            if not pack_dir.is_dir():
                continue
            for version_dir in sorted(pack_dir.iterdir()):
                if not version_dir.is_dir() or not version_dir.name.startswith("v"):
                    continue
                yield {
                    "layer": layer_dir.name,
                    "pack": pack_dir.name,
                    "version": version_dir.name,
                    "src": version_dir,
                }


def read_readme(pack_src: Path) -> str:
    rm = pack_src / "README.md"
    if rm.exists():
        return rm.read_text(encoding="utf-8")
    return ""


def markdown_lite_to_html(md: str) -> str:
    """Very small markdown -> HTML for the README preview. Not a full renderer."""
    out = []
    in_table = False
    for line in md.splitlines():
        stripped = line.rstrip()
        if stripped.startswith("# "):
            out.append(f"<h1>{html.escape(stripped[2:])}</h1>")
        elif stripped.startswith("## "):
            out.append(f"<h2>{html.escape(stripped[3:])}</h2>")
        elif stripped.startswith("### "):
            out.append(f"<h3>{html.escape(stripped[4:])}</h3>")
        elif stripped.startswith("|") and stripped.endswith("|"):
            # naive table
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if not in_table:
                out.append("<table>")
                out.append("<thead><tr>" + "".join(f"<th>{html.escape(c)}</th>" for c in cells) + "</tr></thead><tbody>")
                in_table = "header-next"
            elif in_table == "header-next":
                # separator row
                if all(set(c) <= set("-: ") for c in cells):
                    in_table = True
                    continue
                in_table = True
                out.append("<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in cells) + "</tr>")
            else:
                out.append("<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in cells) + "</tr>")
        else:
            if in_table:
                out.append("</tbody></table>")
                in_table = False
            if stripped.startswith("- "):
                out.append(f"<li>{html.escape(stripped[2:])}</li>")
            elif stripped:
                out.append(f"<p>{html.escape(stripped)}</p>")
            else:
                out.append("")
    if in_table:
        out.append("</tbody></table>")
    return "\n".join(out)


def extract_schema_summary(attrs_path: Path):
    """Return {class_name: [(prop, mandatory, description), ...]} summary."""
    if not attrs_path.exists():
        return {}
    try:
        doc = yaml.safe_load(attrs_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    summary = {}
    for sname, sdef in (doc.get("components", {}).get("schemas", {}) or {}).items():
        if not isinstance(sdef, dict):
            continue
        rows = []
        for pname, pdef in (sdef.get("properties") or {}).items():
            if isinstance(pdef, dict):
                mand = pdef.get("x-ion-mandatory", "—")
                desc = pdef.get("description", "") or ""
                desc = " ".join(desc.split())[:120]
                rows.append((pname, mand, desc))
            else:
                rows.append((pname, "—", ""))
        summary[sname] = rows
    return summary


PACK_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{layer}/{pack}/{version} — schema.ion.id</title>
<meta name="description" content="ION vocabulary reference for {layer}/{pack} ({version})">
<link rel="alternate" type="application/ld+json" href="context.jsonld">
<link rel="alternate" type="application/yaml" href="attributes.yaml">
<style>
 body{{font-family:system-ui,-apple-system,sans-serif;max-width:960px;margin:2rem auto;padding:0 1rem;color:#1a1a1a;line-height:1.55}}
 h1{{border-bottom:1px solid #ddd;padding-bottom:.3rem;margin-bottom:.2rem}}
 h2{{margin-top:2rem;color:#444}}
 h3{{margin-top:1.5rem;color:#555}}
 .meta{{color:#666;font-size:.9rem;margin-bottom:2rem}}
 .meta code{{background:#f4f4f4;padding:.15rem .35rem;border-radius:3px}}
 .links{{margin:1rem 0;padding:.8rem 1rem;background:#f8f9fb;border-left:3px solid #2a7ade;border-radius:2px}}
 .links a{{display:inline-block;margin-right:1rem;color:#2a7ade;font-family:ui-monospace,Menlo,monospace;font-size:.9rem}}
 table{{border-collapse:collapse;width:100%;margin:1rem 0}}
 th,td{{text-align:left;padding:.4rem .6rem;border-bottom:1px solid #e5e5e5;vertical-align:top}}
 th{{background:#f4f4f4;font-weight:600}}
 code{{font-family:ui-monospace,Menlo,monospace;font-size:.9em}}
 .readme{{margin-top:2rem;padding-top:1.5rem;border-top:1px solid #eee}}
 .iri{{font-family:ui-monospace,Menlo,monospace;font-size:.85em;color:#666;word-break:break-all}}
 footer{{margin-top:3rem;padding-top:1.5rem;border-top:1px solid #eee;color:#888;font-size:.85rem}}
 li{{margin-left:1.5rem}}
</style>
</head>
<body>

<nav><a href="{root}/">schema.ion.id</a> &rsaquo; <a href="{root}/{layer}/">{layer}</a> &rsaquo; <a href="{root}/{layer}/{pack}/">{pack}</a> &rsaquo; <strong>{version}</strong></nav>

<h1>{title}</h1>
<p class="meta">Pack IRI: <code>{pack_iri}#</code> &nbsp;|&nbsp; Layer: <code>{layer_label}</code> &nbsp;|&nbsp; Version: <code>{version}</code></p>

<div class="links">
 <a href="context.jsonld">context.jsonld</a>
 <a href="attributes.yaml">attributes.yaml</a>
 {vocab_link}
</div>

{schema_section}

{readme_section}

<footer>
 Part of <a href="{root}/">schema.ion.id</a> — ION Network vocabulary.
 Built from <code>schema/extensions/{layer}/{pack}/{version}/</code> in the ion-network spec.
 Generated {generated_at}.
</footer>

</body>
</html>
"""


def render_pack_html(pack, schema_summary, readme_html):
    layer = pack["layer"]
    pname = pack["pack"]
    version = pack["version"]
    pack_iri = f"{SITE_ROOT}/{layer}/{pname}/{version}"

    LAYER_LABELS = {
        "core": "L4 — Cross-sector core",
        "trade": "L5 — Trade sector",
        "logistics": "L5 — Logistics sector",
    }
    layer_label = LAYER_LABELS.get(layer, layer)

    # Schema section
    if schema_summary:
        parts = []
        for cname, rows in schema_summary.items():
            parts.append(f"<h3>{html.escape(cname)}</h3>")
            parts.append(f'<p class="iri">IRI: {pack_iri}#{html.escape(cname)}</p>')
            if rows:
                parts.append("<table><thead><tr><th>Property</th><th>Mandatory</th><th>Description</th></tr></thead><tbody>")
                for p, m, d in rows:
                    parts.append(
                        f"<tr><td><code>{html.escape(p)}</code></td>"
                        f"<td>{html.escape(str(m))}</td>"
                        f"<td>{html.escape(d)}</td></tr>"
                    )
                parts.append("</tbody></table>")
            else:
                parts.append("<p><em>No properties defined.</em></p>")
        schema_section = "<h2>Schemas in this pack</h2>\n" + "\n".join(parts)
    else:
        schema_section = "<h2>Schemas in this pack</h2><p><em>This pack has no OpenAPI schema (state-machine or flow pack).</em></p>"

    readme_section = (
        f'<section class="readme"><h2>Pack README</h2>{readme_html}</section>'
        if readme_html.strip() else ""
    )

    vocab_link = ""
    if (pack["src"] / "vocab.jsonld").exists():
        vocab_link = '<a href="vocab.jsonld">vocab.jsonld</a>'

    title = f"{layer}/{pname}/{version}"
    return PACK_HTML.format(
        title=title,
        layer=layer,
        pack=pname,
        version=version,
        pack_iri=pack_iri,
        layer_label=layer_label,
        schema_section=schema_section,
        readme_section=readme_section,
        vocab_link=vocab_link,
        root=SITE_ROOT,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )


INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>schema.ion.id — ION Network Vocabulary</title>
<meta name="description" content="ION Network vocabulary — extension attribute types, policies, states, and error categories used across ION-network participants.">
<style>
 body{{font-family:system-ui,-apple-system,sans-serif;max-width:960px;margin:2rem auto;padding:0 1rem;color:#1a1a1a;line-height:1.55}}
 h1{{border-bottom:1px solid #ddd;padding-bottom:.3rem;margin-bottom:.2rem}}
 h2{{margin-top:2rem;color:#444}}
 .meta{{color:#666;font-size:.9rem;margin-bottom:2rem}}
 .packs-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:.8rem;margin-top:1rem}}
 .pack{{padding:.8rem 1rem;background:#f8f9fb;border-left:3px solid #2a7ade;border-radius:2px;text-decoration:none;color:#1a1a1a}}
 .pack:hover{{background:#eef3fa}}
 .pack code{{color:#2a7ade;font-family:ui-monospace,Menlo,monospace;font-size:.95rem}}
 .pack small{{display:block;color:#666;margin-top:.3rem}}
 section.layer{{margin-top:2.5rem}}
 footer{{margin-top:3rem;padding-top:1.5rem;border-top:1px solid #eee;color:#888;font-size:.85rem}}
</style>
</head>
<body>

<h1>schema.ion.id</h1>
<p class="meta">The ION Network vocabulary. Extension attribute types, policies, states, and error categories used across ION participants.</p>

<p>ION is built on <a href="https://spec.beckn.io">Beckn Protocol v2.0.0</a>. Beckn's core transport types live at <a href="https://schema.beckn.io">schema.beckn.io</a>. ION's extensions — Indonesian regulatory fields, sector-specific attributes, and ION-specific protocol extensions — live here.</p>

<p>Every pack is addressable at <code>https://schema.ion.id/{{layer}}/{{pack}}/{{version}}/</code>. Every term has a canonical IRI of the form <code>https://schema.ion.id/{{layer}}/{{pack}}/{{version}}#{{term}}</code>. Contexts are served as <code>application/ld+json</code>; human-readable pages render as <code>text/html</code>.</p>

{sections}

<footer>
 Part of the <a href="https://github.com/ion-network/ion-network">ion-network</a> specification.
 Built {total_packs} packs from ion-network {spec_version}. Generated {generated_at}.
</footer>

</body>
</html>
"""


def render_index(packs, spec_version):
    # Group by layer
    layers = {}
    for p in packs:
        layers.setdefault(p["layer"], []).append(p)

    LAYER_HEADINGS = {
        "core": "L4 — Cross-sector core",
        "trade": "L5 — Trade sector",
        "logistics": "L5 — Logistics sector",
    }

    sections = []
    for layer in ("core", "trade", "logistics"):
        lps = layers.get(layer, [])
        if not lps:
            continue
        sections.append(f'<section class="layer"><h2>{html.escape(LAYER_HEADINGS.get(layer, layer))}</h2>')
        sections.append('<div class="packs-grid">')
        for p in sorted(lps, key=lambda x: (x["pack"], x["version"])):
            sections.append(
                f'<a class="pack" href="/{p["layer"]}/{p["pack"]}/{p["version"]}/">'
                f'<code>{html.escape(p["layer"])}/{html.escape(p["pack"])}/{html.escape(p["version"])}</code>'
                f'<small>{html.escape(p["layer"])} &middot; {html.escape(p["version"])}</small>'
                f'</a>'
            )
        sections.append("</div></section>")

    return INDEX_HTML.format(
        sections="\n".join(sections),
        total_packs=len(packs),
        spec_version=spec_version,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )


def render_sitemap(packs):
    urls = [SITE_ROOT + "/"]
    for p in packs:
        base = f"{SITE_ROOT}/{p['layer']}/{p['pack']}/{p['version']}/"
        urls.append(base)
        urls.append(base + "context.jsonld")
        urls.append(base + "attributes.yaml")
        if (p["src"] / "vocab.jsonld").exists():
            urls.append(base + "vocab.jsonld")
    body = '<?xml version="1.0" encoding="UTF-8"?>\n'
    body += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u in urls:
        body += f"  <url><loc>{html.escape(u)}</loc></url>\n"
    body += "</urlset>\n"
    return body


HEADERS_FILE = """# Cloudflare Pages / Netlify _headers file
# Content negotiation hints for schema.ion.id

/*.jsonld
  Content-Type: application/ld+json; charset=utf-8
  Access-Control-Allow-Origin: *

/*.yaml
  Content-Type: application/yaml; charset=utf-8
  Access-Control-Allow-Origin: *

/*
  X-Robots-Tag: index, follow
"""

ROBOTS = """User-agent: *
Allow: /
Sitemap: {root}/sitemap.xml
""".format(root=SITE_ROOT)


def build(out_dir: Path):
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    spec_version = "v0.5.2-draft"
    try:
        ion_yaml = yaml.safe_load((ROOT / "schema" / "core" / "v2" / "api" / "v2.0.0" / "ion.yaml").read_text())
        spec_version = ion_yaml.get("x-ion-compatibility", {}).get("profileVersion", spec_version)
    except Exception:
        pass

    all_packs = list(iter_packs())

    for p in all_packs:
        target = out_dir / p["layer"] / p["pack"] / p["version"]
        target.mkdir(parents=True, exist_ok=True)

        # verbatim artefacts
        for fname in ("context.jsonld", "vocab.jsonld", "attributes.yaml"):
            src = p["src"] / fname
            if src.exists():
                shutil.copyfile(src, target / fname)

        # readme html
        readme_html = markdown_lite_to_html(read_readme(p["src"]))

        # schema table
        schema_summary = extract_schema_summary(p["src"] / "attributes.yaml")

        index_html = render_pack_html(p, schema_summary, readme_html)
        (target / "index.html").write_text(index_html, encoding="utf-8")

    # root index
    (out_dir / "index.html").write_text(render_index(all_packs, spec_version), encoding="utf-8")
    (out_dir / "sitemap.xml").write_text(render_sitemap(all_packs), encoding="utf-8")
    (out_dir / "_headers").write_text(HEADERS_FILE, encoding="utf-8")
    (out_dir / "robots.txt").write_text(ROBOTS, encoding="utf-8")

    return len(all_packs)


def serve(out_dir: Path, port: int = 8080):
    import os
    os.chdir(out_dir)
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), Handler) as httpd:
        print(f"\nServing {out_dir} on http://localhost:{port}/")
        print("Press Ctrl-C to stop")
        httpd.serve_forever()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="dist/schema.ion.id",
                   help="Output directory (default: dist/schema.ion.id)")
    p.add_argument("--serve", action="store_true",
                   help="Build then start a local HTTP server on :8080")
    p.add_argument("--port", type=int, default=8080)
    args = p.parse_args()

    out = (ROOT / args.out).resolve()
    count = build(out)
    print(f"Built {count} pack(s) → {out}")

    if args.serve:
        serve(out, args.port)


if __name__ == "__main__":
    main()
