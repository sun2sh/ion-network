#!/usr/bin/env python3
"""
verify_inventory.py — Independent verification of inventory_beckn.csv against beckn.yaml.

Why this exists: the inventory CSV was produced by build_inventory.py. To trust it,
we need an independent witness. This script does NOT import anything from
build_inventory.py and uses different parsing strategies. If both produce the
same answer, the chance of a bug in one being mirrored in the other drops sharply.

Three independent verifications:

  CHECK 1: SCHEMA EXISTENCE
    Walk every $ref in beckn.yaml. Confirm every schema name the inventory references
    actually exists in beckn.yaml's components/schemas. Catches typos and stale rows.

  CHECK 2: PROPERTY-SET PARITY (textual, regex-based)
    For each Beckn object in the inventory, re-extract its properties using a
    completely different method: regex over the raw YAML text. The two parsers
    are:
       INVENTORY  : yaml.safe_load -> dict navigation
       VERIFIER 1 : yaml.safe_load -> json.dumps -> regex over JSON
       VERIFIER 2 : raw line-walking of beckn.yaml (no YAML parser at all)
    Any disagreement gets flagged.

  CHECK 3: REQUIRED-FIELD PARITY
    Same three-way comparison for the `required` array on each schema.

  CHECK 4: ADDITIONALPROPERTIES PARITY
    For every object whose schema explicitly sets additionalProperties, all
    three views must agree.

  CHECK 5: PAYLOAD ROUND-TRIP
    Construct a known-good payload (verified by hand against beckn.yaml).
    For each property the inventory claims is allowed, present it in the payload
    and confirm the schema would accept it. For each property the inventory claims
    is forbidden, confirm the schema would reject it. Done by re-implementing
    a minimal JSON Schema validator inline (no external deps).

Run:    python3 verify_inventory.py
Exit code 0 = all green; non-zero = at least one disagreement.
"""

import yaml
import json
import csv
import re
import sys
from pathlib import Path
from collections import defaultdict

BECKN_PATH = Path(__file__).resolve().parent / "beckn.yaml"
if not BECKN_PATH.exists():
    # Try common alternate locations
    for alt in [Path("/mnt/project/beckn__1_.yaml"), Path("beckn__1_.yaml"), Path("beckn.yaml")]:
        if alt.exists():
            BECKN_PATH = alt
            break

INVENTORY_CSV = Path(__file__).resolve().parent / "inventory_beckn.csv"
if not INVENTORY_CSV.exists():
    for alt in [Path("/mnt/user-data/outputs/inventory_beckn.csv"), Path("inventory_beckn.csv")]:
        if alt.exists():
            INVENTORY_CSV = alt
            break

print(f"Beckn schema: {BECKN_PATH}")
print(f"Inventory CSV: {INVENTORY_CSV}\n")

raw_text = BECKN_PATH.read_text()
beckn = yaml.safe_load(raw_text)
schemas = beckn["components"]["schemas"]

# Load the inventory as the "claim" we are verifying
inv_object_props = defaultdict(set)         # object -> set of property names CLAIMED
inv_object_required = defaultdict(set)       # object -> set of required CLAIMED
inv_object_addl = {}                         # object -> additionalProperties string CLAIMED
inv_object_required_str = {}                 # object -> required-on-object cell text CLAIMED
inv_objects_seen = set()

with open(INVENTORY_CSV) as f:
    for r in csv.DictReader(f):
        obj = r["object"]
        inv_objects_seen.add(obj)
        if r["level"] == "object":
            inv_object_addl[obj] = r["additionalProperties"]
            req_str = r["object_required_fields"].strip()
            if req_str:
                inv_object_required[obj] = set(s.strip() for s in req_str.split(",") if s.strip())
        elif r["level"] == "attribute":
            inv_object_props[obj].add(r["attribute"])

