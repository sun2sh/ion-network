#!/usr/bin/env python3
"""
fix_residuals.py — Apply the three residual fixes to ion.yaml.

PHASE 1: Convert machine-translatable x-ion-conditional → JSON Schema if/then/else
   Patterns recognised:
     "Required when X=Y"          → if {X: const Y} then {required: [field]}
     "Required when X is Y"        → same
     "Required if X=Y"             → same
     "Mandatory when X=Y"          → same
     "Required when role=BANK"     → same  (role is a field on the same schema)

   For each schema with conditional properties:
     - Group conditionals by their (trigger_field, trigger_value)
     - Emit a single allOf entry with one if/then per group
     - Strip the now-redundant x-ion-conditional marker on those fields
     - Leave x-ion-condition text in place as inline documentation

   Conditionals that don't match a recognised pattern remain as
   x-ion-conditional with their condition text — properly classified
   for human review.

PHASE 2: Standardise the two non-canonical x-beckn-attaches-to strings
   - "RatingInput (as ionRatingAttributes)" → "RatingInput.target.targetAttributes"
   - "Support.channels[*] (as an Attributes entry...)" → "Support.channels[*]"
     (with an x-ion-attach-mode: array-element annotation explaining the pattern)

PHASE 3: Source-of-truth choice
   We make ion.yaml the canonical source. Generate per-pack stub files
   that simply $ref into ion.yaml's components, replacing the legacy
   per-pack attributes.yaml content. The stubs satisfy "every pack has
   an attributes.yaml" while keeping the canonical definition single-sourced.

   (We don't overwrite the originals; we write the stubs to a separate
   tree under outputs/ion-network-clean/.)

Output:
  - ion_clean.yaml                — ion.yaml with all three fixes applied
  - residuals_fix_report.md       — per-fix audit log
  - ion-network-clean/            — regenerated pack stubs
"""

import yaml, re, sys, shutil
from pathlib import Path
from collections import defaultdict, OrderedDict

ION_YAML = Path("/mnt/user-data/outputs/ion.yaml")
BECKN_YAML = Path("/mnt/project/beckn__1_.yaml")
ION_ROOT = Path("/home/claude/ion-network-main")
OUT = Path("/mnt/user-data/outputs")

# YAML output that preserves order
class OrderedDumper(yaml.SafeDumper): pass
def _odict_rep(d, data): return d.represent_mapping("tag:yaml.org,2002:map", data.items())
OrderedDumper.add_representer(OrderedDict, _odict_rep)
OrderedDumper.ignore_aliases = lambda self, data: True

doc = yaml.safe_load(ION_YAML.read_text())
beckn = yaml.safe_load(BECKN_YAML.read_text())
beckn_objects = {n: set(s.get("properties",{}).keys())
                 for n, s in beckn["components"]["schemas"].items()
                 if isinstance(s, dict)}

report = []
def log(msg): report.append(msg)
log("# ion.yaml residuals fix report\n")


# ============================================================
# PHASE 1 — Convert machine-translatable conditionals to if/then/else
# ============================================================
log("\n## Phase 1 — Conditional → if/then/else conversion\n")

# Patterns that yield (trigger_field, trigger_value)
TRIGGER_PATTERNS = [
    # "when X = Y"  /  "when X=Y"  /  "if X = Y"  /  "if X=Y"
    re.compile(r"\b(?:when|if)\s+(\w+)\s*=\s*([\w_-]+)", re.I),
    # "when X is Y" — only catch when Y is uppercase enum-like (HALAL, PKP, BANK)
    re.compile(r"\bwhen\s+(\w+)\s+is\s+([A-Z][A-Z_]+)\b"),
    # "(X=Y)" parenthetical — common: "(businessType=PERORANGAN)"
    re.compile(r"\((\w+)=([A-Z][A-Z_]+)\)"),
    # "Mandatory when X=Y", "Required if X=Y" — covered by first pattern
]

