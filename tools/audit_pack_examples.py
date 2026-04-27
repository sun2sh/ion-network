#!/usr/bin/env python3
"""audit_pack_examples.py v2 — Type-aware example audit (see prior).
Pack-content examples ≠ full-payload examples. Different rules each.
"""
import yaml, json, csv
from pathlib import Path
from collections import defaultdict

BECKN = yaml.safe_load(Path("/mnt/project/beckn__1_.yaml").read_text())
SCHEMAS = BECKN["components"]["schemas"]
REPO = Path("/home/claude/ion-network-main-updated")
OUT  = Path("/mnt/user-data/outputs")
BECKN_PROPS = {n: set(s.get("properties",{}).keys())
               for n, s in SCHEMAS.items() if isinstance(s, dict)}
REQUIRED_BY_OBJECT = {"Contract":{"commitments"},"Commitment":{"status","resources","offer"},
                      "Resource":{"id"},"Offer":{"id"},"Consideration":{"id","status"}}

def classify(rel):
    return "pack-content" if "schema/extensions/" in str(rel) and "/examples/" in str(rel) else "full-payload"

def check_obj(obj, t, path, issues, src):
    if not isinstance(obj, dict) or t not in BECKN_PROPS: return
    allowed = BECKN_PROPS[t]; required = REQUIRED_BY_OBJECT.get(t,set())
    keys = set(obj.keys())
    for k in keys - allowed:
        if k.startswith(("@","_")): continue
        issues.append({"file":src,"kind":"UNKNOWN_KEY","object":t,"path":path,"detail":k})
    for k in required - keys:
        issues.append({"file":src,"kind":"MISSING_REQUIRED","object":t,"path":path,"detail":k})

def walk_full(node, path, issues, src):
    if isinstance(node, dict):
        for k,v in node.items():
            sub=f"{path}.{k}"
            if k=="context" and isinstance(v,dict): check_obj(v,"Context",sub,issues,src); walk_full(v,sub,issues,src)
            elif k=="contract" and isinstance(v,dict): check_obj(v,"Contract",sub,issues,src); walk_full(v,sub,issues,src)
            elif k=="commitments" and isinstance(v,list):
                for i,c in enumerate(v):
                    if isinstance(c,dict): check_obj(c,"Commitment",f"{sub}[{i}]",issues,src)
                    walk_full(c,f"{sub}[{i}]",issues,src)
            elif k=="resources" and isinstance(v,list):
                for i,r in enumerate(v):
                    if isinstance(r,dict): check_obj(r,"Resource",f"{sub}[{i}]",issues,src)
                    walk_full(r,f"{sub}[{i}]",issues,src)
            elif k=="offer" and isinstance(v,dict): check_obj(v,"Offer",sub,issues,src); walk_full(v,sub,issues,src)
            elif k=="consideration" and isinstance(v,list):
                for i,c in enumerate(v):
                    if isinstance(c,dict): check_obj(c,"Consideration",f"{sub}[{i}]",issues,src)
                    walk_full(c,f"{sub}[{i}]",issues,src)
            elif k=="settlements" and isinstance(v,list):
                for i,s in enumerate(v):
                    if isinstance(s,dict): check_obj(s,"Settlement",f"{sub}[{i}]",issues,src)
                    walk_full(s,f"{sub}[{i}]",issues,src)
            elif k=="performance" and isinstance(v,list):
                for i,p in enumerate(v):
                    if isinstance(p,dict): check_obj(p,"Performance",f"{sub}[{i}]",issues,src)
                    walk_full(p,f"{sub}[{i}]",issues,src)
            elif k.endswith("Attributes") and isinstance(v,dict):
                if "@context" not in v: issues.append({"file":src,"kind":"ATTRIBUTES_NO_CONTEXT","object":k,"path":sub,"detail":"@context missing"})
                if "@type"    not in v: issues.append({"file":src,"kind":"ATTRIBUTES_NO_TYPE","object":k,"path":sub,"detail":"@type missing"})
            else:
                walk_full(v,sub,issues,src)
    elif isinstance(node, list):
        for i,it in enumerate(node): walk_full(it,f"{path}[{i}]",issues,src)