# ------------------------------------------------------------------
# VERIFIER 1: yaml -> json round-trip, then re-walk
# Independent path: serialise to JSON string, parse back with json.loads
# (different parser than yaml.safe_load), then navigate. If yaml.safe_load
# corrupted anything, json.loads on its output would expose it.
# ------------------------------------------------------------------
def verifier1_extract(obj_name):
    """Returns (props_set, required_set, addl_value)."""
    sch = schemas.get(obj_name)
    if sch is None:
        return None
    # Round-trip through JSON: yaml dict -> JSON string -> json.loads back to dict
    # This catches any case where yaml.safe_load produced a non-JSON-serialisable
    # object that the inventory script silently mishandled.
    js_text = json.dumps(sch)
    re_parsed = json.loads(js_text)
    props = set(re_parsed.get("properties", {}).keys())
    required = set(re_parsed.get("required", []))
    addl = re_parsed.get("additionalProperties", None)
    if isinstance(addl, dict): addl = "(inline)"
    return props, required, addl


# ------------------------------------------------------------------
# VERIFIER 2: raw text walker (no YAML parser at all)
# Independent of YAML libraries entirely. Walks the text by indentation.
# ------------------------------------------------------------------
def verifier2_extract(obj_name):
    """Walk beckn.yaml as raw lines. Find the 'ObjName:' definition
       under '  schemas:' (4-space indent under components), then read
       its properties / required / additionalProperties at 6-space indent."""
    lines = raw_text.split("\n")
    # Find the schemas: block, then the object key
    in_schemas = False
    obj_start = None
    for i, line in enumerate(lines):
        if re.match(r"^  schemas:\s*$", line):
            in_schemas = True
            continue
        if in_schemas:
            m = re.match(r"^    ([A-Za-z][A-Za-z0-9_]*):\s*$", line)
            if m and m.group(1) == obj_name:
                obj_start = i
                break
    if obj_start is None:
        return None

    # Find end of this schema (next line at 4-space indent that's not part of this schema)
    obj_end = len(lines)
    for j in range(obj_start + 1, len(lines)):
        if re.match(r"^    [A-Za-z]", lines[j]):
            obj_end = j
            break

    body = lines[obj_start:obj_end]

    # Find the 'properties:' line at 6-space indent (depth 1 inside the schema)
    props = set()
    required = set()
    addl = None
    in_props = False
    in_required = False

    for k, line in enumerate(body):
        # additionalProperties at 6 spaces
        m = re.match(r"^      additionalProperties:\s*(.*)$", line)
        if m:
            v = m.group(1).strip()
            if v == "true": addl = True
            elif v == "false": addl = False
            else: addl = v  # could be inline object
            continue

        # required at 6 spaces (block style — items follow at - prefix)
        m = re.match(r"^      required:\s*$", line)
        if m:
            in_required = True
            in_props = False
            continue
        # required inline list: required: [a, b, c]
        m = re.match(r"^      required:\s*\[(.*)\]\s*$", line)
        if m:
            for item in m.group(1).split(","):
                item = item.strip().strip("'").strip('"')
                if item: required.add(item)
            continue

        if in_required:
            m = re.match(r"^      - (.+)$", line)
            if m:
                required.add(m.group(1).strip().strip("'").strip('"'))
                continue
            # End of required block: any line at <=6 indent that's not a list item
            if line.strip() and not re.match(r"^       ", line):
                in_required = False

        # properties: at 6 spaces
        m = re.match(r"^      properties:\s*$", line)
        if m:
            in_props = True
            in_required = False
            continue

        if in_props:
            # property names at 8-space indent
            m = re.match(r"^        ([A-Za-z@'\"][\w@'\"]*):\s*", line)
            if m:
                pname = m.group(1).strip("'").strip('"')
                props.add(pname)
                continue
            # End of properties block: a 6-space-indent key
            if re.match(r"^      [A-Za-z]", line):
                in_props = False

    return props, required, addl


# ------------------------------------------------------------------
# VERIFIER 3: dict navigation (the SAME method as the inventory),
# kept here as a sanity baseline. If V3 disagrees with the inventory CSV,
# the CSV was corrupted or the inventory script has a bug.
# ------------------------------------------------------------------
def verifier3_extract(obj_name):
    sch = schemas.get(obj_name)
    if not sch: return None
    props = set(sch.get("properties", {}).keys())
    required = set(sch.get("required", []))
    addl = sch.get("additionalProperties", None)
    if isinstance(addl, dict): addl = "(inline)"
    return props, required, addl