def parse_condition(text):
    """Return list of (trigger_field, trigger_value) tuples extracted from condition text.
       Multiple "or"-separated conditions yield multiple tuples."""
    if not text or not isinstance(text, str):
        return []
    # Split on " or " to handle "Required when method=A or method=B"
    fragments = re.split(r"\s+or\s+", text, flags=re.I)
    found = []
    for frag in fragments:
        for pat in TRIGGER_PATTERNS:
            m = pat.search(frag)
            if m:
                trig_field = m.group(1)
                trig_value = m.group(2)
                # Filter: trigger_value must look like an enum value (uppercase or all-letter ID),
                # not an English noun. e.g. exclude "Required" or "individual".
                if (trig_value.isupper() or trig_value in ("true", "false")
                    or re.match(r"^[A-Z][A-Z_]+$", trig_value)):
                    found.append((trig_field, trig_value))
                break
    return found


def convert_conditionals_in_schema(schema, schema_name, path="$"):
    """Walk one schema, find conditional properties, classify each as:
       - in-schema: trigger field exists on the same schema  → emit if/then/else
       - cross-schema: trigger field exists elsewhere        → keep as marker, log rule
       - unparseable: condition text doesn't match a pattern → keep as marker

       Returns:
         in_schema_converted: list of (schema_name, trigger_field, trigger_value, [field_names])
         cross_schema_rules:  list of (schema_name, field, trigger_field, trigger_value, raw_text)
         unparseable:         list of (schema_name, field, raw_text)
    """
    if not isinstance(schema, dict):
        return [], [], []

    in_schema_converted = []
    cross_schema_rules = []
    unparseable = []
    props = schema.get("properties", {})
    if not isinstance(props, dict):
        return [], [], []

    groups = defaultdict(list)            # in-schema groupings
    successful_inschema_fields = set()
    cross_schema_fields = set()

    for pname, pdef in props.items():
        if not isinstance(pdef, dict):
            continue
        if not pdef.get("x-ion-conditional"):
            continue
        cond_text = pdef.get("x-ion-condition", "")
        triggers = parse_condition(cond_text)
        if not triggers:
            unparseable.append((schema_name, pname, cond_text))
            continue
        for tf, tv in triggers:
            if tf in props:
                groups[(tf, tv)].append(pname)
                successful_inschema_fields.add(pname)
            else:
                # Cross-schema rule
                cross_schema_rules.append((schema_name, pname, tf, tv, cond_text))
                cross_schema_fields.add(pname)

    # Emit if/then/else only for in-schema rules
    if groups:
        existing_allof = schema.get("allOf", []) or []
        new_entries = []
        for (trig_field, trig_value), field_list in sorted(groups.items()):
            entry = OrderedDict([
                ("if", OrderedDict([
                    ("properties", OrderedDict([
                        (trig_field, OrderedDict([("const", trig_value)])),
                    ])),
                    ("required", [trig_field]),
                ])),
                ("then", OrderedDict([
                    ("required", sorted(set(field_list))),
                ])),
            ])
            new_entries.append(entry)
            in_schema_converted.append((schema_name, trig_field, trig_value, sorted(set(field_list))))

        if existing_allof:
            existing_allof.extend(new_entries)
            schema["allOf"] = existing_allof
        else:
            schema["allOf"] = new_entries

    # Strip x-ion-conditional ONLY from in-schema converted fields
    for fname in successful_inschema_fields:
        if fname not in cross_schema_fields:  # don't strip if also cross-schema
            pdef = props[fname]
            pdef.pop("x-ion-conditional", None)

    # For cross-schema fields, replace marker with x-ion-conditional-cross-schema
    # so the validator knows these are not handled by this schema's allOf
    for fname in cross_schema_fields:
        pdef = props[fname]
        if fname not in successful_inschema_fields:
            pdef.pop("x-ion-conditional", None)
            pdef["x-ion-conditional-cross-schema"] = True

    return in_schema_converted, cross_schema_rules, unparseable


# Walk every schema in components.schemas
all_in_schema = []
all_cross_schema = []
all_unparseable = []

