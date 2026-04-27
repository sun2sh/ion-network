#!/usr/bin/env python3
"""
audit_all_docs.py — Audit every Markdown doc in docs/ against beckn.yaml.

For each .md file, extract every ```json block, parse it, and verify against
beckn.yaml's schema for any Beckn-named object the block references.

Output:
  - audit_all_docs_report.md   — summary
  - audit_all_docs_detail.csv  — every issue, machine-readable
"""
import yaml, json, re, csv
from pathlib import Path
from collections import defaultdict

BECKN = yaml.safe_load(Path("/mnt/project/beckn__1_.yaml").read_text())
SCHEMAS = BECKN["components"]["schemas"]

DOCS_DIR = Path("/home/claude/ion-network-main-updated/docs")
OUT = Path("/mnt/user-data/outputs")

# Beckn ground truth — properties allowed on each Beckn object
BECKN_PROPS = {}
for name, sch in SCHEMAS.items():
    if isinstance(sch, dict) and "properties" in sch:
        BECKN_PROPS[name] = set(sch["properties"].keys())

REQUIRED_BY_OBJECT = {
    "Contract":     {"commitments"},
    "Commitment":   {"status", "resources", "offer"},
    "Resource":     {"id"},
    "Offer":        {"id"},
    "Consideration":{"id", "status"},
}

def check_obj(obj, expected_type, path, issues):
    """Validate one object dict against Beckn schema."""
    if not isinstance(obj, dict): return
    if expected_type not in BECKN_PROPS: return
    allowed = BECKN_PROPS[expected_type]
    required = REQUIRED_BY_OBJECT.get(expected_type, set())
    keys = set(obj.keys())
    extra = keys - allowed
    missing = required - keys
    for k in extra:
        issues.append({"kind": "UNKNOWN_KEY", "object": expected_type, "path": path, "detail": k})
    for k in missing:
        issues.append({"kind": "MISSING_REQUIRED", "object": expected_type, "path": path, "detail": k})

def walk(node, path, issues):
    """Walk a parsed JSON payload, identify Beckn-named objects, validate each."""
    if isinstance(node, dict):
        for k, v in node.items():
            sub = f"{path}.{k}"
            if k == "context" and isinstance(v, dict):
                check_obj(v, "Context", sub, issues); walk(v, sub, issues)
            elif k == "contract" and isinstance(v, dict):
                check_obj(v, "Contract", sub, issues); walk(v, sub, issues)
            elif k == "commitments" and isinstance(v, list):
                for i, c in enumerate(v):
                    if isinstance(c, dict): check_obj(c, "Commitment", f"{sub}[{i}]", issues)
                    walk(c, f"{sub}[{i}]", issues)
            elif k == "resources" and isinstance(v, list):
                for i, r in enumerate(v):
                    if isinstance(r, dict): check_obj(r, "Resource", f"{sub}[{i}]", issues)
                    walk(r, f"{sub}[{i}]", issues)
            elif k == "offer" and isinstance(v, dict):
                check_obj(v, "Offer", sub, issues); walk(v, sub, issues)
            elif k == "consideration" and isinstance(v, list):
                for i, c in enumerate(v):
                    if isinstance(c, dict): check_obj(c, "Consideration", f"{sub}[{i}]", issues)
                    walk(c, f"{sub}[{i}]", issues)
            elif k == "settlements" and isinstance(v, list):
                for i, s in enumerate(v):
                    if isinstance(s, dict): check_obj(s, "Settlement", f"{sub}[{i}]", issues)
                    walk(s, f"{sub}[{i}]", issues)
            elif k == "performance" and isinstance(v, list):
                for i, p in enumerate(v):
                    if isinstance(p, dict): check_obj(p, "Performance", f"{sub}[{i}]", issues)
                    walk(p, f"{sub}[{i}]", issues)
            elif k == "participants" and isinstance(v, list):
                for i, p in enumerate(v):
                    if isinstance(p, dict): check_obj(p, "Participant", f"{sub}[{i}]", issues)
                    walk(p, f"{sub}[{i}]", issues)
            elif k.endswith("Attributes") and isinstance(v, dict):
                # Attributes bags must have @context and @type
                if "@context" not in v:
                    issues.append({"kind": "ATTRIBUTES_NO_CONTEXT", "object": k, "path": sub, "detail": "@context missing"})
                if "@type" not in v:
                    issues.append({"kind": "ATTRIBUTES_NO_TYPE", "object": k, "path": sub, "detail": "@type missing"})
            else:
                walk(v, sub, issues)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            walk(item, f"{path}[{i}]", issues)

