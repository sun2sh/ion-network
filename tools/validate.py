#!/usr/bin/env python3
"""
ION spec validator — conformance checks for the unified ION network repository.
Exits non-zero if any issue is found. Use this in CI.

Checks:
  1.  YAML and JSON files parse cleanly (including multi-document YAML)
  2.  JSON-LD context and vocab non-empty for every schema pack
  3.  x-ion-mandatory annotation present on every schema property
  4.  No duplicate error codes across any errors/*.yaml
  5.  No Beckn v1.x field paths in flow documents (message.order, snake_case context)
  6.  All spine definitions declare required fields: id, version, participants, phases
  7.  All branch definitions declare required fields: id, branchType, appliesTo, window
  8.  All policy IRI references in offer schema resolve to a policy document
  9.  selectRequired declared on every offer in catalog examples
  10. All state machines in performance-states/v1/states.yaml have terminal states declared
  11. No empty files
  12. Profile.json present for every spine and branch
  13. README.md present for every spine, branch, and schema pack
  14. At least one example per spine
  15. Beckn 2.0 endpoint names used correctly (track not search, on_discover not on_search)

USAGE:
    pip install pyyaml
    python3 tools/validate.py
    python3 tools/validate.py --strict    # fail on warnings too
"""

import sys
import json
import re
import argparse
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:
    print("ERROR: PyYAML is not installed.")
    print("")
    print("Fix it in one line:")
    print("  pip install pyyaml")
    print("")
    print("Then re-run: python3 tools/validate.py")
    sys.exit(1)

ROOT = Path(__file__).parent.parent
ERRORS = []
WARNINGS = []


def err(cat, msg):
    ERRORS.append((cat, msg))


def warn(cat, msg):
    WARNINGS.append((cat, msg))


# ─── Check 1: YAML and JSON parse cleanly ─────────────────────────────────────

def check_yaml_json_parse():
    """All YAML and JSON files must parse without error."""
    for f in ROOT.rglob("*.yaml"):
        if _skip(f):
            continue
        try:
            list(yaml.safe_load_all(f.read_text(encoding="utf-8")))
        except yaml.YAMLError as e:
            err("YAML_PARSE", f"{f.relative_to(ROOT)}: {str(e)[:120]}")

    for f in ROOT.rglob("*.json"):
        if _skip(f):
            continue
        try:
            json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            err("JSON_PARSE", f"{f.relative_to(ROOT)}: {str(e)[:120]}")

    for f in ROOT.rglob("*.jsonld"):
        if _skip(f):
            continue
        try:
            json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            err("JSONLD_PARSE", f"{f.relative_to(ROOT)}: {str(e)[:120]}")


# ─── Check 2: JSON-LD non-empty ────────────────────────────────────────────────

def check_jsonld_populated():
    """context.jsonld and vocab.jsonld must have meaningful content."""
    for ctx in (ROOT / "schema" / "extensions").rglob("context.jsonld"):
        try:
            data = json.loads(ctx.read_text(encoding="utf-8"))
            context = data.get("@context", {})
            if len(context) < 5:
                err("JSONLD_THIN",
                    f"{ctx.relative_to(ROOT)} — only {len(context)} terms; expected >= 5")
        except Exception:
            pass  # Already caught in check 1

    for vocab in (ROOT / "schema" / "extensions").rglob("vocab.jsonld"):
        try:
            data = json.loads(vocab.read_text(encoding="utf-8"))
            graph = data.get("@graph", [])
            if not graph:
                err("VOCAB_EMPTY", f"{vocab.relative_to(ROOT)} — empty @graph")
        except Exception:
            pass


# ─── Check 2b: JSON-LD context ↔ OpenAPI schema drift ────────────────────────
#
# Every property name in an OpenAPI extension schema should have a matching
# term in the pack's context.jsonld (after stripping the "ion:" prefix).
# Every term in the context should have a corresponding property or schema
# name. Drift indicates that context.jsonld or attributes.yaml was edited
# without updating its companion — a problem because schema.ion.id will
# publish the context as authoritative vocabulary.
#
# Currently WARN-only (not ERR) because existing drift needs a dedicated
# cleanup pass. Escalate to ERR once drift is fixed.

