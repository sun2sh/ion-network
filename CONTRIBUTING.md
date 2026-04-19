# Contributing to the ION Network Specification

This repo is the authoritative specification for the ION Network. Contributions fall into three categories — and the process differs for each.

---

## 1 — Reporting a spec issue

Use **GitHub Issues** for:

- A field in a YAML that is missing, wrong, or ambiguous
- A validation rule that does not match your implementation experience
- An Indonesian regulatory requirement that is not covered
- A commerce pattern that needs a field the Dictionary does not have
- An error code that is missing from the registry

Use the issue templates in `.github/ISSUE_TEMPLATE/`. Be specific: which file, which field, what you expected, what you found, and if relevant, what Indonesian regulation is the basis.

---

## 2 — Proposing a new field

New fields follow the Atlas governance process.

**Before raising a proposal, check:**
- The Trade Dictionary — the field may already exist under a different name
- Open issues — someone may have already proposed the same field
- The field layer — ION Core proposals need stronger justification than sector-level proposals

**To propose a new field:**

Open an Issue using the **Field Proposal** template. Include:

```
Field name:        camelCase — e.g. halalCertNumber
Layer:             ION Core | Sector-Trade | Flow-B2C | etc.
Beckn object:      Resource | Offer | Contract | Performance | etc.
Attributes bag:    resourceAttributes | offerAttributes | contractAttributes | etc.
Type:              string | integer | boolean | object | array | enum
Format/pattern:    e.g. ^[0-9]{13}$ for NIB
Enum values:       pipe-separated if enum — e.g. OPEN|TEMPORARILY_CLOSED|DISABLED
Mandatory:         always | conditional | optional
Condition:         plain English — e.g. "required when dietaryClassification=HALAL"
Regulatory basis:  Indonesian law or standard — e.g. PerBPOM No. 22/2019
Example value:     A realistic Indonesian example
Use case:          Which commerce pattern needs this and why
```

ION Council working group reviews field proposals at fortnightly governance cycles. You will receive feedback as comments on the issue.

---

## 3 — Submitting a spec improvement (PR)

For non-breaking improvements that do not require a field proposal — fixing a typo, adding a missing example, improving a description, adding an enum value that was overlooked:

1. Fork this repo
2. Make your change in the relevant YAML or markdown file
3. Open a PR with a clear description of what changed and why
4. Reference any related issues

**PR rules:**
- One logical change per PR
- Do not change field names, types, or remove enum values without raising an issue first — these are breaking changes
- YAML files must remain valid (`python3 -c "import yaml; yaml.safe_load(open('file.yaml'))"`)
- ION is an Indonesian network — keep examples Indonesian (real businesses, IDR prices, Indonesian regulatory fields)

---

## 4 — Contributing to the error registry

The error registry at `errors/ion_error_registry.json` is designed for collaborative contribution. If you encounter an error code in your implementation that is not in the registry, or if an existing entry's resolution guidance is wrong:

1. Open an Issue with the **Error Registry** template
2. Include: the error code, which API call triggered it, the exact payload that caused it, and what fixed it
3. For new entries, propose the full JSON object following the schema in the registry

---

## Governance cycles

| Change type | Process | Typical timeline |
|---|---|---|
| New ION Core field | Full ION Council vote | 4–6 weeks |
| New Sector field | Working group review + Council notification | 2 weeks |
| New Flow field | Working group review | 1 week |
| New enum value (non-breaking) | PR review | Days |
| Error registry entry | PR review | Days |
| Typo / description fix | PR review | Days |
| Breaking change (any layer) | Full ION Council vote + deprecation notice | 8+ weeks |

---

## Code of conduct

This is a technical specification repo. Keep discussions focused on the spec. Be specific, cite sources (Indonesian law, Beckn docs, your implementation experience), and assume good faith. Proposals that are vague or lack Indonesian regulatory basis will be returned for more detail before review.

---

*Questions about the contribution process? Open an Issue with the label `process-question`.*