# ============================================================
# Audit each doc
# ============================================================
all_issues_csv = []
per_doc_summary = []

for doc_path in sorted(DOCS_DIR.glob("*.md")):
    doc_text = doc_path.read_text()
    blocks = re.findall(r"```json\s*\n(.*?)\n```", doc_text, re.DOTALL)
    issues = []
    parse_errors = 0
    for idx, blk in enumerate(blocks, 1):
        # Strip JS-style comments outside URLs
        cleaned = re.sub(r"(?<=[^:\w])//[^\n]*", "", blk)
        cleaned = re.sub(r"/\*.*?\*/", "null", cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'"/\*[^"]*\*/"\s*:\s*"[^"]*"\s*,?', '', cleaned)
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            try:
                data = yaml.safe_load(cleaned)
                if not isinstance(data, (dict, list)): continue
            except Exception:
                parse_errors += 1
                continue
        walk(data, f"{doc_path.name}:block{idx}", issues)

    # Summarise by issue kind
    kinds = defaultdict(int)
    for i in issues:
        kinds[i["kind"]] += 1
        i["doc"] = doc_path.name
        all_issues_csv.append(i)

    per_doc_summary.append({
        "doc": doc_path.name,
        "json_blocks": len(blocks),
        "parse_errors": parse_errors,
        "issues_total": len(issues),
        "by_kind": dict(kinds),
    })

# Write outputs
report = ["# Doc audit report — every doc in docs/ vs beckn.yaml\n"]
report.append("Each doc's JSON blocks were parsed and every Beckn-named object inside them ")
report.append("was validated against `beckn.yaml`'s schema. Two checks per object:")
report.append("- Every key on the object is one Beckn defines for that type")
report.append("- Every Beckn-required property is present\n")
report.append("Plus a check on `*Attributes` bags (must have `@context` and `@type`).\n\n")

# Header table
report.append("| Doc | JSON blocks | Parse errors | Issues |")
report.append("|---|---:|---:|---:|")
total_blocks = 0; total_parse_err = 0; total_issues = 0
for s in per_doc_summary:
    total_blocks += s["json_blocks"]
    total_parse_err += s["parse_errors"]
    total_issues += s["issues_total"]
    report.append(f"| `{s['doc']}` | {s['json_blocks']} | {s['parse_errors']} | {s['issues_total']} |")
report.append(f"| **TOTAL** | **{total_blocks}** | **{total_parse_err}** | **{total_issues}** |\n\n")

# Per-doc detail
for s in per_doc_summary:
    if s["issues_total"] == 0 and s["parse_errors"] == 0:
        continue
    report.append(f"\n## `{s['doc']}` — {s['issues_total']} issue(s) across {s['json_blocks']} JSON block(s)\n")
    if s["by_kind"]:
        report.append("Issue kinds:")
        for kind, n in sorted(s["by_kind"].items(), key=lambda x: -x[1]):
            report.append(f"- {kind}: {n}")
    # Specific issues for this doc
    issues_for_this_doc = [i for i in all_issues_csv if i["doc"] == s["doc"]]
    if issues_for_this_doc:
        report.append("\nFirst 15 specific issues:")
        for i in issues_for_this_doc[:15]:
            report.append(f"- `{i['kind']}` on `{i['object']}` at `{i['path']}`: {i['detail']}")
        if len(issues_for_this_doc) > 15:
            report.append(f"- ... and {len(issues_for_this_doc)-15} more (see CSV)")

# CSV
csv_path = OUT / "audit_all_docs_detail.csv"
with open(csv_path, "w", newline="") as f:
    if all_issues_csv:
        w = csv.DictWriter(f, fieldnames=["doc","kind","object","path","detail"])
        w.writeheader()
        for r in all_issues_csv: w.writerow(r)
    else:
        f.write("doc,kind,object,path,detail\n")

# Markdown report
report_path = OUT / "audit_all_docs_report.md"
report_path.write_text("\n".join(report))

print(f"Docs audited: {len(per_doc_summary)}")
print(f"Total JSON blocks: {total_blocks}")
print(f"Total parse errors: {total_parse_err}")
print(f"Total Beckn-shape issues: {total_issues}")
print()
print(f"Wrote {report_path}")
print(f"Wrote {csv_path}")
print()
# Top offenders
top = sorted(per_doc_summary, key=lambda s: -s["issues_total"])[:5]
print("Top 5 docs by issue count:")
for s in top:
    print(f"  {s['doc']}: {s['issues_total']} issues, {s['parse_errors']} parse errors")