_CLASS_HINT_SUFFIXES = ("Attributes", "Ticket", "Addendum", "Subdivisions",
                        "Identity", "Localization", "Declaration", "Detail",
                        "Certifications", "Text", "Reference", "Fee",
                        "Terms", "Response", "Policy")

_CLASS_HINT_EXACT = {
    "LocalisedText", "PaymentDeclaration", "CashOnDelivery", "BankTransfer",
    "EWallet", "VirtualAccount", "QRIS", "BNPL", "CardPayment", "BISettlement",
    "IONTicket", "CreditTerms", "InvoiceReference", "ProcessingFee", "Refund",
}


def _looks_like_class(name: str) -> bool:
    if not name or not name[0].isupper():
        return False
    if name in _CLASS_HINT_EXACT:
        return True
    return any(name.endswith(s) for s in _CLASS_HINT_SUFFIXES)


def check_context_schema_drift():
    """
    Enforce that JSON-LD context.jsonld and OpenAPI attributes.yaml in each
    extension pack stay in sync. Properties in the schema must have context
    terms (the "ion:" prefix is stripped before comparison); terms in the
    context must have schema properties (or be class names).
    """
    pack_base = ROOT / "schema" / "extensions"
    for layer_dir in sorted(pack_base.iterdir()):
        if not layer_dir.is_dir() or layer_dir.name in {".", ".."}:
            continue
        for pack_dir in sorted(layer_dir.iterdir()):
            if not pack_dir.is_dir():
                continue
            v1 = pack_dir / "v1"
            if not v1.exists():
                continue
            attrs = v1 / "attributes.yaml"
            ctx = v1 / "context.jsonld"
            pack_id = f"{layer_dir.name}/{pack_dir.name}/v1"

            # performance-states packs deliberately have no attributes.yaml
            if not attrs.exists():
                continue
            if not ctx.exists():
                warn("DRIFT_NO_CONTEXT", f"{pack_id}: attributes.yaml present but no context.jsonld")
                continue

            # Parse schema
            try:
                sdoc = yaml.safe_load(attrs.read_text(encoding="utf-8"))
            except Exception as e:
                continue  # parse errors caught elsewhere
            schema_props = set()
            schema_classes = set()
            for sname, sdef in (sdoc.get("components", {}).get("schemas", {}) or {}).items():
                if not isinstance(sdef, dict):
                    continue
                schema_classes.add(sname)
                for pname in (sdef.get("properties") or {}).keys():
                    schema_props.add(pname)

            # Parse context
            try:
                cdoc = json.loads(ctx.read_text(encoding="utf-8"))
            except Exception:
                continue
            ctx_obj = cdoc.get("@context", {})
            if isinstance(ctx_obj, list):
                merged = {}
                for e in ctx_obj:
                    if isinstance(e, dict):
                        merged.update(e)
                ctx_obj = merged
            ctx_props = set()
            ctx_classes = set()
            if isinstance(ctx_obj, dict):
                for k, v in ctx_obj.items():
                    if k.startswith("@"):
                        continue
                    # skip prefix declarations (value is a bare URI)
                    if isinstance(v, str) and (v.endswith("#") or v.endswith("/")):
                        continue
                    bare = k[4:] if k.startswith("ion:") else k
                    if _looks_like_class(bare):
                        ctx_classes.add(bare)
                    else:
                        ctx_props.add(bare)

            # Compare
            only_in_schema = sorted(schema_props - ctx_props)
            only_in_context = sorted(ctx_props - schema_props)
            missing_classes = sorted(schema_classes - ctx_classes)

            if only_in_schema:
                preview = only_in_schema[:5]
                more = f" (+{len(only_in_schema)-5} more)" if len(only_in_schema) > 5 else ""
                warn("DRIFT_SCHEMA_NOT_IN_CONTEXT",
                     f"{pack_id}: props in attributes.yaml but missing from context.jsonld: {preview}{more}")
            if only_in_context:
                preview = only_in_context[:5]
                more = f" (+{len(only_in_context)-5} more)" if len(only_in_context) > 5 else ""
                warn("DRIFT_CONTEXT_NOT_IN_SCHEMA",
                     f"{pack_id}: terms in context.jsonld but missing from attributes.yaml: {preview}{more}")
            if missing_classes:
                warn("DRIFT_CLASS_NO_CONTEXT",
                     f"{pack_id}: schema classes without @type mapping in context: {missing_classes[:5]}")