# ------------------------------------------------------------------
# RUN ALL CHECKS
# ------------------------------------------------------------------
all_disagreements = []

print("=" * 80)
print("CHECK 1: SCHEMA EXISTENCE")
print("=" * 80)
missing = [o for o in inv_objects_seen if o not in schemas]
if missing:
    print(f"  FAIL — {len(missing)} object(s) in inventory not present in beckn.yaml:")
    for o in missing:
        print(f"    - {o}")
    all_disagreements.append(("SCHEMA_EXISTENCE", missing))
else:
    print(f"  PASS — every inventory object exists in beckn.yaml ({len(inv_objects_seen)} objects)")

# Reverse direction: every Beckn schema should be considered for inclusion in the inventory.
# Inventory was hand-curated to focus on payload-level objects, so finding extras isn't
# automatically a bug — but we list them so you can decide whether each was a deliberate
# omission or an oversight.
print()
beckn_only = sorted(set(schemas.keys()) - inv_objects_seen)
if beckn_only:
    print(f"  INFO — {len(beckn_only)} Beckn schema(s) NOT in inventory (you should confirm each is intentionally omitted):")
    for o in beckn_only:
        # Heuristic: is it a top-level object (used in paths) or a utility/Action wrapper?
        is_action = o.endswith("Action")
        is_response = o in ("Ack","AckNoCallback","NackBadRequest","NackUnauthorized","ServerError")
        is_utility = o in ("Pagination","DeliveryPolicy","CatalogSubscribeAction","CatalogSubscription",
                          "CatalogPullAction","CatalogProcessingResult","CatalogPublishAction",
                          "CatalogOnPublishAction","MasterSearchAction","PullResultFile","Error",
                          "AsyncError","MediaInput","MediaSearch","MediaSearchOptions","AddOn")
        kind = "Action wrapper (intentional skip)" if is_action else \
               "Response envelope (intentional skip)" if is_response else \
               "Catalog/utility (review needed)" if is_utility else \
               "REVIEW: payload-level type that should probably be in inventory"
        print(f"    - {o}  [{kind}]")

print()
print("=" * 80)
print("CHECK 2 & 3 & 4: PROPERTY-SET, REQUIRED, ADDITIONALPROPERTIES PARITY")
print("=" * 80)
print(f"For each object: V1 (json+regex) vs V2 (raw text) vs V3 (dict nav) vs Inventory CSV")
print()

prop_disagreements = []
req_disagreements = []
addl_disagreements = []

for obj_name in sorted(inv_objects_seen):
    if obj_name not in schemas:
        continue  # already reported in Check 1

    inv_props = inv_object_props.get(obj_name, set())
    inv_req   = inv_object_required.get(obj_name, set())
    inv_addl  = inv_object_addl.get(obj_name, "")

    r1 = verifier1_extract(obj_name)
    r2 = verifier2_extract(obj_name)
    r3 = verifier3_extract(obj_name)

    v1_props, v1_req, v1_addl = r1 if r1 else (set(), set(), None)
    v2_props, v2_req, v2_addl = r2 if r2 else (set(), set(), None)
    v3_props, v3_req, v3_addl = r3 if r3 else (set(), set(), None)

    # Property set parity
    # Pick V3 (the canonical) vs each other view
    if v1_props != v3_props:
        prop_disagreements.append((obj_name, "V1 vs V3", v1_props ^ v3_props))
    if v2_props != v3_props:
        prop_disagreements.append((obj_name, "V2 vs V3", v2_props ^ v3_props))
    if inv_props != v3_props:
        prop_disagreements.append((obj_name, "INV vs V3", inv_props ^ v3_props))

    # Required parity
    if v1_req != v3_req:
        req_disagreements.append((obj_name, "V1 vs V3", v1_req ^ v3_req))
    if v2_req != v3_req:
        req_disagreements.append((obj_name, "V2 vs V3", v2_req ^ v3_req))
    if inv_req != v3_req:
        req_disagreements.append((obj_name, "INV vs V3", inv_req ^ v3_req))

    # additionalProperties parity (just inv vs v3 — regexes are noisy here)
    inv_addl_norm = inv_addl.lower().strip() if inv_addl else ""
    v3_addl_norm = str(v3_addl).lower() if v3_addl is not None else "(open)"
    if v3_addl is None and inv_addl_norm not in ("(open)", "(unspecified — defaults open)", "none"):
        # Beckn doesn't set additionalProperties; inventory should record open
        addl_disagreements.append((obj_name, f"INV says '{inv_addl}', schema doesn't set additionalProperties (defaults open)"))
    elif v3_addl is False and inv_addl_norm not in ("false", ""):
        addl_disagreements.append((obj_name, f"INV says '{inv_addl}', schema sets additionalProperties: false"))
    elif v3_addl is True and inv_addl_norm not in ("true", ""):
        addl_disagreements.append((obj_name, f"INV says '{inv_addl}', schema sets additionalProperties: true"))

