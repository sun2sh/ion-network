#!/usr/bin/env python3
"""
fix_flow_examples.py — Surgically add Beckn-required fields to flow example
                        JSON files. Walks every Commitment and Consideration in
                        full-payload examples and fills in missing offer/
                        resources/status with sensible placeholder values that
                        preserve the example's narrative.

The fixes are conservative — we add ONLY missing required fields, never modify
existing fields. So existing data stays intact.
"""
import json, csv
from pathlib import Path

REPO = Path("/home/claude/ion-network-main-updated")

# Read the audit detail to know exactly which files need what
issues = list(csv.DictReader(open("/mnt/user-data/outputs/audit_pack_examples_detail.csv")))
files_with_issues = sorted(set(i["file"] for i in issues if i["kind"] == "MISSING_REQUIRED"))

print(f"Fixing {len(files_with_issues)} flow example files...")

def fix_commitments(commitments_list, context_path):
    """For each commitment dict, add status/resources/offer if missing."""
    changes = 0
    for i, c in enumerate(commitments_list):
        if not isinstance(c, dict): continue
        if "status" not in c:
            c["status"] = {
                "descriptor": {"code": "ACTIVE", "shortDesc": "Commitment active"}
            }
            changes += 1
        if "resources" not in c:
            attrs = c.get("commitmentAttributes", {}) or {}
            sku = attrs.get("skuId") or attrs.get("resourceId") or attrs.get("lineId") or f"res-{i+1:03d}"
            qty = attrs.get("quantity")
            res = {"id": str(sku)}
            # Beckn Resource has NO top-level quantity field — quantity goes inside
            # resourceAttributes per ION's trade/resource pack. Build it that way.
            if qty is not None:
                res["resourceAttributes"] = {
                    "@context": "https://schema.ion.id/extensions/trade/resource/v1/context.jsonld",
                    "@type": "ion:TradeResourceAttributes",
                    "quantity": {"count": qty} if not isinstance(qty, dict) else qty,
                }
            c["resources"] = [res]
            changes += 1
        if "offer" not in c:
            attrs = c.get("commitmentAttributes", {}) or {}
            offer_id = attrs.get("offerId") or f"off-{i+1:03d}"
            c["offer"] = {"id": str(offer_id)}
            changes += 1
    return changes

def fix_considerations(consideration_list):
    """For each consideration dict, add status if missing."""
    changes = 0
    for c in consideration_list:
        if not isinstance(c, dict): continue
        if "status" not in c:
            c["status"] = {
                "descriptor": {"code": "QUOTED", "shortDesc": "Consideration quoted"}
            }
            changes += 1
    return changes

total_changes = 0
for rel in files_with_issues:
    fp = REPO / rel
    if not fp.exists():
        print(f"  ✗ {rel} not found")
        continue
    data = json.loads(fp.read_text())
    file_changes = 0
    # Walk the message.contract.commitments and consideration
    contract = data.get("message", {}).get("contract") if isinstance(data, dict) else None
    if isinstance(contract, dict):
        if isinstance(contract.get("commitments"), list):
            file_changes += fix_commitments(contract["commitments"], "message.contract.commitments")
        cons = contract.get("consideration")
        if isinstance(cons, list):
            file_changes += fix_considerations(cons)
        elif isinstance(cons, dict):
            # Single object — promote to list (correct Beckn shape) and fix
            file_changes += fix_considerations([cons])
            contract["consideration"] = [cons]
    # Also handle responses where top is a list of contracts (defensive)
    if isinstance(data, dict) and isinstance(data.get("contracts"), list):
        for c in data["contracts"]:
            if isinstance(c, dict) and isinstance(c.get("commitments"), list):
                file_changes += fix_commitments(c["commitments"], "")
    if file_changes:
        fp.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        print(f"  ✓ {rel}: {file_changes} fields added")
        total_changes += file_changes

print(f"\nTotal fields added: {total_changes}")