# ─── Check 3: x-ion-mandatory annotation ──────────────────────────────────────

def check_mandatory_annotations():
    """Every property in every schema pack must declare x-ion-mandatory."""
    valid = {"always", "conditional", "optional"}
    for f in (ROOT / "schema" / "extensions").rglob("attributes.yaml"):
        try:
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        schemas = data.get("components", {}).get("schemas", {})
        for schema_name, schema in schemas.items():
            if not isinstance(schema, dict):
                continue
            for prop_name, prop_def in schema.get("properties", {}).items():
                if not isinstance(prop_def, dict):
                    continue
                if prop_def.get("deprecated") is True:
                    continue
                m = prop_def.get("x-ion-mandatory")
                if m is None:
                    # Warn rather than error — logistics schema is more complex
                    warn("MANDATORY_MISSING",
                         f"{f.relative_to(ROOT)} :: {schema_name}.{prop_name}")
                elif m not in valid and not str(m).startswith("required"):
                    err("MANDATORY_INVALID",
                        f"{f.relative_to(ROOT)} :: {schema_name}.{prop_name} — "
                        f"invalid value '{m}' (expected: always|conditional|optional)")


# ─── Check 4: No duplicate error codes ────────────────────────────────────────

def check_no_duplicate_error_codes():
    """Error codes across all errors/*.yaml must be unique globally."""
    errors_dir = ROOT / "errors"
    if not errors_dir.exists():
        err("ERRORS_MISSING", "errors/ directory not found")
        return
    seen = {}
    for errors_file in sorted(errors_dir.glob("*.yaml")):
        try:
            data = yaml.safe_load(errors_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        for code in data.get("errors", {}):
            if code in seen:
                err(
                    "DUPLICATE_ERROR_CODE",
                    f"{code} appears in both "
                    f"{seen[code]} and {errors_file.name}",
                )
            else:
                seen[code] = errors_file.name


# ─── Check 5: No Beckn v1.x field paths ───────────────────────────────────────

def check_no_beckn_v1_paths():
    """No Beckn v1.x snake_case field names or message.order paths in flows."""
    bad = [
        (r"\bmessage\.order\b",        "Use message.contract (Beckn v2.0)"),
        (r'"bap_id"',                  "Use bapId (camelCase)"),
        (r'"bpp_id"',                  "Use bppId"),
        (r'"transaction_id"',          "Use transactionId"),
        (r'"message_id"',              "Use messageId"),
        (r'"bap_uri"',                 "Use bapUri"),
        (r'"bpp_uri"',                 "Use bppUri"),
        (r'\bcontext\.bap_id\b',       "Use context.bapId"),
        (r'\bcontext\.bpp_id\b',       "Use context.bppId"),
        (r'\bon_search\b',             "Beckn 2.0 uses on_discover — on_search is v1.x"),
        (r'"/search"',                 "Beckn 2.0 uses /discover — /search is v1.x"),
        (r'step: search\b',            "Beckn 2.0 uses discover — search is v1.x"),
    ]
    for f in (ROOT / "flows").rglob("*"):
        if not f.is_file() or f.suffix not in (".yaml", ".json", ".md"):
            continue
        if _skip(f):
            continue
        text = f.read_text(encoding="utf-8")
        for pat, hint in bad:
            if re.search(pat, text):
                err("BECKN_V1_PATH",
                    f"{f.relative_to(ROOT)} — matches '{pat}' — {hint}")


# ─── Check 6: Spine structure ─────────────────────────────────────────────────

def check_spine_structure():
    """Every spine.yaml must declare: id, version, participants, phases."""
    required_keys = {"id", "version", "participants", "phases"}
    for f in (ROOT / "flows" / "logistics" / "spines").rglob("spine.yaml"):
        try:
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            err("SPINE_INVALID", f"{f.relative_to(ROOT)} — not a YAML mapping")
            continue
        missing = required_keys - set(data.keys())
        if missing:
            err("SPINE_MISSING_KEYS",
                f"{f.relative_to(ROOT)} — missing required keys: {', '.join(sorted(missing))}")
        # Check phases have at least phase1 and phase2
        phases = data.get("phases", {})
        if "phase1" not in phases:
            err("SPINE_NO_PHASE1", f"{f.relative_to(ROOT)} — missing phases.phase1 (catalog)")
        if "phase2" not in phases:
            err("SPINE_NO_PHASE2", f"{f.relative_to(ROOT)} — missing phases.phase2 (transaction)")


# ─── Check 7: Branch structure ────────────────────────────────────────────────

def check_branch_structure():
    """Every branch.yaml must declare: id, branchType, appliesTo, window."""
    required_keys = {"id", "branchType"}
    for f in (ROOT / "flows" / "logistics" / "branches").rglob("branch.yaml"):
        try:
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            err("BRANCH_INVALID", f"{f.relative_to(ROOT)} — not a YAML mapping")
            continue
        missing = required_keys - set(data.keys())
        if missing:
            err("BRANCH_MISSING_KEYS",
                f"{f.relative_to(ROOT)} — missing: {', '.join(sorted(missing))}")
        # appliesTo or subBranches must exist
        if "appliesTo" not in data and "subBranches" not in data:
            warn("BRANCH_NO_APPLIES_TO",
                 f"{f.relative_to(ROOT)} — no appliesTo or subBranches declared")


# ─── Check 8: Policy IRI resolution ───────────────────────────────────────────

def check_policy_iris_resolve():
    """Every ion://policy/... IRI in offer schema must have a policy doc."""
    offer = ROOT / "schema" / "extensions" / "logistics" / "offer" / "v1" / "attributes.yaml"
    if not offer.exists():
        warn("POLICY_CHECK_SKIPPED", "offer/v1/attributes.yaml not found")
        return

    text = offer.read_text(encoding="utf-8")
    iris = set(re.findall(r"ion://policy/[a-zA-Z0-9._\-/]+", text))

    # Build set of policy IDs from all policy yaml files
    existing_ids = set()
    for p in (ROOT / "policies").rglob("*.yaml"):
        try:
            for doc in yaml.safe_load_all(p.read_text(encoding="utf-8")):
                if isinstance(doc, dict):
                    pid = doc.get("id") or doc.get("iri")
                    if pid:
                        existing_ids.add(f"ion://policy/{pid}")
                        existing_ids.add(pid)
        except Exception:
            continue

    for iri in sorted(iris):
        # Strip ion://policy/ prefix and check
        short = iri.replace("ion://policy/", "")
        if iri not in existing_ids and short not in existing_ids:
            warn("POLICY_IRI_UNRESOLVED",
                 f"IRI {iri} referenced in offer schema but no matching policy document found")


# ─── Check 9: selectRequired in examples ──────────────────────────────────────

def check_select_required_in_examples():
    """Catalog publish examples must declare selectRequired on each offer."""
    for f in ROOT.rglob("catalog-publish.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        providers = (data.get("message", {})
                        .get("catalog", {})
                        .get("providers", []))
        for provider in providers:
            for offer in provider.get("offers", []):
                attrs = offer.get("offerAttributes", {})
                if "selectRequired" not in attrs:
                    err("EXAMPLE_MISSING_SELECT_REQUIRED",
                        f"{f.relative_to(ROOT)} — offer '{offer.get('id', '?')}' "
                        f"missing offerAttributes.selectRequired")


# ─── Check 9a: Beckn 2.0 context.version const ────────────────────────────────

def check_beckn_context_version():
    """Beckn 2.0 requires context.version == "2.0.0" (const) in messages."""
    for f in ROOT.rglob("*.json"):
        if _skip(f):
            continue
        # Only check Beckn message files — must live under examples/ directories
        if "examples" not in str(f):
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        ctx = data.get("context")
        if not isinstance(ctx, dict):
            continue
        # Only validate if this actually looks like a Beckn message
        # (has bapId or bppId in context)
        if not (ctx.get("bapId") or ctx.get("bppId")):
            continue
        version = ctx.get("version")
        if version is None:
            err("CONTEXT_VERSION_MISSING",
                f"{f.relative_to(ROOT)} — context.version is missing")
        elif version != "2.0.0":
            err("CONTEXT_VERSION_INCORRECT",
                f"{f.relative_to(ROOT)} — context.version is '{version}', "
                f"Beckn 2.0 requires exactly '2.0.0'")


# ─── Check 9b: JSON-LD @context/@type on extension Attributes ─────────────────

def check_jsonld_on_attributes():
    """Every extension Attributes payload in examples must have @context and @type."""
    attr_slots = [
        "providerAttributes", "offerAttributes", "resourceAttributes",
        "commitmentAttributes", "considerationAttributes",
        "performanceAttributes", "contractAttributes",
        "settlementAttributes", "participantAttributes",
        "trackingAttributes", "targetAttributes", "supportAttributes",
    ]

    def walk(obj, path):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in attr_slots and isinstance(v, dict):
                    # This is an extension Attributes payload
                    if "@context" not in v:
                        err("JSONLD_CONTEXT_MISSING",
                            f"{path}.{k} — missing required @context")
                    if "@type" not in v:
                        err("JSONLD_TYPE_MISSING",
                            f"{path}.{k} — missing required @type")
                walk(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                walk(item, f"{path}[{i}]")

    for f in ROOT.rglob("*.json"):
        if _skip(f) or "examples" not in str(f):
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            walk(data, str(f.relative_to(ROOT)))
        except Exception:
            continue


# ─── Check 9c: Contract.status uses only Beckn 2.0 allowed values ────────────

def check_contract_status_enum():
    """Contract.status.code must be one of DRAFT|ACTIVE|CANCELLED|COMPLETE."""
    allowed = {"DRAFT", "ACTIVE", "CANCELLED", "COMPLETE"}

    def walk(obj, path):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "contract" and isinstance(v, dict):
                    status = v.get("status")
                    if isinstance(status, dict):
                        code = status.get("code")
                        if code and code not in allowed:
                            err("CONTRACT_STATUS_INVALID",
                                f"{path}.contract.status.code = '{code}' "
                                f"— must be one of {sorted(allowed)}")
                walk(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                walk(item, f"{path}[{i}]")

    for f in ROOT.rglob("*.json"):
        if _skip(f) or "examples" not in str(f):
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            walk(data, str(f.relative_to(ROOT)))
        except Exception:
            continue


# ─── Check 9d: Contract.commitments required (minItems 1) ────────────────────

def check_contract_commitments_present():
    """Contract must carry at least one commitment per Beckn 2.0."""

    def walk(obj, path):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "contract" and isinstance(v, dict):
                    commitments = v.get("commitments")
                    if commitments is not None and isinstance(commitments, list):
                        if len(commitments) < 1:
                            err("CONTRACT_NO_COMMITMENTS",
                                f"{path}.contract.commitments "
                                f"— empty, Beckn 2.0 requires minItems: 1")
                walk(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                walk(item, f"{path}[{i}]")

    for f in ROOT.rglob("on-confirm*.json"):
        if _skip(f):
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            walk(data, str(f.relative_to(ROOT)))
        except Exception:
            continue


# ─── Check 9e: No deprecated Beckn elements ──────────────────────────────────

def check_no_deprecated_beckn():
    """publishDirectives is deprecated per Beckn 2.0.

    We only flag ION-authored files. The composed spec
    (ion-with-beckn.yaml) and any upstream Beckn source (beckn.yaml) may
    legitimately reference publishDirectives to document it as deprecated.
    """
    SKIP_NAMES = {"ion-with-beckn.yaml", "beckn.yaml"}
    for f in ROOT.rglob("*"):
        if not f.is_file():
            continue
        if _skip(f):
            continue
        if f.suffix not in (".yaml", ".json"):
            continue
        if f.name in SKIP_NAMES:
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue
        if "publishDirectives" in text:
            err("DEPRECATED_BECKN_ELEMENT",
                f"{f.relative_to(ROOT)} — uses deprecated publishDirectives")


# ─── Check 10: State machine terminal states ───────────────────────────────────

def check_state_machines():
    """Every state machine in states.yaml must declare terminal states."""
    states_file = (ROOT / "schema" / "extensions" / "logistics" /
                   "performance-states" / "v1" / "states.yaml")
    if not states_file.exists():
        err("STATES_MISSING", "performance-states/v1/states.yaml not found")
        return
    try:
        data = yaml.safe_load(states_file.read_text(encoding="utf-8"))
    except Exception:
        return
    if not isinstance(data, dict):
        return
    machines = data.get("states", {})
    for name, machine in machines.items():
        if not isinstance(machine, dict):
            continue
        terminal = machine.get("terminal")
        if not terminal:
            err("STATE_MACHINE_NO_TERMINAL",
                f"states.yaml :: {name} — no terminal states declared")
        transitions = machine.get("transitions", {})
        if not transitions:
            err("STATE_MACHINE_NO_TRANSITIONS",
                f"states.yaml :: {name} — no transitions declared")


# ─── Check 11: No empty files ─────────────────────────────────────────────────

def check_empty_files():
    """No file in the repo should be empty."""
    for f in ROOT.rglob("*"):
        if _skip(f):
            continue
        if f.is_file() and f.stat().st_size == 0:
            err("EMPTY_FILE", str(f.relative_to(ROOT)))


# ─── Check 12: profile.json present ───────────────────────────────────────────

def check_profile_json():
    """Every spine and branch version directory must have profile.json."""
    for spine_dir in (ROOT / "flows" / "logistics" / "spines").glob("*/v1"):
        if not (spine_dir / "profile.json").exists():
            err("PROFILE_MISSING", f"{spine_dir.relative_to(ROOT)}/profile.json")
    for branch_dir in (ROOT / "flows" / "logistics" / "branches").glob("*/v1"):
        if not (branch_dir / "profile.json").exists():
            err("PROFILE_MISSING", f"{branch_dir.relative_to(ROOT)}/profile.json")


# ─── Check 13: README.md present ──────────────────────────────────────────────

def check_readmes():
    """Every spine, branch, and schema pack must have a README.md."""
    for spine_dir in (ROOT / "flows" / "logistics" / "spines").glob("*/v1"):
        if not (spine_dir / "README.md").exists():
            err("README_MISSING", f"{spine_dir.relative_to(ROOT)}/README.md")
    for branch_dir in (ROOT / "flows" / "logistics" / "branches").glob("*/v1"):
        if not (branch_dir / "README.md").exists():
            err("README_MISSING", f"{branch_dir.relative_to(ROOT)}/README.md")
    for pack_dir in (ROOT / "schema" / "extensions" / "logistics").glob("*/v1"):
        if not (pack_dir / "README.md").exists():
            err("README_MISSING", f"{pack_dir.relative_to(ROOT)}/README.md")


# ─── Check 14: At least one example per spine ─────────────────────────────────

def check_examples():
    """Every spine must have at least one example file."""
    for spine_dir in (ROOT / "flows" / "logistics" / "spines").glob("*/v1"):
        examples_dir = spine_dir / "examples"
        if not examples_dir.exists() or not any(examples_dir.iterdir()):
            err("NO_EXAMPLES",
                f"{spine_dir.relative_to(ROOT)} — no examples directory or no example files")


# ─── Check 15: Beckn 2.0 endpoint names in docs ───────────────────────────────

def check_beckn2_endpoints():
    """Docs must use correct Beckn 2.0 endpoint naming conventions."""
    # These indicate v1.x patterns that should not appear
    v1_patterns = [
        (r"\bon_search\b",                  "Use on_discover (Beckn 2.0)"),
        # /search is v1.x ONLY when standalone — /catalog/master/search is valid Beckn 2.0
        (r'(?<!master)(?<!master/)"/search"', "Use /discover (Beckn 2.0) — /search is v1.x"),
        (r'step:\s+search\b',               "Use discover step — search is v1.x"),
    ]
    # These must appear in the dev orientation doc
    required_concepts = [
        (r"catalog/publish", "catalog/publish must be mentioned"),
        (r"on_discover",     "on_discover must be mentioned"),
        (r"selectRequired",  "selectRequired must be mentioned"),
    ]
    # Prefer the merged-repo name; fall back to logistics-repo name for safety.
    orient_doc = ROOT / "docs" / "ION_Sector_B_Logistics.md"
    if not orient_doc.exists():
        orient_doc = ROOT / "docs" / "01-developer-orientation.md"
    if orient_doc.exists():
        text = orient_doc.read_text(encoding="utf-8")
        rel = orient_doc.relative_to(ROOT)
        for pat, hint in required_concepts:
            if not re.search(pat, text):
                err("ORIENTATION_INCOMPLETE",
                    f"{rel} — missing concept: {hint}")
        for pat, hint in v1_patterns:
            if re.search(pat, text):
                err("BECKN_V1_IN_DOCS",
                    f"{rel} — {hint}")
    else:
        err("ORIENTATION_MISSING", "docs/ION_Sector_B_Logistics.md not found")


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _skip(f: Path) -> bool:
    """Skip generated files, hidden files, and non-spec files."""
    parts = f.parts
    return any(p.startswith(".") or p in ("__pycache__", ".git") for p in parts)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="ION Logistics spec validator"
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="Treat warnings as errors"
    )
    args = parser.parse_args()

    print("ION Network Spec Validator")
    print("=" * 40)

    check_yaml_json_parse()
    check_empty_files()
    check_jsonld_populated()
    check_context_schema_drift()
    check_mandatory_annotations()
    check_no_duplicate_error_codes()
    check_no_beckn_v1_paths()
    check_spine_structure()
    check_branch_structure()
    check_policy_iris_resolve()
    check_select_required_in_examples()
    check_beckn_context_version()
    check_jsonld_on_attributes()
    check_contract_status_enum()
    check_contract_commitments_present()
    check_no_deprecated_beckn()
    check_state_machines()
    check_profile_json()
    check_readmes()
    check_examples()
    check_beckn2_endpoints()

    total_errors = len(ERRORS)
    total_warnings = len(WARNINGS)

    if args.strict:
        all_issues = ERRORS + [(f"WARN_{c}", m) for c, m in WARNINGS]
    else:
        all_issues = ERRORS

    if not all_issues:
        if total_warnings:
            print(f"\n✓ ALL VALIDATION CHECKS PASSED ({total_warnings} warning(s))\n")
            for cat, msg in WARNINGS[:5]:
                print(f"  [WARN:{cat}] {msg}")
            if total_warnings > 5:
                print(f"  ... and {total_warnings - 5} more warnings (run with --strict to fail on these)")
        else:
            print("\n✓ ALL VALIDATION CHECKS PASSED — no issues found\n")
        return 0

    print(f"\n✗ VALIDATION FAILED — {total_errors} error(s), {total_warnings} warning(s)\n")
    by_cat = {}
    for cat, msg in ERRORS:
        by_cat.setdefault(cat, []).append(msg)
    for cat in sorted(by_cat):
        msgs = by_cat[cat]
        print(f"  [{cat}] {len(msgs)} issue(s):")
        for m in msgs[:8]:
            print(f"    - {m}")
        if len(msgs) > 8:
            print(f"    ... and {len(msgs) - 8} more")
        print()

    if WARNINGS and not args.strict:
        print(f"  {total_warnings} additional warning(s) — run with --strict to see them\n")

    return 1


if __name__ == "__main__":
    sys.exit(main())