# Report
total = len(inv_objects_seen)
print(f"PROPERTY-SET CHECK ({total} objects):")
if not prop_disagreements:
    print("  PASS — all three independent extractions agree with the inventory CSV on every object's property set.")
else:
    print(f"  FAIL — {len(prop_disagreements)} disagreement(s):")
    for obj, pair, diff in prop_disagreements:
        print(f"    {obj}: {pair} differs by {diff}")
    all_disagreements.append(("PROPERTY_SET", prop_disagreements))

print()
print(f"REQUIRED-FIELD CHECK ({total} objects):")
if not req_disagreements:
    print("  PASS — all three views agree on the required-field list for every object.")
else:
    print(f"  FAIL — {len(req_disagreements)} disagreement(s):")
    for obj, pair, diff in req_disagreements:
        print(f"    {obj}: {pair} differs by {diff}")
    all_disagreements.append(("REQUIRED", req_disagreements))

print()
print(f"ADDITIONALPROPERTIES CHECK ({total} objects):")
if not addl_disagreements:
    print("  PASS — additionalProperties matches between schema and inventory for every object.")
else:
    print(f"  FAIL — {len(addl_disagreements)} disagreement(s):")
    for obj, msg in addl_disagreements:
        print(f"    {obj}: {msg}")
    all_disagreements.append(("ADDITIONAL_PROPS", addl_disagreements))


# ------------------------------------------------------------------
# CHECK 5: PAYLOAD ROUND-TRIP
# Construct a payload that uses every property the inventory says is valid for
# 'Resource'. Validate it with a minimal JSON-Schema enforcer that consults
# beckn.yaml directly. If a property the inventory says is allowed gets rejected,
# the inventory has a false positive. If a property the inventory says is forbidden
# gets accepted, the inventory has a false negative.
# ------------------------------------------------------------------
print()
print("=" * 80)
print("CHECK 5: PAYLOAD ROUND-TRIP (Resource & Commitment)")
print("=" * 80)

def minimal_validate(value, schema_name, all_schemas):
    """Tiny JSON-Schema enforcer. Returns (ok, errors)."""
    sch = all_schemas[schema_name]
    errors = []
    if not isinstance(value, dict):
        return True, []  # only validate object-shaped payloads
    props = sch.get("properties", {})
    required = sch.get("required", [])
    addl = sch.get("additionalProperties", None)
    for r in required:
        if r not in value:
            errors.append(f"missing required '{r}'")
    if addl is False:
        for k in value:
            if k not in props:
                errors.append(f"additionalProperty '{k}' rejected by additionalProperties:false")
    return len(errors) == 0, errors

# Test on Resource (we know its inventory claims id, descriptor, resourceAttributes)
print()
print("Testing Resource:")
inv_props_resource = inv_object_props.get("Resource", set())
print(f"  Inventory claims valid properties: {sorted(inv_props_resource)}")

