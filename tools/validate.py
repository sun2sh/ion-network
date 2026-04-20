#!/usr/bin/env python3
"""
ION spec validator — conformance checks for the spec repository.
Exits non-zero if any issue is found. Use this in CI.

Checks:
1.  YAML and JSON files parse cleanly
2.  x-ion-mandatory on every property (valid values: always, conditional, optional)
3.  No duplicate error codes across errors/*.yaml
4.  context.jsonld and vocab.jsonld non-empty for every schema pack
5.  All policy IRIs in offer schema resolve to existing policy documents
6.  No Beckn v1.x field paths in flow documents
    (message.order, snake_case context fields like bap_id/bpp_id)
7.  Empty files disallowed
"""

import sys
import json
import re
from pathlib import Path

# Friendly error if PyYAML not installed
try:
    import yaml
except ModuleNotFoundError:
    print("ERROR: PyYAML is not installed.")
    print("")
    print("Fix it in one line:")
    print("  pip install pyyaml")
    print("")
    print("Then re-run: python tools/validate.py")
    sys.exit(1)

ROOT = Path(__file__).parent.parent
ERRORS = []


def err(cat, msg):
    ERRORS.append((cat, msg))


def check_yaml_json_parse():
    for f in ROOT.rglob("*.yaml"):
        try:
            yaml.safe_load(f.read_text(encoding='utf-8'))
        except yaml.YAMLError as e:
            err("YAML_PARSE", f"{f.relative_to(ROOT)}: {str(e)[:100]}")
    for f in ROOT.rglob("*.json"):
        try:
            json.loads(f.read_text(encoding='utf-8'))
        except json.JSONDecodeError as e:
            err("JSON_PARSE", f"{f.relative_to(ROOT)}: {str(e)[:100]}")


def check_empty_files():
    for f in ROOT.rglob("*"):
        if f.is_file() and f.stat().st_size == 0:
            err("EMPTY_FILE", str(f.relative_to(ROOT)))


def check_mandatory_annotations():
    """Every property in every ION schema pack MUST declare x-ion-mandatory."""
    valid = {"always", "conditional", "optional"}
    for f in (ROOT / "schema" / "extensions").rglob("attributes.yaml"):
        try:
            data = yaml.safe_load(f.read_text(encoding='utf-8'))
        except Exception:
            continue
        schemas = data.get("components", {}).get("schemas", {})
        for schema_name, schema in schemas.items():
            if not isinstance(schema, dict):
                continue
            props = schema.get("properties", {})
            for prop_name, prop_def in props.items():
                if not isinstance(prop_def, dict):
                    continue
                if prop_def.get("deprecated") is True:
                    continue
                m = prop_def.get("x-ion-mandatory")
                if m is None:
                    err("MANDATORY_MISSING",
                        f"{f.relative_to(ROOT)} :: {schema_name}.{prop_name} — "
                        f"missing x-ion-mandatory")
                elif m not in valid:
                    err("MANDATORY_INVALID",
                        f"{f.relative_to(ROOT)} :: {schema_name}.{prop_name} — "
                        f"invalid value '{m}'")


def check_no_duplicate_error_codes():
    seen = {}
    for f in (ROOT / "errors").glob("*.yaml"):
        try:
            data = yaml.safe_load(f.read_text(encoding='utf-8'))
        except Exception:
            continue
        if not isinstance(data, list):
            continue
        for entry in data:
            if not isinstance(entry, dict):
                continue
            code = entry.get("code")
            if not code:
                continue
            if code in seen:
                err("DUPLICATE_ERROR_CODE",
                    f"{code} appears in {f.name} (first seen in {seen[code]})")
            else:
                seen[code] = f.name


def check_jsonld_populated():
    for ctx in (ROOT / "schema" / "extensions").rglob("context.jsonld"):
        try:
            data = json.loads(ctx.read_text(encoding='utf-8'))
            context = data.get("@context", {})
            if not context or len(context) < 3:
                err("JSONLD_EMPTY",
                    f"{ctx.relative_to(ROOT)} — context too small ({len(context)} terms)")
        except Exception as e:
            err("JSONLD_PARSE", f"{ctx.relative_to(ROOT)}: {e}")
    for v in (ROOT / "schema" / "extensions").rglob("vocab.jsonld"):
        try:
            data = json.loads(v.read_text(encoding='utf-8'))
            graph = data.get("@graph", [])
            if not graph:
                err("VOCAB_EMPTY", f"{v.relative_to(ROOT)} — empty @graph")
        except Exception as e:
            err("VOCAB_PARSE", f"{v.relative_to(ROOT)}: {e}")


