"""
Audit the JSON payloads in ION_First_Transaction.md against beckn.yaml.

Strategy:
1. Parse the markdown, extract every ```json block.
2. For each JSON block, walk the tree and at each Beckn-named object,
   check that every key is either:
   (a) a Beckn-defined property of that object, OR
   (b) the *Attributes slot of that object (which can carry anything ION-defined), OR
   (c) inside an Attributes bag where additionalProperties: true allows anything.
3. Also flag missing 'required' fields (warning, not error — examples may be partial).
"""
import yaml, json, re
from pathlib import Path

BECKN = yaml.safe_load(Path("/mnt/project/beckn__1_.yaml").read_text())
SCHEMAS = BECKN["components"]["schemas"]
DOC = Path("/mnt/user-data/outputs/ION_First_Transaction.md").read_text()

# Properties allowed on each Beckn object (we hand-derive from the schema)
BECKN_PROPS = {
    "Context": {"domain","location","action","version","bapId","bapUri","bppId","bppUri",
                "transactionId","messageId","networkId","timestamp","key","ttl",
                "schemaContext","requestDigest"},
    "Contract": {"id","descriptor","commitments","consideration","participants",
                 "performance","settlements","status","contractAttributes"},
    "Commitment": {"id","status","resources","offer","commitmentAttributes"},
    "Resource": {"id","descriptor","resourceAttributes"},
    "Offer": {"id","descriptor","provider","resourceIds","addOns","considerations",
              "validity","availableTo","offerAttributes"},
    "Consideration": {"id","status","considerationAttributes"},
    "Settlement": {"id","considerationId","status","settlementAttributes"},
    "Performance": {"id","status","commitmentIds","performanceAttributes"},
    "Participant": {"id","descriptor","participantAttributes"},
    "Address": {"addressCountry","addressLocality","addressRegion","extendedAddress",
                "postalCode","streetAddress"},
}

REQUIRED = {
    "Contract": {"commitments"},
    "Commitment": {"status","resources","offer"},
    "Resource": {"id"},
    "Offer": {"id"},
    "Consideration": {"id","status"},
}

# Find json blocks
blocks = re.findall(r"```json\s*\n(.*?)\n```", DOC, re.DOTALL)
print(f"Found {len(blocks)} JSON blocks in the doc.\n")

issues = []

def check_obj(obj, expected_type, path):
    """obj is a dict expected to conform to Beckn's schema for expected_type."""
    if not isinstance(obj, dict):
        return
    if expected_type not in BECKN_PROPS:
        return
    allowed = BECKN_PROPS[expected_type]
    required = REQUIRED.get(expected_type, set())
    keys = set(obj.keys())
    extra = keys - allowed
    missing = required - keys
    for k in extra:
        issues.append(("UNKNOWN_KEY", expected_type, path, k))
    for k in missing:
        issues.append(("MISSING_REQUIRED", expected_type, path, k))

def walk(node, path="$"):
    if isinstance(node, dict):
        # Heuristic: walk in based on key names
        for k, v in node.items():
            sub = f"{path}.{k}"
            if k == "context" and isinstance(v, dict):
                check_obj(v, "Context", sub)
                walk(v, sub)
            elif k == "contract" and isinstance(v, dict):
                check_obj(v, "Contract", sub)
                walk(v, sub)
            elif k == "commitments" and isinstance(v, list):
                for i, c in enumerate(v):
                    if isinstance(c, dict):
                        check_obj(c, "Commitment", f"{sub}[{i}]")
                    walk(c, f"{sub}[{i}]")
            elif k == "resources" and isinstance(v, list):
                for i, r in enumerate(v):
                    if isinstance(r, dict):
                        check_obj(r, "Resource", f"{sub}[{i}]")
                    walk(r, f"{sub}[{i}]")
            elif k == "offer" and isinstance(v, dict):
                check_obj(v, "Offer", sub)
                walk(v, sub)
            elif k == "consideration" and isinstance(v, list):
                for i, c in enumerate(v):
                    if isinstance(c, dict):
                        check_obj(c, "Consideration", f"{sub}[{i}]")
                    walk(c, f"{sub}[{i}]")
            elif k == "settlements" and isinstance(v, list):
                for i, s in enumerate(v):
                    if isinstance(s, dict):
                        check_obj(s, "Settlement", f"{sub}[{i}]")
                    walk(s, f"{sub}[{i}]")
            elif k == "performance" and isinstance(v, list):
                for i, p in enumerate(v):
                    if isinstance(p, dict):
                        check_obj(p, "Performance", f"{sub}[{i}]")
                    walk(p, f"{sub}[{i}]")
            elif k == "participants" and isinstance(v, list):
                for i, p in enumerate(v):
                    if isinstance(p, dict):
                        check_obj(p, "Participant", f"{sub}[{i}]")
                    walk(p, f"{sub}[{i}]")
            elif k.endswith("Attributes"):
                # Attributes bag: additionalProperties:true. We only check @context/@type present.
                if isinstance(v, dict):
                    if "@context" not in v:
                        issues.append(("ATTRIBUTES_NO_CONTEXT", k, sub, "@context missing"))
                    if "@type" not in v:
                        issues.append(("ATTRIBUTES_NO_TYPE", k, sub, "@type missing"))
                # don't recurse into ION extension content
            else:
                walk(v, sub)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            walk(item, f"{path}[{i}]")

for idx, blk in enumerate(blocks, 1):
    # Strip JS-style line comments only when they appear OUTSIDE strings/URLs.
    # The lookbehind ensures we don't match `://` in URLs.
    cleaned = re.sub(r"(?<=[^:\w])//[^\n]*", "", blk)
    cleaned = re.sub(r"/\*.*?\*/", "null", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r'"/\*[^"]*\*/"\s*:\s*"[^"]*"\s*,?', '', cleaned)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        # Fall back to yaml for unicode-heavy strings
        try:
            data = yaml.safe_load(cleaned)
        except Exception as e2:
            issues.append(("PARSE_ERROR", f"block {idx}", "", str(e)[:80]))
            continue
    walk(data, f"block{idx}")

print(f"{'='*75}")
print(f"AUDIT RESULTS — {len(issues)} issue(s)")
print(f"{'='*75}\n")
for kind, obj, path, detail in issues:
    print(f"[{kind}] on {obj} at {path}")
    print(f"   detail: {detail}\n")
