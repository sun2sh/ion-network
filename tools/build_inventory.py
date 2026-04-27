"""
Build a structured inventory of every Beckn object and every ION pack object,
covering: endpoint context, object name, attribute name, type, level (object|attribute),
required flag, extendable flag (= has *Attributes slot or is itself an Attributes bag),
links-to (what other object/schema this attribute references), and which Beckn endpoints
use this object.

Output:
- inventory_beckn.csv
- inventory_ion.csv
- inventory_beckn.md  (human-readable)
- inventory_ion.md
"""
import yaml, csv, json, re
from pathlib import Path
from collections import defaultdict

BECKN_PATH = Path("/mnt/project/beckn__1_.yaml")
ION_ROOT = Path("/home/claude/ion-network-main")

OUT = Path("/mnt/user-data/outputs")
OUT.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------
# Parse beckn.yaml
# ------------------------------------------------------------------
beckn = yaml.safe_load(BECKN_PATH.read_text())
schemas = beckn.get("components", {}).get("schemas", {})
paths = beckn.get("paths", {})

# 1. Map every endpoint -> which Action schema it uses, and trace down to top-level objects used.
endpoint_to_action = {}
for path, methods in paths.items():
    for method_name, op in methods.items():
        if not isinstance(op, dict):
            continue
        body = op.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
        # Walk to find the message ref
        if isinstance(body, dict):
            msg = body.get("properties", {}).get("message", {})
            ref = msg.get("$ref")
            if ref:
                action_name = ref.split("/")[-1]
                endpoint_to_action[(method_name.upper(), path)] = action_name

# 2. For each Action schema, find which top-level Beckn object it carries
action_to_object = {}
for name, sch in schemas.items():
    if not name.endswith("Action"):
        continue
    # Action schemas usually have properties.{contract|catalogs|tracking|support|...} -> $ref
    props = sch.get("properties", {})
    for prop, pdef in props.items():
        if isinstance(pdef, dict):
            # Direct $ref
            if "$ref" in pdef:
                action_to_object.setdefault(name, []).append((prop, pdef["$ref"].split("/")[-1]))
            # allOf with $ref
            elif "allOf" in pdef:
                for item in pdef["allOf"]:
                    if isinstance(item, dict) and "$ref" in item:
                        action_to_object.setdefault(name, []).append((prop, item["$ref"].split("/")[-1]))
            # array of $refs
            elif pdef.get("type") == "array":
                items = pdef.get("items", {})
                if isinstance(items, dict) and "$ref" in items:
                    action_to_object.setdefault(name, []).append((prop, items["$ref"].split("/")[-1]))

# 3. Build object-to-endpoints reverse map
object_to_endpoints = defaultdict(set)
for (method, path), action in endpoint_to_action.items():
    for prop, obj in action_to_object.get(action, []):
        object_to_endpoints[obj].add(path)

# 4. For each Beckn schema, walk its properties and produce inventory rows
def is_attributes_slot(prop_name, prop_def):
    """True if the property is one of the *Attributes extension slots."""
    if prop_name.endswith("Attributes"):
        return True
    # Detect by $ref to Attributes
    if isinstance(prop_def, dict):
        if prop_def.get("$ref", "").endswith("/Attributes"):
            return True
        if "allOf" in prop_def:
            for it in prop_def["allOf"]:
                if isinstance(it, dict) and it.get("$ref", "").endswith("/Attributes"):
                    return True
    return False