def check_no_beckn_v1_paths():
    """Flag Beckn v1.x field paths and snake_case context in flows."""
    bad_patterns = [
        (r"\bmessage\.order\b", "Use message.contract (Beckn v2.0)"),
        (r'"\s*bap_id\s*"', "Use bapId (camelCase, Beckn v2.0)"),
        (r'"\s*bpp_id\s*"', "Use bppId"),
        (r'"\s*transaction_id\s*"', "Use transactionId"),
        (r'"\s*message_id\s*"', "Use messageId"),
        (r'"\s*bap_uri\s*"', "Use bapUri"),
        (r'"\s*bpp_uri\s*"', "Use bppUri"),
        (r"\bcontext\.bap_id\b", "Use context.bapId"),
        (r"\bcontext\.bpp_id\b", "Use context.bppId"),
        (r"\bcontext\.transaction_id\b", "Use context.transactionId"),
        (r"\bcontext\.message_id\b", "Use context.messageId"),
    ]
    for f in (ROOT / "flows").rglob("*"):
        if not f.is_file() or f.suffix not in (".yaml", ".json", ".md"):
            continue
        text = f.read_text(encoding='utf-8')
        for pat, hint in bad_patterns:
            if re.search(pat, text):
                err("BECKN_V1_PATH",
                    f"{f.relative_to(ROOT)} — matches {pat!r} — {hint}")


def check_composed_spec():
    """ion-with-beckn.yaml must exist and parse."""
    composed = ROOT / "schema" / "core" / "v2" / "api" / "v2.0.0" / "ion-with-beckn.yaml"
    if not composed.exists():
        err("COMPOSED_MISSING", "schema/core/v2/api/v2.0.0/ion-with-beckn.yaml not found — run tools/generate_composed.py")
        return
    try:
        import yaml as _yaml
        data = _yaml.safe_load(composed.read_text(encoding='utf-8'))
        schemas = data.get("components", {}).get("schemas", {})
        ion_schemas = [k for k in schemas if k.startswith("ION_")]
        if len(ion_schemas) < 10:
            err("COMPOSED_INCOMPLETE", f"ion-with-beckn.yaml has only {len(ion_schemas)} ION_ schemas — regenerate")
    except Exception as e:
        err("COMPOSED_INVALID", f"ion-with-beckn.yaml: {e}")


def check_policy_iris_resolve():
    """Every ion://policy/... IRI referenced in offer schema must have a policy doc."""
    offer = ROOT / "schema" / "extensions" / "trade" / "offer" / "v1" / "attributes.yaml"
    if not offer.exists():
        return
    text = offer.read_text(encoding='utf-8')
    iris = re.findall(r"ion://policy/[a-zA-Z0-9._\-]+", text)
    policies_dir = ROOT / "policies"
    if not policies_dir.exists():
        return
    existing = set()
    for p in policies_dir.rglob("*.yaml"):
        try:
            d = yaml.safe_load(p.read_text(encoding='utf-8'))
            if isinstance(d, dict) and "iri" in d:
                existing.add(d["iri"])
        except Exception:
            continue
    for iri in sorted(set(iris)):
        if iri not in existing:
            err("POLICY_MISSING",
                f"IRI {iri} referenced in offer schema but no policy document exists")


def main():
    check_yaml_json_parse()
    check_empty_files()
    check_mandatory_annotations()
    check_no_duplicate_error_codes()
    check_jsonld_populated()
    check_no_beckn_v1_paths()
    check_policy_iris_resolve()
    check_composed_spec()

    if not ERRORS:
        print("ALL VALIDATION CHECKS PASSED")
        return 0

    print(f"VALIDATION FAILED — {len(ERRORS)} issue(s)\n")
    by_cat = {}
    for cat, msg in ERRORS:
        by_cat.setdefault(cat, []).append(msg)
    for cat in sorted(by_cat):
        msgs = by_cat[cat]
        print(f"  [{cat}] {len(msgs)} issue(s)")
        for m in msgs[:10]:
            print(f"    - {m}")
        if len(msgs) > 10:
            print(f"    ... and {len(msgs) - 10} more")
        print()
    return 1


if __name__ == "__main__":
    sys.exit(main())
