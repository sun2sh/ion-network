#!/usr/bin/env python3
"""
fix_resource_quantity_and_stops.py — Move misplaced fields into proper
Attributes bags:
  - Resource.quantity   →  Resource.resourceAttributes.quantity
  - Performance.stops   →  Performance.performanceAttributes.stops

Walks every full-payload example and fixes systematically.
"""
import json
from pathlib import Path

REPO = Path("/home/claude/ion-network-main-updated")

RESOURCE_CTX = "https://schema.ion.id/extensions/trade/resource/v1/context.jsonld"
RESOURCE_TYPE = "ion:TradeResourceAttributes"
LOG_RESOURCE_CTX = "https://schema.ion.id/extensions/logistics/resource/v1/context.jsonld"
LOG_RESOURCE_TYPE = "ion:LogisticsResourceAttributes"
PERF_CTX = "https://schema.ion.id/extensions/logistics/performance/v1/context.jsonld"
PERF_TYPE = "ion:LogisticsPerformanceAttributes"

def is_logistics(rel):
    return "logistics" in rel.lower()

def fix_resource(r, rel):
    """If Resource has top-level quantity, move it into resourceAttributes."""
    if not isinstance(r, dict): return 0
    if "quantity" not in r: return 0
    qty = r.pop("quantity")
    attrs = r.get("resourceAttributes")
    if not isinstance(attrs, dict):
        attrs = {
            "@context": LOG_RESOURCE_CTX if is_logistics(rel) else RESOURCE_CTX,
            "@type":    LOG_RESOURCE_TYPE if is_logistics(rel) else RESOURCE_TYPE,
        }
        r["resourceAttributes"] = attrs
    attrs.setdefault("quantity", qty)
    return 1

def fix_performance(p, rel):
    """If Performance has top-level stops, move it into performanceAttributes."""
    if not isinstance(p, dict): return 0
    if "stops" not in p: return 0
    stops = p.pop("stops")
    attrs = p.get("performanceAttributes")
    if not isinstance(attrs, dict):
        attrs = {
            "@context": PERF_CTX,
            "@type": PERF_TYPE,
        }
        p["performanceAttributes"] = attrs
    attrs.setdefault("stops", stops)
    return 1

def walk(node, rel, changes):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "resources" and isinstance(v, list):
                for r in v:
                    changes[0] += fix_resource(r, rel)
                    walk(r, rel, changes)
            elif k == "performance" and isinstance(v, list):
                for p in v:
                    changes[0] += fix_performance(p, rel)
                    walk(p, rel, changes)
            else:
                walk(v, rel, changes)
    elif isinstance(node, list):
        for it in node: walk(it, rel, changes)

total = 0
for ex in sorted(REPO.rglob("examples/*.json")):
    rel = str(ex.relative_to(REPO))
    if "schema/extensions/" in rel: continue   # pack-content, skip
    try: data = json.loads(ex.read_text())
    except Exception: continue
    changes = [0]
    walk(data, rel, changes)
    if changes[0]:
        ex.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        print(f"  ✓ {rel}: {changes[0]} field(s) relocated")
        total += changes[0]

print(f"\nTotal fields relocated: {total}")
