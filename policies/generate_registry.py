#!/usr/bin/env python3
"""Generate policies/registry.json from per-category YAML terms documents."""

import yaml
import json
from pathlib import Path

POLICY_ROOT = Path(__file__).parent
OUTPUT = POLICY_ROOT / "registry.json"

CATEGORIES = ["return", "cancellation", "warranty", "dispute",
              "grievance-sla", "payment-terms", "penalty"]

def main():
    policies = []
    seen_iris = set()
    errors = []

    for category in CATEGORIES:
        version_dir = POLICY_ROOT / category / "v1"
        if not version_dir.exists():
            continue
        for yaml_file in sorted(version_dir.glob("*.yaml")):
            try:
                doc = yaml.safe_load(yaml_file.read_text(encoding='utf-8'))
            except yaml.YAMLError as e:
                errors.append(f"{yaml_file}: YAML error - {e}")
                continue

            iri = doc.get("iri")
            if not iri:
                errors.append(f"{yaml_file}: missing iri")
                continue
            if iri in seen_iris:
                errors.append(f"{yaml_file}: duplicate iri {iri}")
                continue
            seen_iris.add(iri)

            policies.append({
                "iri": iri,
                "category": doc.get("category"),
                "subCategory": doc.get("subCategory"),
                "version": doc.get("version", "1.0.0"),
                "status": doc.get("status", "ratified"),
                "versionEffectiveFrom": doc.get("versionEffectiveFrom"),
                "displayText": doc.get("displayText", {}),
                "shortDesc": doc.get("shortDesc"),
                "applicableCategories": doc.get("applicableCategories", []),
                "applicableResourceTypes": doc.get("applicableResourceTypes", []),
                "regulatoryBasis": doc.get("regulatoryBasis", []),
                "supersededBy": doc.get("supersededBy"),
                "deprecatedAt": doc.get("deprecatedAt"),
                "docPath": str(yaml_file.relative_to(POLICY_ROOT.parent)),
            })

    if errors:
        print("Errors:")
        for e in errors:
            print(f"  {e}")

    registry = {
        "generatedAt": "2026-04-21T00:00:00Z",
        "networkVersion": "0.4.0-draft",
        "totalPolicies": len(policies),
        "byCategory": {c: sum(1 for p in policies if p["category"] == c.upper().replace("-","_")) for c in CATEGORIES},
        "policies": policies,
    }

    OUTPUT.write_text(json.dumps(registry, indent=2, ensure_ascii=False))
    print(f"Generated {OUTPUT} with {len(policies)} policies")

if __name__ == "__main__":
    main()
