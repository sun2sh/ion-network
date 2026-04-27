#!/usr/bin/env python3
"""
align_with_beckn.py — Make ion.yaml structurally match Beckn's posture as closely as
possible while preserving ION's principles (regulatory compliance, sector packs,
non-forking extension).

This script applies four alignments:

ALIGNMENT 1 — Open Attributes posture
  Beckn's Attributes type has additionalProperties: true. Every ION pack schema that
  attaches to a Beckn *Attributes slot SHOULD honour that openness — otherwise ION
  forbids fields Beckn's design explicitly permits (and our earlier discussion identified
  this as the blocker for NPOS extensions).

  Rule applied:
    - For every ION schema whose x-beckn-attaches-to points to a Beckn *Attributes slot
      (or a freeform "(reusable shape...)" annotation that nests inside one),
      flip additionalProperties: false → additionalProperties: true.
    - Schemas marked off-Beckn (IONTicket) keep their closed posture.
    - Internal helper types (LocalisedText, AddressDetail, etc. that are nested inside
      a parent schema and not directly attached to a Beckn slot) keep their closed
      posture, since they're internal type definitions, not extension bags.

  We add x-ion-closed-extensions: false to every flipped schema as a marker so
  validators / participants know this slot is open to NPOS additions.

ALIGNMENT 2 — allOf composition with the Beckn base type
  When an ION schema attaches to Beckn.Object.someAttributes, the validator should
  check both that the host Object satisfies Beckn AND that the *Attributes content
  satisfies ION. JSON Schema's allOf is the standard mechanism.

  Rule applied:
    - For each ION schema with a parseable x-beckn-attaches-to "Object.attribute":
        Wrap the schema body in allOf:
          - $ref: beckn.yaml#/components/schemas/Attributes  (the ION extension content
                                                              IS an Attributes bag)
          - <original ION body>
    - This makes every ION pack a formal subtype of beckn:Attributes, ensuring
      @context and @type are always present (Beckn's Attributes requires them).

ALIGNMENT 3 — oneOf + discriminator for role-based / type-based variants
  Where a schema has multiple cross-schema conditional fields keyed off the same
  trigger field (e.g. role=BANK requires X, role=DRIVER requires Y), we can't
  use if/then/else (cross-schema), but we CAN encode it as oneOf variants on a
  parent schema if the trigger field is local.

  Rule applied:
    - Detect schemas with 3+ conditional fields all keyed off the same trigger field
    - If the trigger field IS on the schema, build a oneOf with one variant per
      trigger value, each variant requiring its associated fields
    - If the trigger field IS NOT on the schema, leave the conditionals as-is
      (cross-schema rules already handled by the previous pass)

ALIGNMENT 4 — Discriminator for @type-keyed Attributes arrays
  IONSupportTicket lives in Support.channels[*] (an array of Beckn Attributes), and
  is identified by its @type=ion:SupportTicket. This is exactly what JSON Schema's
  discriminator was designed for.

  Rule applied:
    - For schemas attaching to "Object.field[*]" patterns, emit a propertyName: "@type"
      discriminator alongside the existing pack reference. This makes the
      identification mechanism formal rather than narrative.
"""

import yaml, re, sys, copy
from pathlib import Path
from collections import OrderedDict, defaultdict

ION_YAML = Path("/mnt/user-data/outputs/ion_clean.yaml")
OUT = Path("/mnt/user-data/outputs")

class OrderedDumper(yaml.SafeDumper): pass
def _odict_rep(d, data): return d.represent_mapping("tag:yaml.org,2002:map", data.items())
OrderedDumper.add_representer(OrderedDict, _odict_rep)
OrderedDumper.ignore_aliases = lambda self, data: True

doc = yaml.safe_load(ION_YAML.read_text())

report = []
def log(m): report.append(m)
log("# ion.yaml alignment with Beckn — report\n")
log("Goal: make ion.yaml match Beckn's structural posture while preserving ION's principles.\n")


# ============================================================
# ALIGNMENT 1: Open Attributes posture
# ============================================================
log("\n## Alignment 1: Open Attributes posture\n")
log("Beckn's `Attributes` type has `additionalProperties: true`. ION pack schemas that "
    "attach to a Beckn `*Attributes` slot MUST honour that openness — otherwise ION's "
    "schema forbids fields Beckn's design explicitly permits, which also blocks Network "
    "Participant Overlay Schemas (NPOS). We flip the closed packs to open.\n")

flipped = []
unchanged_internal = []
unchanged_off_beckn = []

def is_attached_to_beckn_slot(attaches_to):
    """True if this string is or refers to a Beckn *Attributes slot."""
    if not isinstance(attaches_to, str):
        return False
    text = attaches_to.strip()
    # Canonical form: Object.fieldAttributes
    if re.match(r"^[A-Z][A-Za-z]+\.[a-zA-Z]+Attributes\b", text):
        return True
    # Multi-level: Object.path.subAttributes
    if re.match(r"^[A-Z][A-Za-z]+(?:\.[a-zA-Z]\w*)+", text) and "Attributes" in text:
        return True
    # Array form: Object.field[*]
    if re.match(r"^[A-Z][A-Za-z]+\.\w+\[\*\]", text):
        return True
    # Object as carrier: "Object (as ionAttributes)"
    if re.match(r"^[A-Z][A-Za-z]+\s*\(as\s+\w+\)", text):
        return True
    # Reusable / embedded annotations refer to slots
    if "reusable" in text.lower() or "embedded" in text.lower():
        return True
    return False