for sname, sdef in doc["components"]["schemas"].items():
    in_sch, cross, unp = convert_conditionals_in_schema(sdef, sname)
    all_in_schema.extend(in_sch)
    all_cross_schema.extend(cross)
    all_unparseable.extend(unp)

log(f"### Classification of {len(all_in_schema) + len(all_cross_schema) + len(all_unparseable)} parsed conditional fields\n")
log(f"- **In-schema (converted to JSON Schema if/then/else): {len(all_in_schema)}**")
log(f"- **Cross-schema (rule is across pack boundaries, kept as `x-ion-conditional-cross-schema`): {len(all_cross_schema)}**")
log(f"- **Unparseable / narrative-only (kept as `x-ion-conditional`): {len(all_unparseable)}**")

log("\n### In-schema if/then/else conversions (sample):\n")
for sname, tf, tv, fields in all_in_schema[:15]:
    log(f"  - `{sname}`: if `{tf}` == `{tv}` then required={fields}")
if len(all_in_schema) > 15:
    log(f"\n  ... and {len(all_in_schema)-15} more.")

log("\n### Cross-schema rules (need validator-level enforcement, not JSON Schema):\n")
log("These have been emitted to a separate machine-readable rules file `ion_conditional_rules.yaml` "
    "so a network validator (ONIX) can enforce them at the Attributes-bag composition level. "
    "JSON Schema can't enforce them because the trigger field lives in a different pack's schema "
    "but ends up in the same Beckn `*Attributes` bag at runtime.\n")
for sname, field, tf, tv, text in all_cross_schema[:10]:
    log(f"  - `{sname}.{field}` required when `{tf}=={tv}` (trigger lives outside this schema)")
if len(all_cross_schema) > 10:
    log(f"\n  ... and {len(all_cross_schema)-10} more.")

log(f"\n### Unparseable conditionals (need human review): {len(all_unparseable)}\n")
log("These have condition text that doesn't match a simple `field=value` pattern. "
    "Example texts include things like `Required for delivery addresses` (no field name "
    "given) or `Required when amount > 0` (numeric comparison, not equality). They "
    "remain marked `x-ion-conditional: true`.\n")
for sname, field, text in all_unparseable[:10]:
    log(f"  - `{sname}.{field}`: {text[:100]}")
if len(all_unparseable) > 10:
    log(f"\n  ... and {len(all_unparseable)-10} more.")

# Emit cross-schema rules file
rules_file = OUT / "ion_conditional_rules.yaml"
rules_doc = OrderedDict([
    ("version", "1.0.0"),
    ("description",
     "Cross-schema conditional requirements for ION. Each rule says: when the "
     "trigger field (somewhere in the same Beckn *Attributes bag) takes a given "
     "value, the listed field on the named schema becomes required. JSON Schema's "
     "if/then/else cannot express these because the trigger field lives in a "
     "different schema but ends up in the same composed Attributes bag at runtime. "
     "A network-level validator (ONIX) is the right place to enforce these."),
    ("rules", [
        OrderedDict([
            ("schema", sname),
            ("field", field),
            ("triggerField", tf),
            ("triggerValue", tv),
            ("rawCondition", text[:200]),
            ("enforcementLevel", "Attributes-bag-composition"),
        ])
        for sname, field, tf, tv, text in sorted(set(all_cross_schema))
    ]),
])
with open(rules_file, "w") as f:
    yaml.dump(rules_doc, f, Dumper=OrderedDumper, sort_keys=False, default_flow_style=False,
              width=100, allow_unicode=True)
log(f"\n**Cross-schema rules written to:** `{rules_file}`")

# Recount remaining conditionals
remaining_conditional = 0
def count_conditionals(node):
    global remaining_conditional
    if isinstance(node, dict):
        if node.get("x-ion-conditional"):
            remaining_conditional += 1
        for v in node.values(): count_conditionals(v)
    elif isinstance(node, list):
        for it in node: count_conditionals(it)