def resolve_type(prop_def, schemas):
    """Render a one-line type description for a property definition."""
    if not isinstance(prop_def, dict):
        return str(prop_def)
    if "$ref" in prop_def:
        return prop_def["$ref"].split("/")[-1]
    if "allOf" in prop_def:
        parts = []
        for it in prop_def["allOf"]:
            if isinstance(it, dict) and "$ref" in it:
                parts.append(it["$ref"].split("/")[-1])
            elif isinstance(it, dict) and "properties" in it:
                parts.append("(inline)")
        return " + ".join(parts) if parts else "object"
    if prop_def.get("type") == "array":
        items = prop_def.get("items", {})
        if isinstance(items, dict):
            if "$ref" in items:
                return f"array<{items['$ref'].split('/')[-1]}>"
            if items.get("type"):
                return f"array<{items['type']}>"
        return "array"
    if "enum" in prop_def:
        return f"enum({', '.join(map(str, prop_def['enum']))[:60]})"
    if prop_def.get("type"):
        if prop_def.get("format"):
            return f"{prop_def['type']}<{prop_def['format']}>"
        return prop_def["type"]
    return "object"

# Pick the Beckn objects that are "real" data objects users will encounter
# (skip enum-only / tiny utility schemas that don't appear in payloads directly)
BECKN_OBJECTS = [
    "Context", "Contract", "Commitment", "Resource", "Offer",
    "Consideration", "Settlement", "Performance", "Participant",
    "Address", "Catalog", "Provider", "Location", "Descriptor",
    "Attributes", "RequestDigest", "Document", "MediaFile",
    "Tracking", "Support", "RatingInput", "FormSubmission",
    "Intent", "TimePeriod", "GeoJSONGeometry", "SpatialConstraint",
    "Signature", "CounterSignature", "Ack",
]

beckn_rows = []
for obj_name in BECKN_OBJECTS:
    sch = schemas.get(obj_name)
    if not sch:
        continue
    obj_required = set(sch.get("required", []))
    obj_addl = sch.get("additionalProperties", "(open)")
    obj_props = sch.get("properties", {})
    # Determine if this object is extendable by being or carrying an Attributes bag
    is_attrs_bag = (obj_name == "Attributes")
    has_attrs_slot = any(p.endswith("Attributes") for p in obj_props)
    extendable = "yes (Attributes bag, anything goes)" if is_attrs_bag else \
                 ("yes (via *Attributes slot)" if has_attrs_slot else "no")

    endpoints = sorted(object_to_endpoints.get(obj_name, []))
    endpoint_str = ", ".join(endpoints) if endpoints else "(nested object — inherits parent's endpoints)"

    # Object-level row
    beckn_rows.append({
        "object": obj_name,
        "level": "object",
        "attribute": "",
        "type": "object",
        "required_on_object": "",
        "extendable": extendable,
        "additionalProperties": str(obj_addl),
        "links_to": "",
        "used_in_endpoints": endpoint_str,
        "object_required_fields": ", ".join(sorted(obj_required)),
        "notes": "",
    })

    # Attribute-level rows
    for prop_name, prop_def in obj_props.items():
        type_str = resolve_type(prop_def, schemas)
        # links_to: if the type references another known schema
        links = ""
        if isinstance(prop_def, dict):
            if "$ref" in prop_def:
                links = prop_def["$ref"].split("/")[-1]
            elif "allOf" in prop_def:
                for it in prop_def["allOf"]:
                    if isinstance(it, dict) and "$ref" in it:
                        links = it["$ref"].split("/")[-1]
                        break
            elif prop_def.get("type") == "array":
                items = prop_def.get("items", {})
                if isinstance(items, dict) and "$ref" in items:
                    links = items["$ref"].split("/")[-1]
        is_slot = is_attributes_slot(prop_name, prop_def)
        slot_marker = "yes (extension slot — ION mounts here)" if is_slot else "no"
        notes = ""
        if is_slot:
            notes = "ION packs attach here via x-beckn-attaches-to"
        if isinstance(prop_def, dict) and prop_def.get("description"):
            d = prop_def["description"].strip().split("\n")[0][:120]
            notes = (notes + " | " if notes else "") + d
        beckn_rows.append({
            "object": obj_name,
            "level": "attribute",
            "attribute": prop_name,
            "type": type_str,
            "required_on_object": "yes" if prop_name in obj_required else "no",
            "extendable": slot_marker,
            "additionalProperties": "",
            "links_to": links,
            "used_in_endpoints": "",
            "object_required_fields": "",
            "notes": notes,
        })

