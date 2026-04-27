"""
Build the integrated mapping for parsers / validators / docs:
For every Beckn endpoint:
  - which top-level message object does it carry?
  - which *Attributes slots can extension packs mount on?
  - which ION packs declare x-beckn-attaches-to that slot?

Output: inventory_endpoint_to_packs.csv  +  .md
"""
import yaml, csv, re
from pathlib import Path
from collections import defaultdict

BECKN = yaml.safe_load(Path("/mnt/project/beckn__1_.yaml").read_text())
ION_ROOT = Path("/home/claude/ion-network-main")
OUT = Path("/mnt/user-data/outputs")

schemas = BECKN["components"]["schemas"]
paths = BECKN["paths"]

# 1. Find every endpoint -> Action -> top-level Beckn object
endpoint_msgobj = []
for path, methods in paths.items():
    for method, op in methods.items():
        if not isinstance(op, dict): continue
        body = op.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
        if not isinstance(body, dict): continue
        msg = body.get("properties", {}).get("message", {})
        ref = msg.get("$ref")
        if not ref: continue
        action = ref.split("/")[-1]
        action_sch = schemas.get(action, {})
        # Find the top-level object reference inside the action
        for prop, pdef in action_sch.get("properties", {}).items():
            obj_name = None
            if isinstance(pdef, dict):
                if "$ref" in pdef:
                    obj_name = pdef["$ref"].split("/")[-1]
                elif "allOf" in pdef:
                    for it in pdef["allOf"]:
                        if isinstance(it, dict) and "$ref" in it:
                            obj_name = it["$ref"].split("/")[-1]
                            break
                elif pdef.get("type") == "array":
                    items = pdef.get("items", {})
                    if isinstance(items, dict) and "$ref" in items:
                        obj_name = items["$ref"].split("/")[-1]
            if obj_name:
                endpoint_msgobj.append({
                    "endpoint": path,
                    "action": action,
                    "messageProperty": prop,
                    "topLevelObject": obj_name,
                })

# 2. For each top-level object, walk into nested Beckn objects and discover every
# *Attributes slot they expose. We do a shallow walk: each named object's direct
# *Attributes properties.
def attrs_slots_on_object(obj_name, visited=None):
    """Return list of (containingObject, slotName) for every *Attributes slot reachable."""
    if visited is None:
        visited = set()
    if obj_name in visited:
        return []
    visited.add(obj_name)
    sch = schemas.get(obj_name, {})
    if not isinstance(sch, dict):
        return []
    out = []
    for prop, pdef in sch.get("properties", {}).items():
        if prop.endswith("Attributes"):
            out.append((obj_name, prop))
        # Recurse if it references another Beckn object
        nested = None
        if isinstance(pdef, dict):
            if "$ref" in pdef:
                nested = pdef["$ref"].split("/")[-1]
            elif "allOf" in pdef:
                for it in pdef["allOf"]:
                    if isinstance(it, dict) and "$ref" in it:
                        nested = it["$ref"].split("/")[-1]; break
            elif pdef.get("type") == "array":
                items = pdef.get("items", {})
                if isinstance(items, dict) and "$ref" in items:
                    nested = items["$ref"].split("/")[-1]
        if nested and nested in schemas and nested != "Attributes":
            out.extend(attrs_slots_on_object(nested, visited))
    return out

# 3. Read every ION pack and capture x-beckn-attaches-to
ion_attach = []  # list of {layer, sector, pack, type, attaches_to_raw}
for sector_dir in (ION_ROOT/"schema"/"extensions").iterdir():
    if not sector_dir.is_dir(): continue
    sector = sector_dir.name
    layer = "L4" if sector == "core" else "L5"
    for pack_dir in sector_dir.iterdir():
        if not pack_dir.is_dir(): continue
        pack = pack_dir.name
        for v in pack_dir.iterdir():
            if not v.is_dir(): continue
            attrs = v / "attributes.yaml"
            if not attrs.exists(): continue
            try:
                sch = yaml.safe_load(attrs.read_text())
            except Exception:
                continue
            for tname, tdef in sch.get("components", {}).get("schemas", {}).items():
                if isinstance(tdef, dict) and tdef.get("x-beckn-attaches-to"):
                    ion_attach.append({
                        "layer": layer, "sector": sector, "pack": pack,
                        "type": tname, "attaches_to_raw": tdef["x-beckn-attaches-to"],
                    })