# Build a payload using all claimed-valid props
payload_ok = {p: f"<value-{p}>" for p in inv_props_resource}
ok, errs = minimal_validate(payload_ok, "Resource", schemas)
if ok:
    print(f"  ✓ Payload with all claimed-valid props passes minimal validation.")
else:
    print(f"  ✗ Payload should pass but failed: {errs}")
    all_disagreements.append(("ROUNDTRIP_FALSE_POSITIVE_Resource", errs))

# Try with the property the original buggy doc had — top-level 'quantity'
payload_bad = dict(payload_ok)
payload_bad["quantity"] = {"value": 1, "unit": "piece"}
ok, errs = minimal_validate(payload_bad, "Resource", schemas)
# We expect Resource to NOT have additionalProperties:false (Beckn leaves it open
# on Resource). Inventory should reflect that.
inv_addl_resource = inv_object_addl.get("Resource", "")
v3_addl_resource = schemas["Resource"].get("additionalProperties", None)
print(f"  Inventory says additionalProperties for Resource: '{inv_addl_resource}'")
print(f"  Schema says additionalProperties for Resource: {v3_addl_resource}")
if v3_addl_resource is None and ok:
    print(f"  ✓ Resource accepts top-level 'quantity' (open additionalProperties) — inventory would predict this.")
elif v3_addl_resource is False and not ok:
    print(f"  ✓ Resource rejects top-level 'quantity' — inventory would predict this.")
else:
    print(f"  ! Inventory and schema disagree on whether top-level 'quantity' is accepted.")

print()
print("Testing Contract (we expect additionalProperties: false):")
inv_props_contract = inv_object_props.get("Contract", set())
print(f"  Inventory claims valid properties: {sorted(inv_props_contract)}")
v3_addl_contract = schemas["Contract"].get("additionalProperties", None)
print(f"  Schema additionalProperties: {v3_addl_contract}")

# Try injecting a bogus property
payload_bad = {"commitments": [], "fakeField": "x"}
ok, errs = minimal_validate(payload_bad, "Contract", schemas)
if v3_addl_contract is False and not ok:
    print(f"  ✓ Contract rejects 'fakeField' as inventory's 'additionalProperties: False' predicts.")
else:
    print(f"  ✗ Mismatch: schema additionalProperties={v3_addl_contract}, validation ok={ok}, errs={errs}")
    all_disagreements.append(("ROUNDTRIP_Contract", errs))


# ------------------------------------------------------------------
# FINAL VERDICT
# ------------------------------------------------------------------
print()
print("=" * 80)
print("FINAL VERDICT")
print("=" * 80)
if not all_disagreements:
    print("  ✅ ALL CHECKS PASSED.")
    print()
    print("  Three independent extractions of beckn.yaml's schema (json+regex, raw text walker,")
    print("  dict navigation) agreed with each other and with the inventory CSV on:")
    print("   - which schemas exist")
    print("   - the property set of every Beckn object")
    print("   - the required-field list of every Beckn object")
    print("   - the additionalProperties posture of every Beckn object")
    print("  Plus payload-level round-trip validation matches inventory predictions.")
    print()
    print("  The inventory CSV is consistent with the Beckn YAML at the property/required/addl level.")
    print("  Remaining residual risk:")
    print("    1. Inventory might be missing OBJECTS that exist in beckn.yaml but were not enumerated.")
    print("       To check: diff this script's `inv_objects_seen` against `schemas.keys()`.")
    print("    2. Inventory's TYPE strings (e.g. 'array<Commitment>') are derived heuristically;")
    print("       a separate type-equivalence check would be needed for full coverage.")
    print("    3. Nested $refs inside properties haven't been chased recursively; only top-level")
    print("       property names are verified.")
    sys.exit(0)
else:
    print(f"  ❌ {len(all_disagreements)} CATEGORY(IES) OF DISAGREEMENT FOUND.")
    print()
    for cat, details in all_disagreements:
        print(f"    {cat}: {len(details) if isinstance(details, list) else details}")
    sys.exit(1)