def check_pack(data, src, issues):
    if not isinstance(data, dict): return
    # Pack examples have either:
    #  - top-level @context + @type (single instance content), OR
    #  - top-level _attachesTo + _comment (showing a list of instances inside a Beckn array slot)
    has_jsonld = ("@context" in data and "@type" in data)
    has_attaches_marker = "_attachesTo" in data
    if not has_jsonld and not has_attaches_marker:
        issues.append({"file":src,"kind":"PACK_EXAMPLE_NO_JSONLD","object":"-","path":"$","detail":"missing both top-level @context/@type and _attachesTo marker"})
    forbidden = {"context":"Beckn message envelope","message":"Beckn message envelope",
                 "contract":"Beckn object","commitments":"Beckn Contract field — pack example should show pack content not contract array",
                 "resources":"Beckn field","performance":"Beckn field","settlements":"Beckn field"}
    # If _attachesTo is present and points to a Beckn array slot (e.g. "Contract.participants[]"),
    # then a wrapper key like "participants" is allowed.
    expected_wrapper = None
    if has_attaches_marker:
        slot = str(data["_attachesTo"])
        m = slot.split(".")
        if len(m) == 2 and m[1].endswith("[]"):
            expected_wrapper = m[1][:-2]
    for k in data:
        if k.startswith("_") or k.startswith("@"): continue
        if k in forbidden:
            if k == expected_wrapper:
                continue   # legitimate wrapper for array-slot pack example
            issues.append({"file":src,"kind":"PACK_EXAMPLE_USES_BECKN_KEY","object":"-","path":"$","detail":f"'{k}': {forbidden[k]}"})

all_issues = []; file_summary = []; cls = defaultdict(int)
for ex in sorted(REPO.rglob("examples/*.json")):
    rel = str(ex.relative_to(REPO))
    try: data = json.loads(ex.read_text())
    except Exception as e:
        all_issues.append({"file":rel,"kind":"PARSE_ERROR","object":"-","path":"-","detail":str(e)[:100]})
        file_summary.append({"file":rel,"issues":1,"kind":"parse-error"}); continue
    k = classify(rel); cls[k] += 1
    issues = []
    if k == "pack-content": check_pack(data, rel, issues)
    else: walk_full(data, rel, issues, rel)
    all_issues.extend(issues)
    file_summary.append({"file":rel,"issues":len(issues),"kind":k})

# Report
report = ["# Examples audit (v2) — pack-content vs full-payload\n"]
report.append(f"- pack-content examples: {cls['pack-content']}")
report.append(f"- full-payload examples: {cls['full-payload']}\n")
report.append("Different rules per kind. pack-content must declare @context/@type and must NOT")
report.append("use Beckn-named wrappers. full-payload must validate as Beckn-shaped.\n\n")
report.append("| File | Type | Issues |\n|---|---|---:|")
total = 0
for f in file_summary:
    total += f["issues"]
    report.append(f"| `{f['file']}` | {f['kind']} | {f['issues']} |")
report.append(f"| **TOTAL** | | **{total}** |\n")
by_file = defaultdict(list)
for i in all_issues: by_file[i["file"]].append(i)
for f, issues in sorted(by_file.items()):
    if not issues: continue
    report.append(f"\n## `{f}` — {len(issues)} issue(s)\n")
    for i in issues[:25]:
        report.append(f"- `{i['kind']}` on `{i['object']}` at `{i['path']}`: {i['detail']}")
(OUT/"audit_pack_examples_report.md").write_text("\n".join(report))
with open(OUT/"audit_pack_examples_detail.csv","w",newline="") as f:
    w = csv.DictWriter(f, fieldnames=["file","kind","object","path","detail"]); w.writeheader()
    for r in all_issues: w.writerow(r)

print(f"Total issues: {total}")
print(f"  pack-content: {cls['pack-content']}, full-payload: {cls['full-payload']}")
print()
for f in sorted(file_summary, key=lambda x:-x["issues"])[:10]:
    print(f"  {f['issues']:3d}  [{f['kind']}]  {f['file']}")