count_conditionals(doc)
log(f"\n**Remaining `x-ion-conditional` markers after Phase 1: {remaining_conditional}**")


# ============================================================
# PHASE 2 — Standardise non-canonical x-beckn-attaches-to
# ============================================================
log("\n\n## Phase 2 — Standardising x-beckn-attaches-to strings\n")

phase2_changes = []

# 2a. IONRatingAttributes — "RatingInput (as ionRatingAttributes)"
#     The Beckn RatingInput.target.targetAttributes IS the slot (Beckn defines
#     RatingInput with target object containing targetAttributes: Attributes).
if "IONRatingAttributes" in doc["components"]["schemas"]:
    schema = doc["components"]["schemas"]["IONRatingAttributes"]
    old = schema.get("x-beckn-attaches-to", "")
    if "(as ion" in old:
        new = "RatingInput.target.targetAttributes"
        schema["x-beckn-attaches-to"] = new
        phase2_changes.append(("IONRatingAttributes", old, new))

# 2b. IONSupportTicket — "Support.channels[*] (as an Attributes entry...)"
#     Support.channels[*] is an array of Attributes; ION fields appear inside each
#     entry's @type=ion:SupportTicket. The standard form is the array path; the
#     "@type=ion:..." discriminator is captured in x-jsonld which the schema already has.
if "IONSupportTicket" in doc["components"]["schemas"]:
    schema = doc["components"]["schemas"]["IONSupportTicket"]
    old = schema.get("x-beckn-attaches-to", "")
    if "Support.channels" in old:
        new = "Support.channels[*]"
        schema["x-beckn-attaches-to"] = new
        # Add an explicit discriminator for the array-element pattern
        schema["x-ion-attach-mode"] = "array-element-by-jsonld-type"
        phase2_changes.append(("IONSupportTicket", old, new))

# 2c. IONTicket — "ION Raise channel (off-Beckn)"
#     Mark this clearly as off-Beckn so verifiers don't flag it as a slot
if "IONTicket" in doc["components"]["schemas"]:
    schema = doc["components"]["schemas"]["IONTicket"]
    old = schema.get("x-beckn-attaches-to", "")
    if "off-Beckn" in old:
        new = "(off-Beckn — ION-only object, carried in /raise message body)"
        schema["x-beckn-attaches-to"] = new
        phase2_changes.append(("IONTicket", old, new))

log(f"### Standardised: {len(phase2_changes)}\n")
for name, old, new in phase2_changes:
    log(f"  - `{name}`")
    log(f"    - was: `{old}`")
    log(f"    - now: `{new}`")


# ============================================================
# Write ion_clean.yaml
# ============================================================
out_yaml = OUT / "ion_clean.yaml"
with open(out_yaml, "w") as f:
    yaml.dump(doc, f, Dumper=OrderedDumper, sort_keys=False, default_flow_style=False,
              width=100, allow_unicode=True)
log(f"\n## Output\n")
log(f"- `{out_yaml}` ({out_yaml.stat().st_size:,} bytes)")


# ============================================================
# PHASE 3 — Per-pack stubs that $ref into ion.yaml
# ============================================================
log("\n\n## Phase 3 — Per-pack stub generation\n")

# Build a map: schema name → which pack it came from
# We use the pack→names mapping that the original builder created. We replicate
# that here by re-reading the pack files.
pack_to_types = defaultdict(list)
for sector_dir in sorted((ION_ROOT/"schema/extensions").iterdir()):
    if not sector_dir.is_dir(): continue
    sector = sector_dir.name
    layer = "L4" if sector == "core" else "L5"
    for pack_dir in sorted(sector_dir.iterdir()):
        if not pack_dir.is_dir(): continue
        pack = pack_dir.name
        for v in pack_dir.iterdir():
            if not v.is_dir(): continue
            attrs = v / "attributes.yaml"
            if not attrs.exists(): continue
            old = yaml.safe_load(attrs.read_text())
            for tname in old.get("components",{}).get("schemas",{}).keys():
                pack_to_types[(layer, sector, pack)].append(tname)

