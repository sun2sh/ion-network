#!/usr/bin/env python3
"""
build_conditional_worksheet.py — Produce a CSV listing every unparseable
conditional field in ion.yaml so ION authors can review them in parallel.

Output columns:
  pack            — which extension pack the schema lives in
  schema          — the schema name
  field           — the conditional field name
  current_text    — current x-ion-condition text (may be empty)
  proposed_rule   — BLANK column for reviewer to fill in
                    (format: "FIELD=VALUE" for in-schema, or
                             "OTHER_SCHEMA.FIELD=VALUE" for cross-schema, or
                             "ALWAYS" or "NEVER" if the rule should be
                             unconditional)
  notes           — BLANK column for reviewer notes

After review, re-run tools/fix_residuals.py and the rules will auto-convert
into JSON Schema if/then/else (in-schema) or rules-file entries (cross-schema).
"""
import yaml, csv
from pathlib import Path
from collections import defaultdict

ION_YAML = Path("/home/claude/ion-network-main-updated/schema/core/v2/api/v2.0.0/ion.yaml")
EXT_ROOT = Path("/home/claude/ion-network-main-updated/schema/extensions")
OUT = Path("/mnt/user-data/outputs")

doc = yaml.safe_load(ION_YAML.read_text())

# Build a map: schema_name -> pack_id (using per-pack files)
schema_to_pack = {}
for sector_dir in sorted(EXT_ROOT.iterdir()):
    if not sector_dir.is_dir(): continue
    for pack_dir in sorted(sector_dir.iterdir()):
        if not pack_dir.is_dir(): continue
        for v in pack_dir.iterdir():
            if not v.is_dir(): continue
            attrs = v / "attributes.yaml"
            if not attrs.exists(): continue
            try:
                pdoc = yaml.safe_load(attrs.read_text())
            except Exception:
                continue
            for tname in pdoc.get("components",{}).get("schemas",{}).keys():
                schema_to_pack[tname] = f"{sector_dir.name}/{pack_dir.name}"

rows = []
def walk(node, schema_name, pack_id, path=""):
    if isinstance(node, dict):
        if node.get("x-ion-conditional") or node.get("x-ion-conditional-cross-schema"):
            text = node.get("x-ion-condition", "")
            field = path.split(".")[-1] if path else "(unnamed)"
            kind = "cross-schema" if node.get("x-ion-conditional-cross-schema") else "unparseable"
            rows.append({
                "pack": pack_id,
                "schema": schema_name,
                "path_in_schema": path,
                "field": field,
                "current_kind": kind,
                "current_text": text,
                "proposed_rule": "",
                "proposed_target_schema": "",
                "notes": "",
            })
        for k, v in node.items():
            walk(v, schema_name, pack_id, f"{path}.{k}" if path else k)
    elif isinstance(node, list):
        for i, it in enumerate(node):
            walk(it, schema_name, pack_id, f"{path}[{i}]")

for sname, sdef in doc["components"]["schemas"].items():
    pack_id = schema_to_pack.get(sname, "(unknown)")
    walk(sdef, sname, pack_id)

# Sort: by pack, then schema, then field
rows.sort(key=lambda r: (r["pack"], r["schema"], r["field"]))

csv_path = OUT / "conditional_review_worksheet.csv"
with open(csv_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=[
        "pack", "schema", "path_in_schema", "field", "current_kind",
        "current_text", "proposed_rule", "proposed_target_schema", "notes"
    ])
    w.writeheader()
    for r in rows:
        w.writerow(r)

# Also a compact markdown view grouped by pack
md_path = OUT / "conditional_review_worksheet.md"
with open(md_path, "w") as f:
    f.write("# Conditional review worksheet\n\n")
    f.write(f"**Total: {len(rows)} fields awaiting review.**\n\n")
    f.write("Instructions for reviewers:\n\n")
    f.write("- For each field, decide whether the rule is `IN-SCHEMA` (trigger field is on the same schema) or `CROSS-SCHEMA` (trigger lives elsewhere).\n")
    f.write("- Write the rule as `field_name=VALUE` (e.g. `businessType=PERORANGAN`).\n")
    f.write("- For cross-schema, also fill in `proposed_target_schema` (the schema that owns the trigger field).\n")
    f.write("- If the field should actually be unconditionally required, write `ALWAYS`.\n")
    f.write("- If the field is fully optional and the marker should be removed, write `NEVER`.\n")
    f.write("- Edit the CSV (`conditional_review_worksheet.csv`); after edits, re-run `tools/fix_residuals.py` and the script will convert IN-SCHEMA rules to standard `if/then/else` automatically.\n\n")
    by_pack = defaultdict(list)
    for r in rows: by_pack[r["pack"]].append(r)
    for pack, prows in sorted(by_pack.items()):
        f.write(f"\n## `{pack}` — {len(prows)} field(s)\n\n")
        f.write("| Schema | Field | Current text |\n|---|---|---|\n")
        for r in prows:
            text = (r["current_text"] or "").replace("|","\\|").replace("\n"," ").strip()
            if not text: text = "*(empty — TODO)*"
            if len(text) > 80: text = text[:77] + "..."
            f.write(f"| `{r['schema']}` | `{r['field']}` | {text} |\n")

print(f"Wrote {csv_path}")
print(f"Wrote {md_path}")
print(f"Total rows: {len(rows)}")
print()

# Stats
empty = sum(1 for r in rows if not r["current_text"].strip())
narrative = len(rows) - empty
print(f"  Empty condition text (TODO markers): {empty}")
print(f"  Narrative/freeform condition text:   {narrative}")
print(f"  Cross-schema (already classified):   {sum(1 for r in rows if r['current_kind']=='cross-schema')}")
print()
# Top packs
top = defaultdict(int)
for r in rows: top[r["pack"]] += 1
print("Top 5 packs by review-needed count:")
for p, n in sorted(top.items(), key=lambda x:-x[1])[:5]:
    print(f"  {n:3d}  {p}")
