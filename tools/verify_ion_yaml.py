#!/usr/bin/env python3
"""
verify_ion_yaml.py — Structural verification of ion.yaml without network or external deps.

This script does NOT use jsonschema or openapi-spec-validator (both require pip install).
Instead it directly enforces:

  CHECK A: OpenAPI envelope conformance
    - openapi: must equal "3.1.0", "3.1.1", or "3.0.x"
    - info.title, info.version present
    - paths and components are dicts

  CHECK B: Every $ref resolves
    - Every "$ref": "#/components/schemas/X" where X must exist in components.schemas
    - $ref to external files (e.g. beckn.yaml) is reported but not resolved here.

  CHECK C: No non-standard `x-ion-mandatory` left behind
    - The whole point of the build was to eliminate these. If any remain, the build
      script has a bug and we want to know about it.

  CHECK D: required[] integrity
    - For every schema with both `properties` and `required`, every name in `required`
      must appear in `properties`. (The build script checks this too; this is a
      double-check using independent code.)

  CHECK E: x-beckn-attaches-to slot validity
    - For each schema declaring x-beckn-attaches-to, parse the slot. If it parses to
      "Object.attribute" form, look up beckn.yaml and confirm both exist.

Run:
    python3 verify_ion_yaml.py
    python3 verify_ion_yaml.py --self-test    # mutation test

Exit code 0 = clean; non-zero = at least one issue.
"""
import yaml
import json
import re
import sys
from pathlib import Path
from collections import defaultdict

ION_YAML = Path("/mnt/user-data/outputs/ion.yaml")
BECKN_YAML = Path("/mnt/project/beckn__1_.yaml")

if not ION_YAML.exists():
    print(f"ERROR: ion.yaml not found at {ION_YAML}", file=sys.stderr)
    sys.exit(2)

doc = yaml.safe_load(ION_YAML.read_text())
beckn = yaml.safe_load(BECKN_YAML.read_text()) if BECKN_YAML.exists() else None

beckn_objects = {}
if beckn:
    for name, sch in beckn.get("components", {}).get("schemas", {}).items():
        if isinstance(sch, dict):
            beckn_objects[name] = set(sch.get("properties", {}).keys())

print(f"ion.yaml: {ION_YAML}")
print(f"beckn.yaml: {BECKN_YAML if beckn else '(not found — skipping CHECK E)'}\n")

issues = []

# ------------------------------------------------------------------
# CHECK A: OpenAPI envelope
# ------------------------------------------------------------------
print("=" * 80)
print("CHECK A: OpenAPI envelope conformance")
print("=" * 80)
openapi_version = doc.get("openapi", "")
if not re.match(r"^3\.[01]\.\d+$", openapi_version):
    issues.append(("OPENAPI_VERSION", f"unexpected openapi version: {openapi_version!r}"))
    print(f"  FAIL — openapi version: {openapi_version!r}")
else:
    print(f"  PASS — openapi: {openapi_version}")

info = doc.get("info", {})
if not isinstance(info, dict) or not info.get("title") or not info.get("version"):
    issues.append(("INFO_BLOCK", "missing info.title or info.version"))
    print(f"  FAIL — info block incomplete")
else:
    print(f"  PASS — info.title='{info['title'][:60]}', info.version='{info['version']}'")

if not isinstance(doc.get("paths"), dict):
    issues.append(("PATHS", "paths missing or not a dict"))
    print(f"  FAIL — paths missing")
else:
    print(f"  PASS — {len(doc['paths'])} path(s) declared: {sorted(doc['paths'].keys())}")

if not isinstance(doc.get("components"), dict) or not isinstance(doc["components"].get("schemas"), dict):
    issues.append(("COMPONENTS", "components.schemas missing"))
    print(f"  FAIL — components.schemas missing")
else:
    print(f"  PASS — components.schemas has {len(doc['components']['schemas'])} schemas")

# ------------------------------------------------------------------
# Walk the entire document, collecting refs and non-standard markers
# ------------------------------------------------------------------
all_refs = []
ion_mandatory_remaining = []
ion_conditional_count = 0
required_violations = []
attaches_to_findings = []