# ------------------------------------------------------------------
# Parse ION packs
# ------------------------------------------------------------------
ion_packs_dir = ION_ROOT / "schema" / "extensions"
ion_rows = []

def parse_ion_pack(attr_yaml_path, layer, sector, pack):
    try:
        sch = yaml.safe_load(attr_yaml_path.read_text())
    except Exception as e:
        return [{"layer": layer, "sector": sector, "pack": pack, "object": "(parse error)",
                 "level": "object", "attribute": "", "type": str(e)[:80], "attaches_to": "", "required": "", "notes": ""}]
    rows = []
    components = sch.get("components", {}).get("schemas", {})
    if not components:
        return rows
    for type_name, type_def in components.items():
        if not isinstance(type_def, dict):
            continue
        attaches = type_def.get("x-beckn-attaches-to", "")
        required = set(type_def.get("required", []))
        addl = type_def.get("additionalProperties", "(open)")
        props = type_def.get("properties", {})

        # Object-level row
        rows.append({
            "layer": layer,
            "sector": sector,
            "pack": pack,
            "object": type_name,
            "level": "object",
            "attribute": "",
            "type": "object",
            "attaches_to": attaches,
            "required": "",
            "additionalProperties": str(addl),
            "object_required_fields": ", ".join(sorted(required)),
            "notes": (type_def.get("description","").strip().split("\n")[0][:120]) if type_def.get("description") else "",
        })

        for pname, pdef in props.items():
            type_str = resolve_type(pdef, {})
            note = ""
            if isinstance(pdef, dict):
                if pdef.get("description"):
                    note = pdef["description"].strip().split("\n")[0][:120]
                # ION-specific markers
                if pdef.get("x-ion-mandatory"):
                    note = (note + " | " if note else "") + f"x-ion-mandatory: {pdef['x-ion-mandatory']}"
            rows.append({
                "layer": layer,
                "sector": sector,
                "pack": pack,
                "object": type_name,
                "level": "attribute",
                "attribute": pname,
                "type": type_str,
                "attaches_to": "",
                "required": "yes" if pname in required else "no",
                "additionalProperties": "",
                "object_required_fields": "",
                "notes": note,
            })
    return rows

# Walk extension dirs
for sector_dir in sorted(ion_packs_dir.iterdir()):
    if not sector_dir.is_dir():
        continue
    sector = sector_dir.name
    layer = "L4" if sector == "core" else "L5"
    for pack_dir in sorted(sector_dir.iterdir()):
        if not pack_dir.is_dir():
            continue
        pack = pack_dir.name
        # find the attributes.yaml file
        for v in pack_dir.iterdir():
            if v.is_dir():
                attrs = v / "attributes.yaml"
                if attrs.exists():
                    ion_rows.extend(parse_ion_pack(attrs, layer, sector, pack))

# ------------------------------------------------------------------
# Write outputs
# ------------------------------------------------------------------
def write_csv(rows, fields, path):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)

beckn_fields = ["object","level","attribute","type","required_on_object","extendable",
                "additionalProperties","links_to","used_in_endpoints","object_required_fields","notes"]
ion_fields = ["layer","sector","pack","object","level","attribute","type","attaches_to",
              "required","additionalProperties","object_required_fields","notes"]

write_csv(beckn_rows, beckn_fields, OUT/"inventory_beckn.csv")
write_csv(ion_rows, ion_fields, OUT/"inventory_ion.csv")