clean_root = Path("/home/claude/ion-network-clean")
import subprocess
subprocess.run(["rm", "-rf", str(clean_root)], check=False)
clean_root.mkdir(parents=True, exist_ok=True)

new_schemas = doc["components"]["schemas"]
stub_count = 0

for (layer, sector, pack), tnames in sorted(pack_to_types.items()):
    pack_dir = clean_root / "schema" / "extensions" / sector / pack / "v1"
    pack_dir.mkdir(parents=True)
    stub = OrderedDict([
        ("openapi", "3.1.1"),
        ("info", OrderedDict([
            ("title", f"ION {sector}/{pack} Extension Pack (v1)"),
            ("description",
             f"This pack is now defined canonically inside the composed `ion.yaml`. "
             f"The schemas below are stubs that $ref into `ion.yaml` so that "
             f"any tool expecting per-pack file paths still resolves correctly. "
             f"The full schema definition lives at "
             f"`#/components/schemas/<TypeName>` in `../../../../api/v2.0.0/ion.yaml`."),
            ("version", "1.0.0"),
        ])),
        ("components", OrderedDict([
            ("schemas", OrderedDict([
                (tname, OrderedDict([
                    ("$ref", f"../../../../api/v2.0.0/ion.yaml#/components/schemas/{tname}"
                             + ("" if tname in new_schemas else ""))  # may be renamed
                ]))
                for tname in tnames
                if tname in new_schemas or f"{tname}__{sector}_{pack}" in new_schemas
            ])),
        ])),
    ])
    # Handle the renamed duplicate
    for tname in tnames:
        if tname not in new_schemas:
            renamed = f"{tname}__{sector}_{pack}"
            if renamed in new_schemas:
                stub["components"]["schemas"][tname] = OrderedDict([
                    ("$ref", f"../../../../api/v2.0.0/ion.yaml#/components/schemas/{renamed}")
                ])

    out_path = pack_dir / "attributes.yaml"
    with open(out_path, "w") as f:
        yaml.dump(stub, f, Dumper=OrderedDumper, sort_keys=False, default_flow_style=False,
                  width=100, allow_unicode=True)
    stub_count += 1

# Also copy the cleaned ion.yaml into the canonical location of the new tree
(clean_root / "schema" / "core" / "v2" / "api" / "v2.0.0").mkdir(parents=True)
shutil.copy(out_yaml, clean_root / "schema" / "core" / "v2" / "api" / "v2.0.0" / "ion.yaml")

log(f"### Per-pack stubs generated: {stub_count}\n")
log(f"Tree: `{clean_root}/`\n")
log("- Each stub at `schema/extensions/{sector}/{pack}/v1/attributes.yaml` contains "
    "only `$ref` entries pointing into `ion.yaml`'s components.")
log("- The canonical `ion.yaml` lives at `schema/core/v2/api/v2.0.0/ion.yaml`.\n")
log("This makes `ion.yaml` the single source of truth and removes the per-pack "
    "drift risk that's been catching us throughout this audit.\n")


# Write report
report_path = OUT / "residuals_fix_report.md"
with open(report_path, "w") as f:
    f.write("\n".join(report))

print(f"Wrote {out_yaml} ({out_yaml.stat().st_size:,} bytes)")
print(f"Wrote {report_path}")
print(f"Wrote {clean_root}/ (with {stub_count} pack stubs)")
print()
print(f"Phase 1 — conditional handling:")
print(f"  - in-schema → if/then/else: {len(all_in_schema)}")
print(f"  - cross-schema → rules file: {len(all_cross_schema)}")
print(f"  - unparseable → kept for human review: {len(all_unparseable)}")
print(f"Phase 2 — attaches-to standardised:    {len(phase2_changes)}")
print(f"Phase 3 — per-pack stubs generated:    {stub_count}")
print(f"Remaining x-ion-conditional markers:   {remaining_conditional}")
print(f"Cross-schema markers added:            {sum(1 for _ in all_cross_schema)}")