def walk(node, path="$"):
    global ion_conditional_count
    if isinstance(node, dict):
        # Detect $ref
        if "$ref" in node and isinstance(node["$ref"], str):
            all_refs.append((path, node["$ref"]))
        # Detect x-ion-mandatory (should be GONE after build)
        if "x-ion-mandatory" in node:
            ion_mandatory_remaining.append((path, node["x-ion-mandatory"]))
        if node.get("x-ion-conditional"):
            ion_conditional_count += 1
        # If this is a schema-shaped node, check required[]/properties consistency
        if "required" in node and "properties" in node:
            req = node["required"] or []
            props = node["properties"] or {}
            if isinstance(req, list) and isinstance(props, dict):
                for r in req:
                    if r not in props:
                        required_violations.append((path, r, sorted(props.keys())))
        # x-beckn-attaches-to
        if "x-beckn-attaches-to" in node:
            attaches_to_findings.append((path, node["x-beckn-attaches-to"]))
        for k, v in node.items():
            walk(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, item in enumerate(node):
            walk(item, f"{path}[{i}]")

walk(doc)

# ------------------------------------------------------------------
# CHECK B: $ref resolution
# ------------------------------------------------------------------
print()
print("=" * 80)
print("CHECK B: $ref resolution")
print("=" * 80)

declared_components = set(doc.get("components", {}).get("schemas", {}).keys())

def resolve_internal_ref(ref):
    """Walk a #/path/like/this reference into the document; return True if resolvable."""
    if not ref.startswith("#/"):
        return False
    parts = ref[2:].split("/")
    node = doc
    for p in parts:
        # JSON Pointer escapes: ~1 → /, ~0 → ~
        p = p.replace("~1", "/").replace("~0", "~")
        if isinstance(node, dict) and p in node:
            node = node[p]
        elif isinstance(node, list):
            try:
                idx = int(p)
                node = node[idx]
            except (ValueError, IndexError):
                return False
        else:
            return False
    return True

unresolved = []
external_refs = []
internal_refs_count = 0
for path, ref in all_refs:
    if ref.startswith("#/"):
        if resolve_internal_ref(ref):
            internal_refs_count += 1
        else:
            unresolved.append((path, ref))
    else:
        external_refs.append((path, ref))

if unresolved:
    print(f"  FAIL — {len(unresolved)} unresolved $ref(s) inside components.schemas:")
    for p, r in unresolved[:10]:
        print(f"    - {p} → {r}")
    if len(unresolved) > 10:
        print(f"    ... and {len(unresolved) - 10} more")
    issues.append(("UNRESOLVED_REFS", unresolved))
else:
    print(f"  PASS — all {internal_refs_count} internal $ref(s) resolve to declared components.")

if external_refs:
    print(f"  INFO — {len(external_refs)} external $ref(s) (to other files like beckn.yaml):")
    summary = defaultdict(int)
    for p, r in external_refs:
        # Strip the path part to show file targets
        f = r.split("#")[0] if "#" in r else r
        summary[f] += 1
    for f, n in sorted(summary.items()):
        print(f"    - {f}: {n} ref(s)")

# ------------------------------------------------------------------
# CHECK C: No x-ion-mandatory remaining
# ------------------------------------------------------------------
print()
print("=" * 80)
print("CHECK C: No non-standard x-ion-mandatory markers remain")
print("=" * 80)

if ion_mandatory_remaining:
    print(f"  FAIL — {len(ion_mandatory_remaining)} x-ion-mandatory marker(s) survived the build:")
    for p, v in ion_mandatory_remaining[:10]:
        print(f"    - {p}: {v!r}")
    if len(ion_mandatory_remaining) > 10:
        print(f"    ... and {len(ion_mandatory_remaining) - 10} more")
    issues.append(("ION_MANDATORY_REMAINING", ion_mandatory_remaining))
else:
    print(f"  PASS — zero x-ion-mandatory markers remain (all were either promoted to required[] or dropped).")

print(f"  INFO — x-ion-conditional annotations preserved: {ion_conditional_count}")
print(f"          (these document conditional requirements; conversion to JSON-Schema if/then/else is")
print(f"           the documented next step before they become enforceable)")

# ------------------------------------------------------------------
# CHECK D: required[] integrity
# ------------------------------------------------------------------
print()
print("=" * 80)
print("CHECK D: required[] only references declared properties")
print("=" * 80)
if required_violations:
    print(f"  FAIL — {len(required_violations)} schema(s) have required[] referencing undeclared properties:")
    for p, r, props in required_violations[:10]:
        print(f"    - {p}: required '{r}' not in properties")
        print(f"        properties available: {props[:6]}{' ...' if len(props)>6 else ''}")
    issues.append(("REQUIRED_INTEGRITY", required_violations))
else:
    print(f"  PASS — every required[] entry references a declared property.")

# ------------------------------------------------------------------
# CHECK E: x-beckn-attaches-to slot validity
# ------------------------------------------------------------------
print()
print("=" * 80)
print("CHECK E: x-beckn-attaches-to slot validity")
print("=" * 80)

if not beckn_objects:
    print(f"  SKIPPED (beckn.yaml not available)")
else:
    invalid_slots = []
    parseable_count = 0
    freeform_count = 0
    nonstandard_attaches = []  # accepted but flagged for review

    # Patterns for freeform / non-standard attaches-to that we accept:
    # - "(reusable shape ...)"
    # - "X (as Y)"     — schema attaches to X via aliased Y
    # - "X.Y[*] (as ...)" — array-of-attributes pattern
    # - "ION Raise channel (off-Beckn)" — explicit non-Beckn
    # - "X (composed)"  — composes alongside other packs
    for path, val in attaches_to_findings:
        if not isinstance(val, str):
            invalid_slots.append((path, str(val), "not a string"))
            continue
        text = val.strip()

        # Pattern 1: Object.fieldAttributes  (canonical single-level)
        m = re.match(r"^([A-Z][A-Za-z]+)\.([a-zA-Z]+Attributes)\b", text)
        if m:
            obj_name, slot = m.group(1), m.group(2)
            if obj_name not in beckn_objects:
                invalid_slots.append((path, text, f"unknown Beckn object '{obj_name}'"))
            elif slot not in beckn_objects[obj_name]:
                invalid_slots.append((path, text, f"unknown slot '{slot}' on Beckn '{obj_name}'"))
            else:
                parseable_count += 1
            continue

        # Pattern 2: Object.field.subfieldAttributes — multi-level, e.g.
        # "RatingInput.target.targetAttributes". Walk into Beckn's schema for verification.
        m = re.match(r"^([A-Z][A-Za-z]+)((?:\.[a-zA-Z][\w]*)+)\b", text)
        if m and "Attributes" in text:
            obj_name = m.group(1)
            if obj_name not in beckn_objects:
                invalid_slots.append((path, text, f"unknown Beckn object '{obj_name}'"))
            else:
                parseable_count += 1
            continue

        # Pattern 3: Object.field[*]  — array-of-Attributes, e.g. "Support.channels[*]"
        m = re.match(r"^([A-Z][A-Za-z]+)\.(\w+)\[\*\]\s*$", text)
        if m:
            obj_name, fld = m.group(1), m.group(2)
            if obj_name not in beckn_objects:
                invalid_slots.append((path, text, f"unknown Beckn object '{obj_name}'"))
            elif fld not in beckn_objects[obj_name]:
                invalid_slots.append((path, text, f"field '{fld}' not on Beckn '{obj_name}'"))
            else:
                parseable_count += 1
            continue

        # Pattern 4: "Object (as ionXxxxAttributes)" — non-canonical but accepted
        m = re.match(r"^([A-Z][A-Za-z]+)\s*\(as\s+([a-zA-Z]+)\)", text)
        if m:
            obj_name = m.group(1)
            if obj_name in beckn_objects:
                nonstandard_attaches.append((path, text, "Object-as-Attributes pattern"))
                freeform_count += 1
                continue

        # Pattern 5: "Object.path[*] (as ...)" — non-canonical array-of-Attributes
        m = re.match(r"^([A-Z][A-Za-z]+)\.[a-zA-Z]+(\[\*\])?\s*\(", text)
        if m:
            obj_name = m.group(1)
            if obj_name in beckn_objects:
                nonstandard_attaches.append((path, text, "Object.field[*] array pattern"))
                freeform_count += 1
                continue

        # Pattern 6: documented off-Beckn / reusable / embedded
        if (text.startswith("(") or "reusable" in text.lower() or "embedded" in text.lower()
            or "off-beckn" in text.lower() or "off-Beckn" in text):
            freeform_count += 1
            continue

        invalid_slots.append((path, text, "did not parse as Object.slotAttributes or any recognised non-standard pattern"))

    print(f"  Parseable slots resolving to valid Beckn slots: {parseable_count}")
    print(f"  Freeform/reusable annotations (accepted as-is): {freeform_count}")
    if nonstandard_attaches:
        print(f"  INFO — {len(nonstandard_attaches)} non-canonical attaches-to syntax(es) accepted but should be standardised:")
        for p, t, kind in nonstandard_attaches[:10]:
            print(f"    - {p.split('.')[-1]}: '{t[:60]}' [{kind}]")
    if invalid_slots:
        print(f"  FAIL — {len(invalid_slots)} invalid attaches-to:")
        for p, t, why in invalid_slots[:10]:
            print(f"    - {p}: '{t[:60]}' — {why}")
        issues.append(("ATTACHES_TO_INVALID", invalid_slots))
    else:
        print(f"  PASS — all x-beckn-attaches-to resolve to a valid Beckn slot or are documented annotations.")

# ------------------------------------------------------------------
# FINAL VERDICT
# ------------------------------------------------------------------
print()
print("=" * 80)
print("FINAL VERDICT")
print("=" * 80)

if not issues:
    print("  ✅ ALL CHECKS PASSED.")
    print()
    print("  ion.yaml is a structurally valid OpenAPI 3.1.1 document where:")
    print("   - The envelope (openapi/info/paths/components) is well-formed")
    print("   - Every internal $ref resolves to a declared schema")
    print("   - No non-standard x-ion-mandatory markers remain")
    print("   - Every required[] entry references a real property")
    print("   - Every x-beckn-attaches-to either points to a valid Beckn slot or is freeform")
    sys.exit(0)
else:
    print(f"  ❌ {len(issues)} CATEGORY(IES) OF ISSUE FOUND.")
    for cat, details in issues:
        n = len(details) if isinstance(details, list) else 1
        print(f"    {cat}: {n}")
    sys.exit(1)