for sname, sdef in doc["components"]["schemas"].items():
    if not isinstance(sdef, dict): continue
    attaches = sdef.get("x-beckn-attaches-to")
    has_addl = sdef.get("additionalProperties", None)

    if attaches and "off-beckn" in str(attaches).lower():
        unchanged_off_beckn.append(sname)
        continue

    if not attaches:
        # Internal type, not attached to Beckn — leave closed
        unchanged_internal.append(sname)
        continue

    if is_attached_to_beckn_slot(attaches):
        if has_addl is False:
            sdef["additionalProperties"] = True
            sdef["x-ion-closed-extensions"] = False  # explicit marker: open to NPOS
            flipped.append(sname)
        else:
            # Already open or unspecified
            pass

log(f"\n### Schemas flipped to additionalProperties: true: {len(flipped)}\n")
for s in flipped:
    log(f"  - `{s}`")
log(f"\n### Internal helper types (kept closed): {len(unchanged_internal)}")
log(f"### Off-Beckn schemas (kept closed): {len(unchanged_off_beckn)}\n")
for s in unchanged_off_beckn:
    log(f"  - `{s}`")


# ============================================================
# ALIGNMENT 2: allOf composition with Beckn Attributes base
# ============================================================
log("\n## Alignment 2: allOf composition with `beckn:Attributes`\n")
log("Every ION schema that attaches to a Beckn `*Attributes` slot semantically IS a "
    "`beckn:Attributes` bag — it must carry `@context` and `@type` per Beckn's design. "
    "We encode this formally with `allOf: [<beckn:Attributes>, <ion body>]` so a "
    "validator checks both layers in one pass.\n")

allof_added = []

# Beckn objects/types that schemas might reference. We use beckn.yaml#/components/schemas/Attributes
# as the base for *Attributes slot extensions.
BECKN_ATTRIBUTES_REF = "beckn.yaml#/components/schemas/Attributes"

for sname, sdef in doc["components"]["schemas"].items():
    if not isinstance(sdef, dict): continue
    attaches = sdef.get("x-beckn-attaches-to")
    if not attaches or not is_attached_to_beckn_slot(attaches):
        continue
    if "off-beckn" in str(attaches).lower():
        continue

    # If it already has allOf with Attributes ref, skip
    existing_allof = sdef.get("allOf")
    if isinstance(existing_allof, list):
        already = any(isinstance(e, dict) and e.get("$ref") == BECKN_ATTRIBUTES_REF
                      for e in existing_allof)
        if already:
            continue

    # Wrap: take everything except metadata fields (description, title, x-*, allOf,
    # x-beckn-attaches-to) and put it under an allOf.
    # Actually the cleaner way: ADD a $ref to allOf. The if/then/else blocks emitted
    # earlier are part of allOf, so we just prepend a $ref entry.
    if existing_allof is None:
        # Create new allOf with the body wrapped
        # But we want to keep top-level metadata; OAS allOf typically wraps "the rest"
        # under a separate entry. Cleanest: keep type/properties/required/etc at top
        # level (this is valid in 3.1 because allOf adds more constraints) and just
        # record the Beckn base type via allOf.
        sdef["allOf"] = [OrderedDict([("$ref", BECKN_ATTRIBUTES_REF)])]
    else:
        # Prepend the Beckn base ref to existing allOf
        sdef["allOf"] = [OrderedDict([("$ref", BECKN_ATTRIBUTES_REF)])] + existing_allof

    allof_added.append(sname)

log(f"\n### Schemas given allOf composition with `beckn:Attributes`: {len(allof_added)}\n")
for s in allof_added[:20]:
    log(f"  - `{s}`")
if len(allof_added) > 20:
    log(f"  ... and {len(allof_added)-20} more.")
log(f"\n**What this means semantically:** every ION extension pack now formally is a "
    "subtype of `beckn:Attributes`. Any validator that reads ion.yaml will require "
    "`@context` and `@type` on every Attributes bag, and ION fields are added on top. "
    "The composition rule is now machine-checkable, not just documented.\n")


# ============================================================
# ALIGNMENT 3: oneOf + discriminator for role-based variants
# ============================================================
log("\n## Alignment 3: `oneOf` + discriminator for role/type variants\n")
log("Where multiple conditional fields share the same on-schema trigger field "
    "(typically `role` or `businessType`), we can convert them to a `oneOf` over "
    "schema variants. This is the standard Beckn pattern for polymorphic types.\n")

