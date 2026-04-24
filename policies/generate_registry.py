#!/usr/bin/env python3
"""Generate policies/registry.json from per-category YAML terms documents.

Supports two document formats used across the network:
  1. Trade format — one policy per .yaml file, top-level `iri:` field,
     structured fields (displayText, applicableCategories, etc.)
  2. Logistics format — multiple policies per .yaml file separated by
     `---`, top-level `id:` field, shape varies by category.

Output registry.json deduplicates by IRI; entries carry a common minimum
of fields (iri, category, version, status, displayText/description,
docPath) regardless of source format.
"""

import yaml
import json
from pathlib import Path

POLICY_ROOT = Path(__file__).parent
OUTPUT = POLICY_ROOT / "registry.json"

# All policy categories in the merged network — trade + logistics
CATEGORIES = [
    # Trade-originated (some shared with logistics via IRI namespacing)
    "return", "cancellation", "warranty", "dispute",
    "grievance-sla", "payment-terms", "penalty",
    # Logistics-originated (v0.5.2)
    "evidence", "insurance", "sla", "re-attempt",
    "weight-dispute", "liability", "incident",
    "rts-handoff", "logistics-fwa",
]

def iri_for_logistics(doc):
    """Logistics policies use `id:` at top; IRI is ion://policy/{id}."""
    pid = doc.get("id")
    if pid:
        return f"ion://policy/{pid}"
    return None


def normalize_entry(doc, yaml_file):
    """Return a registry entry dict or None if doc can't be parsed."""
    # Trade format: top-level iri
    iri = doc.get("iri")
    if iri:
        return {
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
            "sector": doc.get("sector"),
            "docPath": str(yaml_file.relative_to(POLICY_ROOT.parent)),
            "format": "trade-v1",
        }

    # Logistics format: top-level id, category derived from parent dir
    iri = iri_for_logistics(doc)
    if iri:
        # Derive category from file's parent directory
        # policies/penalty/v1/logistics-penalty-policies.yaml -> PENALTY
        category = yaml_file.parent.parent.name.upper().replace("-", "_")
        return {
            "iri": iri,
            "category": category,
            "subCategory": doc.get("type"),
            "version": "1.0.0",
            "status": "ratified",
            "versionEffectiveFrom": None,
            "displayText": {"en": (doc.get("description") or "").strip()[:160]},
            "shortDesc": (doc.get("description") or "").strip()[:200],
            "applicableCategories": [],
            "applicableResourceTypes": [],
            "regulatoryBasis": [],
            "supersededBy": None,
            "deprecatedAt": None,
            "sector": doc.get("sector"),
            "docPath": str(yaml_file.relative_to(POLICY_ROOT.parent)),
            "format": "logistics-v1",
        }

    return None


def iter_docs(yaml_file):
    """Yield all YAML documents in a file (handles multi-doc YAML)."""
    try:
        for doc in yaml.safe_load_all(yaml_file.read_text(encoding='utf-8')):
            if doc is not None:
                yield doc
    except yaml.YAMLError as e:
        print(f"  YAML error in {yaml_file.name}: {str(e)[:80]}")


def main():
    policies = []
    seen_iris = set()
    errors = []

    for category in CATEGORIES:
        version_dir = POLICY_ROOT / category / "v1"
        if not version_dir.exists():
            continue
        for yaml_file in sorted(version_dir.glob("*.yaml")):
            if yaml_file.name == "_schema.yaml":
                continue
            for doc in iter_docs(yaml_file):
                entry = normalize_entry(doc, yaml_file)
                if entry is None:
                    errors.append(f"{yaml_file.name}: no iri/id")
                    continue
                iri = entry["iri"]
                if iri in seen_iris:
                    errors.append(f"{yaml_file.name}: duplicate iri {iri}")
                    continue
                seen_iris.add(iri)
                policies.append(entry)

    if errors:
        print("Registry build — non-fatal issues:")
        for e in errors:
            print(f"  {e}")

    by_category = {}
    for p in policies:
        c = p.get("category", "UNKNOWN")
        by_category[c] = by_category.get(c, 0) + 1

    registry = {
        "generatedAt": "2026-04-24T00:00:00Z",
        "networkVersion": "0.5.2-draft",
        "totalPolicies": len(policies),
        "byCategory": by_category,
        "policies": policies,
    }

    OUTPUT.write_text(json.dumps(registry, indent=2, ensure_ascii=False))
    print(f"Generated {OUTPUT.relative_to(POLICY_ROOT.parent)} with {len(policies)} policies")

if __name__ == "__main__":
    main()
