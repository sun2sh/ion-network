#!/usr/bin/env python3
"""
ION Composed Spec Generator — tools/generate_composed.py

Merges Beckn Protocol core (beckn.yaml) with all ION extension packs into
a single OpenAPI 3.1.1 file: ion-with-beckn.yaml

The output file is the canonical validator for implementers. Running a standard
OpenAPI validator against ion-with-beckn.yaml checks BOTH Beckn core conformance
AND ION field-level correctness in a single pass — eliminating the need to chain
two validators.

USAGE:
    python3 tools/generate_composed.py [--beckn <path>]

    --beckn   Path to beckn.yaml (default: looks for it in project root)

REGENERATE WHEN:
    - Any ION schema pack (schema/extensions/*/v1/attributes.yaml) is updated
    - beckn.yaml is updated to a new version
    - PACK_MAP is changed (new attachment points)

OUTPUT:
    schema/core/v2/api/v2.0.0/ion-with-beckn.yaml
"""

import sys
import argparse
from pathlib import Path
from copy import deepcopy

try:
    import yaml
except ModuleNotFoundError:
    print("ERROR: PyYAML is not installed.")
    print("")
    print("Fix it in one line:")
    print("  pip install pyyaml")
    print("")
    print("Then re-run: python tools/generate_composed.py")
    sys.exit(1)

ROOT = Path(__file__).parent.parent

# Maps Beckn *Attributes slot → [(ION schema name, pack path)]
# Order within each list matters for oneOf presentation; put primary schema first.
#
# Expanded in v0.5.2:
#   - core/participant/v1 added for participantAttributes
#   - All 10 logistics packs attached to their respective slots
#   - trackingAttributes slot activated (logistics tracking pack)
#   - participantAttributes carries both core + logistics addendum
PACK_MAP = {
    "resourceAttributes": [
        ("TradeResourceAttributes",       "trade/resource/v1"),
        ("LogisticsResourceAttributes",   "logistics/resource/v1"),
        ("ProductCertifications",         "core/product/v1"),
    ],
    "offerAttributes": [
        ("TradeOfferAttributes",          "trade/offer/v1"),
        ("LogisticsOfferAttributes",      "logistics/offer/v1"),
    ],
    "providerAttributes": [
        ("TradeProviderAttributes",       "trade/provider/v1"),
        ("LogisticsProviderAttributes",   "logistics/provider/v1"),
    ],
    "commitmentAttributes": [
        ("TradeCommitmentAttributes",     "trade/commitment/v1"),
        ("LogisticsCommitmentAttributes", "logistics/commitment/v1"),
        ("IONBusinessIdentity",           "core/identity/v1"),
    ],
    "considerationAttributes": [
        ("TradeConsiderationAttributes",  "trade/consideration/v1"),
        ("LogisticsConsiderationAttributes", "logistics/consideration/v1"),
    ],
    "performanceAttributes": [
        ("TradePerformanceAttributes",    "trade/performance/v1"),
        ("LogisticsPerformanceAttributes","logistics/performance/v1"),
    ],
    "contractAttributes": [
        ("TradeContractAttributes",       "trade/contract/v1"),
        ("LogisticsContractAttributes",   "logistics/contract/v1"),
        ("IONTaxDetail",                  "core/tax/v1"),
    ],
    "settlementAttributes": [
        ("PaymentDeclaration",            "core/payment/v1"),
        ("IONReconcileAttributes",        "core/reconcile/v1"),
    ],
    "participantAttributes": [
        ("IONParticipantAttributes",      "core/participant/v1"),
        ("LogisticsParticipantAddendum",  "logistics/participant-logistics/v1"),
    ],
    "trackingAttributes": [
        ("LogisticsTrackingAttributes",   "logistics/tracking/v1"),
    ],
}

# Beckn schemas that carry *Attributes slots → which slots they carry
BECKN_SCHEMA_SLOTS = {
    "Resource":      ["resourceAttributes"],
    "Offer":         ["offerAttributes"],
    "Provider":      ["providerAttributes"],
    "Commitment":    ["commitmentAttributes"],
    "Consideration": ["considerationAttributes"],
    "Performance":   ["performanceAttributes"],
    "Contract":      ["contractAttributes"],
    "Settlement":    ["settlementAttributes"],
    "Participant":   ["participantAttributes"],
    "Tracking":      ["trackingAttributes"],
}


def find_beckn(cli_path=None):
    candidates = [
        cli_path,
        ROOT / "beckn.yaml",
        ROOT / "beckn__1_.yaml",
        Path("/mnt/project/beckn__1_.yaml"),
    ]
    for c in candidates:
        if c and Path(c).exists():
            return Path(c)
    raise FileNotFoundError("beckn.yaml not found. Pass --beckn <path>")


def load_ion_schemas():
    """Load all ION extension pack schemas, keyed by schema name."""
    all_schemas = {}
    for pack_file in sorted((ROOT / "schema" / "extensions").rglob("attributes.yaml")):
        data = yaml.safe_load(pack_file.read_text(encoding='utf-8'))
        for name, schema in data.get("components", {}).get("schemas", {}).items():
            all_schemas[name] = schema
    return all_schemas


