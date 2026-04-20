# Contributing to ION Network

## The fastest way to contribute — ION Atlas

For field additions and schema questions, ION Atlas is the right tool. It prevents duplicates, checks for clashes with Beckn core, and drafts compliant schema files automatically.

```bash
npm install -g @ion-network/cli

ion search "what you need"        # check if it already exists
ion validate yourFieldName        # clash detection before proposing
ion propose                       # draft + submit PR in one flow
```

Web Explorer: `devlabs.ion.id/atlas (coming soon)`

---

## Contribution types

### Adding a new field

Use `ion propose`. The interactive flow will:
1. Check existing schemas semantically — you may find it already exists
2. Run clash detection against Beckn reserved terms
3. Draft `attributes.yaml`, `context.jsonld`, and `vocab.jsonld`
4. Raise a PR to the ION Council

If you prefer GitHub directly, use `.github/ISSUE_TEMPLATE/field_proposal.md`.

**Approval bar by type:**

| Type | Bar |
|---|---|
| New field within existing pack | Standard PR — single reviewer |
| New pack within existing sector | Elevated — sector lead + council |
| New sector | Exceptional — full council + Beckn team |
| ION core field (cross-sector) | High — full council decision |

### Reporting a spec issue

Use `.github/ISSUE_TEMPLATE/spec_issue.md` for errors or gaps in existing files — wrong field type, missing enum value, incorrect regulatory reference, flow step with wrong required fields.

### Proposing a new error code

Use `.github/ISSUE_TEMPLATE/error_proposal.md`. Assign the next available code in the correct category range (see `errors/README.md`). After approval, run `python errors/generate_registry.py` to regenerate `registry.json`.

---

## ION Council review

All PRs are reviewed by the ION Council fortnightly. The Council includes the Beckn team for decisions with upstream implications. No schema enters the network without that review.

- Approved → merged → Atlas registry re-indexed
- Rejected → feedback to proposer
- Upstream → Beckn team reviews for Tier 2 core inclusion

---

## Branching

- `main` — current ratified spec
- `draft/*` — working branches for new patterns or packs

## Code style

All field names follow Beckn's mandated camelCase. YAML files must parse with `python3 -c "import yaml; yaml.safe_load(open('file').read())"`. JSON files must parse as valid JSON.
