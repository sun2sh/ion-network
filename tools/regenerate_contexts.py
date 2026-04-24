#!/usr/bin/env python3
"""
regenerate_contexts.py

Regenerate the `@context` term list of every pack's context.jsonld from its
attributes.yaml. This keeps JSON-LD contexts in lockstep with OpenAPI schemas
so schema.ion.id publishes coherent vocabulary.

Preserves:
  - The existing @context prefix declarations (ion:, beckn:, rdfs:, xsd:, etc.)
  - Any hand-edited term annotations (e.g. a term with {"@type": "@id"} for IRI
    references) — if a term already exists, its definition is kept as-is.

Adds:
  - Missing property terms (bare name -> "ion:{name}" mapping)
  - Missing class terms (class name -> "ion:{ClassName}" mapping)

Removes:
  - Terms whose underlying schema property/class no longer exists

Run as:
  python3 tools/regenerate_contexts.py          # rewrite in place
  python3 tools/regenerate_contexts.py --check  # exit non-zero if changes would be made
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
EXT = ROOT / "schema" / "extensions"

CLASS_HINT_SUFFIXES = ("Attributes", "Ticket", "Addendum", "Subdivisions",
                       "Identity", "Localization", "Declaration", "Detail",
                       "Certifications", "Text", "Reference", "Fee",
                       "Terms", "Response", "Policy")
CLASS_HINT_EXACT = {
    "LocalisedText", "PaymentDeclaration", "CashOnDelivery", "BankTransfer",
    "EWallet", "VirtualAccount", "QRIS", "BNPL", "CardPayment", "BISettlement",
    "IONTicket", "CreditTerms", "InvoiceReference", "ProcessingFee", "Refund",
}


def looks_like_class(name: str) -> bool:
    if not name or not name[0].isupper():
        return False
    if name in CLASS_HINT_EXACT:
        return True
    return any(name.endswith(s) for s in CLASS_HINT_SUFFIXES)


def extract_schema(attrs_path: Path):
    """Return (set-of-props, set-of-classes)."""
    doc = yaml.safe_load(attrs_path.read_text(encoding="utf-8"))
    props = set()
    classes = set()
    for sname, sdef in (doc.get("components", {}).get("schemas", {}) or {}).items():
        if not isinstance(sdef, dict):
            continue
        classes.add(sname)
        for pname in (sdef.get("properties") or {}).keys():
            props.add(pname)
    return props, classes


def load_context(ctx_path: Path) -> dict:
    return json.loads(ctx_path.read_text(encoding="utf-8"))


def regenerate_one(attrs_path: Path, ctx_path: Path) -> tuple[dict, bool]:
    """
    Return (new_doc, changed). The new doc is the updated context.jsonld
    structure. `changed` is True if the new doc differs from the existing.
    """
    props, classes = extract_schema(attrs_path)
    original = load_context(ctx_path)
    new_doc = json.loads(json.dumps(original))  # deep copy

    ctx = new_doc.get("@context", {})
    # If context is a list (multi-entry), operate on the last dict entry;
    # create one if absent.
    if isinstance(ctx, list):
        target = None
        for entry in ctx:
            if isinstance(entry, dict):
                target = entry
        if target is None:
            target = {}
            ctx.append(target)
    else:
        target = ctx

    # Separate existing entries into (prefixes, terms)
    existing_terms = {}
    prefixes = {}
    reserved = {}
    for k, v in list(target.items()):
        if k.startswith("@"):
            reserved[k] = v
            continue
        if isinstance(v, str) and (v.endswith("#") or v.endswith("/")):
            prefixes[k] = v
            continue
        existing_terms[k] = v

    # Determine what terms SHOULD exist
    desired_terms = {}
    for p in sorted(props):
        # bare name maps to "ion:{p}"
        desired_terms[p] = existing_terms.get(p, f"ion:{p}")
    for c in sorted(classes):
        # class name maps to "ion:{ClassName}"
        # (also allow an "ion:ClassName" key form if it was already there)
        prefixed = f"ion:{c}"
        if c in existing_terms:
            desired_terms[c] = existing_terms[c]
        elif prefixed in existing_terms:
            desired_terms[prefixed] = existing_terms[prefixed]
        else:
            desired_terms[c] = prefixed

    # Build the new @context: @reserved first, then prefixes, then terms (sorted)
    new_ctx = {}
    for k, v in reserved.items():
        new_ctx[k] = v
    for k, v in prefixes.items():
        new_ctx[k] = v
    for k in sorted(desired_terms.keys()):
        new_ctx[k] = desired_terms[k]

    if isinstance(ctx, list):
        # Replace the last dict entry
        for i in range(len(ctx) - 1, -1, -1):
            if isinstance(ctx[i], dict):
                ctx[i] = new_ctx
                break
        new_doc["@context"] = ctx
    else:
        new_doc["@context"] = new_ctx

    changed = (original != new_doc)
    return new_doc, changed


def iter_packs():
    for layer_dir in sorted(EXT.iterdir()):
        if not layer_dir.is_dir() or layer_dir.name.startswith("."):
            continue
        for pack_dir in sorted(layer_dir.iterdir()):
            if not pack_dir.is_dir():
                continue
            v1 = pack_dir / "v1"
            if not v1.exists():
                continue
            a = v1 / "attributes.yaml"
            c = v1 / "context.jsonld"
            if a.exists() and c.exists():
                yield f"{layer_dir.name}/{pack_dir.name}/v1", a, c


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--check", action="store_true",
                   help="Exit non-zero if any pack would change.")
    args = p.parse_args()

    changed_packs = []
    for pack_id, attrs, ctx in iter_packs():
        try:
            new_doc, changed = regenerate_one(attrs, ctx)
        except Exception as e:
            print(f"[ERROR] {pack_id}: {e}", file=sys.stderr)
            continue
        if changed:
            changed_packs.append(pack_id)
            if not args.check:
                ctx.write_text(json.dumps(new_doc, indent=2) + "\n",
                               encoding="utf-8")

    if args.check:
        if changed_packs:
            print("Context drift detected in:")
            for p in changed_packs:
                print(f"  {p}")
            print("\nRun: python3 tools/regenerate_contexts.py")
            sys.exit(1)
        print("All contexts in sync.")
    else:
        if changed_packs:
            print(f"Regenerated {len(changed_packs)} context file(s):")
            for p in changed_packs:
                print(f"  {p}")
        else:
            print("All contexts already in sync.")


if __name__ == "__main__":
    main()