# Markdown summaries (concise — one section per object)
def beckn_md(rows):
    out = ["# Beckn v2.0.0 Object Inventory\n",
           "Generated from `beckn.yaml`. For each top-level object, this lists every property,\n"
           "its type, whether it's required, and whether ION can extend through it.\n"]
    by_obj = defaultdict(list)
    obj_meta = {}
    for r in rows:
        if r["level"] == "object":
            obj_meta[r["object"]] = r
        else:
            by_obj[r["object"]].append(r)
    for obj_name in BECKN_OBJECTS:
        if obj_name not in obj_meta:
            continue
        m = obj_meta[obj_name]
        out.append(f"\n## {obj_name}\n")
        out.append(f"- **additionalProperties**: `{m['additionalProperties']}`")
        out.append(f"- **required fields on this object**: `{m['object_required_fields'] or '—'}`")
        out.append(f"- **extendable**: {m['extendable']}")
        out.append(f"- **used in endpoints**: {m['used_in_endpoints']}\n")
        out.append("| Attribute | Type | Required | Extension slot? | Links to | Notes |")
        out.append("|---|---|---|---|---|---|")
        for r in by_obj[obj_name]:
            out.append(f"| `{r['attribute']}` | `{r['type']}` | {r['required_on_object']} | "
                       f"{r['extendable']} | {r['links_to']} | {r['notes']} |")
    return "\n".join(out)

def ion_md(rows):
    out = ["# ION Extension Pack Inventory\n",
           "Generated from `schema/extensions/{core,trade,logistics}/<pack>/v1/attributes.yaml`.\n"
           "Each pack carries an `x-beckn-attaches-to` annotation declaring which Beckn slot it mounts onto.\n"]
    # Group: layer -> sector -> pack -> [rows]
    grouped = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    obj_meta = {}
    for r in rows:
        key = (r["layer"], r["sector"], r["pack"], r["object"])
        if r["level"] == "object":
            obj_meta[key] = r
        else:
            grouped[r["layer"]][r["sector"]][r["pack"]].append(r)
    for layer in sorted(grouped):
        out.append(f"\n# {layer} — " + ("ION core (cross-sector)" if layer=="L4" else "ION sector packs"))
        for sector in sorted(grouped[layer]):
            out.append(f"\n## Sector: `{sector}`")
            for pack in sorted(grouped[layer][sector]):
                out.append(f"\n### Pack: `{sector}/{pack}/v1`\n")
                # group by object
                by_obj = defaultdict(list)
                for r in grouped[layer][sector][pack]:
                    by_obj[r["object"]].append(r)
                for obj_name in sorted(by_obj):
                    key = (layer, sector, pack, obj_name)
                    m = obj_meta.get(key, {})
                    out.append(f"\n#### `{obj_name}`")
                    if m:
                        out.append(f"- **attaches to**: `{m['attaches_to'] or '—'}`")
                        out.append(f"- **additionalProperties**: `{m['additionalProperties']}`")
                        out.append(f"- **object-required fields**: `{m['object_required_fields'] or '—'}`")
                        if m.get("notes"):
                            out.append(f"- **note**: {m['notes']}")
                    out.append("\n| Attribute | Type | Required | Notes |")
                    out.append("|---|---|---|---|")
                    for r in by_obj[obj_name]:
                        out.append(f"| `{r['attribute']}` | `{r['type']}` | {r['required']} | {r['notes']} |")
    return "\n".join(out)

(OUT/"inventory_beckn.md").write_text(beckn_md(beckn_rows))
(OUT/"inventory_ion.md").write_text(ion_md(ion_rows))

# Print summary
print(f"Beckn inventory rows: {len(beckn_rows)} ({sum(1 for r in beckn_rows if r['level']=='object')} objects)")
print(f"ION inventory rows:   {len(ion_rows)} ({sum(1 for r in ion_rows if r['level']=='object')} types across ION packs)")
print()
print("Files written to /mnt/user-data/outputs/:")
for f in ["inventory_beckn.csv","inventory_beckn.md","inventory_ion.csv","inventory_ion.md"]:
    p = OUT/f
    print(f"  {f}  ({p.stat().st_size:,} bytes)")