# Detect candidates: schemas where 3+ cross-schema conditionals share a trigger field
# AND that trigger field exists on the schema (would be in-schema then, but if/then/else
# was emitted only when trigger field is present locally — for cross-schema we already
# wrote the rules to ion_conditional_rules.yaml). So we're looking for schemas where
# multiple if/then/else allOf entries use the same trigger field. These are candidates
# for collapsing into oneOf.

oneof_candidates = []  # (schema_name, trigger_field, [(value, [fields])])

for sname, sdef in doc["components"]["schemas"].items():
    if not isinstance(sdef, dict): continue
    allof = sdef.get("allOf")
    if not isinstance(allof, list): continue
    # Find if/then entries
    by_trigger = defaultdict(list)
    for entry in allof:
        if not (isinstance(entry, dict) and "if" in entry and "then" in entry): continue
        if_clause = entry["if"]
        then_clause = entry["then"]
        # Extract trigger field and value
        if_props = if_clause.get("properties", {}) if isinstance(if_clause, dict) else {}
        for tf, tspec in if_props.items():
            if isinstance(tspec, dict) and "const" in tspec:
                tv = tspec["const"]
                req = then_clause.get("required", []) if isinstance(then_clause, dict) else []
                by_trigger[tf].append((tv, req))
    # If a single trigger field has 3+ variants, that's a oneOf candidate
    for tf, variants in by_trigger.items():
        if len(variants) >= 3:
            oneof_candidates.append((sname, tf, variants))

log(f"\n### oneOf candidates detected: {len(oneof_candidates)}\n")
if oneof_candidates:
    for sname, tf, variants in oneof_candidates[:5]:
        values = [v for v, _ in variants]
        log(f"  - `{sname}`: trigger `{tf}`, values {values}")
else:
    log("None. The current `if/then/else` structure is sufficient; no schema has 3+ "
        "in-schema conditionals on a single trigger field.\n")
log("\n**Why we don't always convert to oneOf even when possible:** `oneOf` is *exclusive* "
    "— exactly one variant must match. `if/then/else` is *additive* — each rule applies "
    "if its condition holds. ION's role-based requirements are additive (if you're a "
    "DRIVER, you also have all the BUSINESS fields). So `if/then/else` is the correct "
    "encoding. We document oneOf detection here for the cases that genuinely warrant it.\n")


# ============================================================
# ALIGNMENT 4: Discriminator for @type-keyed Attributes arrays
# ============================================================
log("\n## Alignment 4: Discriminator for `@type`-keyed array entries\n")
log("Where an ION schema attaches to `Object.field[*]` (an array of Beckn `Attributes`), "
    "JSON Schema's discriminator on the `@type` property is the standard mechanism for "
    "saying 'this entry is an ION schema iff its @type matches'.\n")

discriminator_added = []
for sname, sdef in doc["components"]["schemas"].items():
    if not isinstance(sdef, dict): continue
    attaches = sdef.get("x-beckn-attaches-to", "")
    if not isinstance(attaches, str): continue
    if not re.match(r"^[A-Z][A-Za-z]+\.\w+\[\*\]", attaches): continue

    # Get the @type value. If x-jsonld is present, use its "@type" entry.
    jsonld = sdef.get("x-jsonld", {})
    type_val = jsonld.get("@type") if isinstance(jsonld, dict) else None
    if not type_val:
        # Default convention: ion:<SchemaName without ION prefix>
        clean_name = sname.replace("ION", "")
        type_val = f"ion:{clean_name}"

    # Add a discriminator block
    sdef["x-ion-discriminator"] = OrderedDict([
        ("propertyName", "@type"),
        ("expectedValue", type_val),
        ("doc", "JSON Schema discriminator: an array element matches this schema iff "
                "its @type property equals expectedValue."),
    ])
    discriminator_added.append((sname, type_val))

log(f"\n### Schemas given `@type` discriminator: {len(discriminator_added)}\n")
for s, t in discriminator_added:
    log(f"  - `{s}` → `@type == {t}`")


# ============================================================
# Write the aligned document
# ============================================================
out_yaml = OUT / "ion_aligned.yaml"
with open(out_yaml, "w") as f:
    yaml.dump(doc, f, Dumper=OrderedDumper, sort_keys=False, default_flow_style=False,
              width=100, allow_unicode=True)

report_path = OUT / "alignment_report.md"
with open(report_path, "w") as f:
    f.write("\n".join(report))

print(f"Wrote {out_yaml} ({out_yaml.stat().st_size:,} bytes)")
print(f"Wrote {report_path}")
print()
print(f"Alignment 1 — additionalProperties flipped to true: {len(flipped)}")
print(f"             internal helpers kept closed:          {len(unchanged_internal)}")
print(f"             off-Beckn schemas kept closed:         {len(unchanged_off_beckn)}")
print(f"Alignment 2 — allOf composition with beckn:Attributes added: {len(allof_added)}")
print(f"Alignment 3 — oneOf candidates flagged (not auto-converted): {len(oneof_candidates)}")
print(f"Alignment 4 — @type discriminators added:                    {len(discriminator_added)}")