# 4. Build slot key (e.g. "Offer.offerAttributes") from raw attaches-to
def normalize_slot(raw):
    """
    Try to extract 'Object.slot' form. If it's freeform text (reusable shape), return None.
    """
    raw_clean = raw.strip()
    # Common patterns:
    #   "Offer.offerAttributes"
    #   "Resource.resourceAttributes"
    #   "Performance.performanceAttributes"
    #   "Address (as ionAddressAttributes)"
    m = re.match(r"^([A-Z][A-Za-z]+)\.([a-zA-Z]+Attributes)\b", raw_clean)
    if m:
        return f"{m.group(1)}.{m.group(2)}"
    # "(reusable shape ...)" -> None
    if raw_clean.startswith("("):
        return None
    return raw_clean.split("\n")[0][:60]  # fallback: first line

slot_to_packs = defaultdict(list)
for r in ion_attach:
    slot = normalize_slot(r["attaches_to_raw"])
    slot_to_packs[slot].append(r)

# 5. For every endpoint, list slots and which ION packs mount each slot
out_rows = []
for ep in endpoint_msgobj:
    slots = attrs_slots_on_object(ep["topLevelObject"])
    if not slots:
        out_rows.append({
            "endpoint": ep["endpoint"],
            "action": ep["action"],
            "messageProperty": ep["messageProperty"],
            "topLevelObject": ep["topLevelObject"],
            "extensionSlot": "—",
            "containingObject": "—",
            "ionPacks": "(no extension slots)",
        })
        continue
    seen = set()
    for container, slot in slots:
        key = f"{container}.{slot}"
        if key in seen: continue
        seen.add(key)
        packs_here = slot_to_packs.get(key, [])
        pack_str = ", ".join(f"{p['layer']}:{p['sector']}/{p['pack']}({p['type']})" for p in packs_here) or "(no ION pack mounted)"
        out_rows.append({
            "endpoint": ep["endpoint"],
            "action": ep["action"],
            "messageProperty": ep["messageProperty"],
            "topLevelObject": ep["topLevelObject"],
            "extensionSlot": slot,
            "containingObject": container,
            "ionPacks": pack_str,
        })

# Write CSV
csv_path = OUT/"inventory_endpoint_to_packs.csv"
with open(csv_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["endpoint","action","messageProperty","topLevelObject",
                                       "containingObject","extensionSlot","ionPacks"])
    w.writeheader()
    for r in out_rows: w.writerow(r)

# Write markdown
md = ["# Endpoint × Object × Extension-Slot × ION Pack — Integrated Mapping\n",
      "Reading guide: pick an endpoint, see the top-level Beckn object it carries, the *Attributes slots reachable from that object, and the ION packs that declare attachment to each slot.\n",
      "Slots showing `(no ION pack mounted)` are valid Beckn extension points where ION has not (yet) defined a pack — a participant could in principle mount an NPOS there.\n",
      "Slots showing `—` mean the endpoint's top-level object has no `*Attributes` extension slots reachable.\n"]
prev_ep = None
for r in out_rows:
    if r["endpoint"] != prev_ep:
        md.append(f"\n## `{r['endpoint']}` → action `{r['action']}` → carries `{r['messageProperty']}: {r['topLevelObject']}`\n")
        md.append("| Containing object | Extension slot | ION packs mounted here |")
        md.append("|---|---|---|")
        prev_ep = r["endpoint"]
    md.append(f"| `{r['containingObject']}` | `{r['extensionSlot']}` | {r['ionPacks']} |")
(OUT/"inventory_endpoint_to_packs.md").write_text("\n".join(md))

# Also list packs that declare attaches-to but couldn't normalise (reusable shapes etc.)
unresolved = [p for p in ion_attach if normalize_slot(p["attaches_to_raw"]) is None]
print(f"Endpoint-pack mapping rows: {len(out_rows)}")
print(f"ION packs with reusable/non-slot attaches-to (not in mapping): {len(unresolved)}")
for u in unresolved[:5]:
    print(f"  e.g. {u['layer']}:{u['sector']}/{u['pack']}/{u['type']} — '{u['attaches_to_raw'][:80]}'")
print()
print(f"Files written:")
for f in ["inventory_endpoint_to_packs.csv","inventory_endpoint_to_packs.md"]:
    p = OUT/f
    print(f"  {f}  ({p.stat().st_size:,} bytes)")