def load_ion_profile():
    """Load ION network profile extensions."""
    ion_yaml = ROOT / "schema" / "core" / "v2" / "api" / "v2.0.0" / "ion.yaml"
    data = yaml.safe_load(ion_yaml.read_text(encoding='utf-8'))
    return {k: v for k, v in data.items() if k.startswith("x-ion-")}


def compose(beckn_path):
    beckn = yaml.safe_load(Path(beckn_path).read_text(encoding='utf-8'))
    ion_schemas = load_ion_schemas()
    ion_profile = load_ion_profile()

    composed = deepcopy(beckn)

    # Update info block
    composed["info"]["title"] = "ION Indonesia Open Network — Composed Specification"
    bv = beckn["info"]["version"]
    composed["info"]["description"] = (
        f"Composed OpenAPI 3.1.1: Beckn Protocol v{bv} core + ION extension packs.\n\n"
        "Each Beckn *Attributes slot is replaced with a discriminated union of the\n"
        "relevant ION schemas. A single validator run confirms both Beckn conformance\n"
        "and ION field correctness simultaneously.\n\n"
        "Generated by tools/generate_composed.py — do not edit manually.\n"
        f"  Beckn core: v{bv}  |  ION profile: v0.5.1-draft"
    )

    # Inject ION schemas with ION_ prefix to avoid name collisions
    for name, schema in ion_schemas.items():
        composed["components"]["schemas"][f"ION_{name}"] = schema

    # Inject ION profile extensions at root
    composed.update(ion_profile)

    # Replace *Attributes slots in Beckn schemas with ION discriminated unions
    for beckn_schema_name, slots in BECKN_SCHEMA_SLOTS.items():
        schema = composed["components"]["schemas"].get(beckn_schema_name)
        if not schema:
            continue
        for slot in slots:
            if slot not in schema.get("properties", {}):
                continue
            ion_options = PACK_MAP.get(slot, [])
            if not ion_options:
                continue

            valid_options = [
                (sn, pp) for sn, pp in ion_options
                if f"ION_{sn}" in composed["components"]["schemas"]
            ]
            if not valid_options:
                continue

            one_of_refs = [
                {"$ref": f"#/components/schemas/ION_{sn}"}
                for sn, _ in valid_options
            ]

            if len(valid_options) == 1:
                sn = valid_options[0][0]
                schema["properties"][slot] = {
                    "allOf": [
                        {"$ref": "#/components/schemas/Attributes"},
                        {"$ref": f"#/components/schemas/ION_{sn}"},
                    ],
                    "description": (
                        f"ION extension for {beckn_schema_name}.{slot}. "
                        f"Must carry JSON-LD @context and @type. "
                        f"Schema: ION_{sn}."
                    ),
                }
            else:
                # Discriminate on @type
                all_of = [{"$ref": "#/components/schemas/Attributes"}]
                for ref_obj, (sn, _) in zip(one_of_refs, valid_options):
                    ion_s = ion_schemas.get(sn, {})
                    at_type = ion_s.get("x-jsonld", {}).get("@type", f"ion:{sn}")
                    all_of.append({
                        "if": {
                            "properties": {"@type": {"const": at_type}},
                            "required": ["@type"],
                        },
                        "then": ref_obj,
                    })
                schema["properties"][slot] = {
                    "allOf": all_of,
                    "description": (
                        f"ION extension for {beckn_schema_name}.{slot}. "
                        f"@type discriminator selects schema: "
                        + ", ".join(f"{sn}" for sn, _ in valid_options)
                        + "."
                    ),
                }

    return composed


def main():
    parser = argparse.ArgumentParser(description="Generate ion-with-beckn.yaml")
    parser.add_argument("--beckn", default=None, help="Path to beckn.yaml")
    args = parser.parse_args()

    beckn_path = find_beckn(args.beckn)
    print(f"Beckn source: {beckn_path}")

    composed = compose(beckn_path)

    out = ROOT / "schema" / "core" / "v2" / "api" / "v2.0.0" / "ion-with-beckn.yaml"
    out.write_text(
        yaml.dump(composed, default_flow_style=False, allow_unicode=True,
                  sort_keys=False, width=120),
        encoding='utf-8'
    )

    # Verify
    yaml.safe_load(out.read_text(encoding='utf-8'))

    schemas_n = len(composed["components"]["schemas"])
    paths_n = len(composed.get("paths", {}))
    size_kb = out.stat().st_size // 1024
    print(f"Written: {out.relative_to(ROOT)}")
    print(f"  Schemas: {schemas_n} ({schemas_n - 69} ION + 69 Beckn core)")
    print(f"  Paths:   {paths_n}")
    print(f"  Size:    {size_kb} KB")
    print("  YAML:    valid")
    print("Done.")


if __name__ == "__main__":
    main()
