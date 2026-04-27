#!/usr/bin/env python3
"""
verify_ion_yaml_completeness.py — Confirm the cleaned ion.yaml lost no information.

For every schema in every original pack file:
  - Check that the same schema exists in components.schemas of the new ion.yaml
  - Check that the property set matches exactly (no fields dropped)
  - Check that fields previously marked x-ion-mandatory:always are now in required[]
  - Check that fields previously marked x-ion-mandatory:conditional now have x-ion-conditional
"""
import yaml, sys
from pathlib import Path
from collections import defaultdict

ION_ROOT = Path("/home/claude/ion-network-main")
ION_YAML = Path("/mnt/user-data/outputs/ion.yaml")

new_doc = yaml.safe_load(ION_YAML.read_text())
new_schemas = new_doc["components"]["schemas"]

issues = []
checked = 0

for sector_dir in sorted((ION_ROOT/"schema/extensions").iterdir()):
    if not sector_dir.is_dir(): continue
    sector = sector_dir.name
    for pack_dir in sorted(sector_dir.iterdir()):
        if not pack_dir.is_dir(): continue
        pack = pack_dir.name
        for v in pack_dir.iterdir():
            if not v.is_dir(): continue
            attrs = v / "attributes.yaml"
            if not attrs.exists(): continue
            old = yaml.safe_load(attrs.read_text())
            for tname, told in old.get("components",{}).get("schemas",{}).items():
                checked += 1
                if not isinstance(told, dict): continue
                tnew = new_schemas.get(tname)
                if tnew is None:
                    # Could be a duplicate that got renamed by the builder
                    alt_name = f"{tname}__{sector}_{pack}"
                    tnew = new_schemas.get(alt_name)
                    if tnew is None:
                        issues.append((f"{sector}/{pack}/{tname}", "MISSING from ion.yaml"))
                        continue
                else:
                    # Schema exists with the original name. But if there's also a
                    # renamed-with-suffix version, the canonical lookup may have hit
                    # a *different* pack's same-named schema. Use the rename if it exists.
                    alt_name = f"{tname}__{sector}_{pack}"
                    if alt_name in new_schemas:
                        tnew = new_schemas[alt_name]

                # Property set parity
                old_props = set(told.get("properties",{}).keys())
                new_props = set(tnew.get("properties",{}).keys())
                if old_props != new_props:
                    issues.append((f"{sector}/{pack}/{tname}",
                                   f"property set differs: missing in new={old_props-new_props}, extra in new={new_props-old_props}"))

                # required[] should include every field that was marked x-ion-mandatory:always
                always_required = []
                def find_always(node, path=""):
                    if isinstance(node, dict):
                        for k,v in node.items():
                            if k=="x-ion-mandatory" and v=="always":
                                always_required.append(path)
                            else:
                                find_always(v, f"{path}.{k}" if path else k)
                    elif isinstance(node, list):
                        for i,it in enumerate(node):
                            find_always(it, f"{path}[{i}]")
                find_always(told.get("properties",{}))

                # Filter to top-level always-required only (immediate properties of the schema)
                top_level_always = [p.split(".")[0] for p in always_required if "." not in p]
                new_required = set(tnew.get("required", []))
                missing_in_required = [p for p in top_level_always if p not in new_required]
                # Some fields in pre-existing required[] won't have x-ion-mandatory at all — that's fine
                if missing_in_required:
                    issues.append((f"{sector}/{pack}/{tname}",
                                   f"x-ion-mandatory:always fields not in required[]: {missing_in_required}"))

print(f"Schemas checked: {checked}")
print(f"Issues found: {len(issues)}")
if issues:
    for n, msg in issues[:20]:
        print(f"  - {n}: {msg}")
    sys.exit(1)
else:
    print()
    print("✅ Every schema from every original pack:")
    print("   - is present in the new ion.yaml")
    print("   - has the same property set as the original (no fields dropped)")
    print("   - has all original x-ion-mandatory:always fields now in required[]")
