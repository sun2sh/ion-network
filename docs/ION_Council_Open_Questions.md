# ION Council — Open Questions (v0.5.2-draft)

This document logs the network-level decisions that have been taken for the v0.5.2-draft spec plus the corresponding open questions that ION Council should formally ratify. Every item below is already **carried out in the spec** at the positions listed — this doc records the decision, its rationale, and the formal question Council should answer.

The pattern is: *position taken, rationale, question for Council, what Council could change if it disagreed.*

---

## Q1 — Registry surface: "ION Registry" vs "dedi.global"

**Position taken.** User-facing documentation, ION's onboarding flows, and all participant-developer material refer exclusively to **"ION Registry."** The underlying implementation runs on Beckn's DeDi infrastructure, but participants never interact with `dedi.global` directly. ION Registry captures Indonesia-specific participant fields (NPWP, NIB, PKP status, Indonesian address hierarchy, authorised-signatory details, operating hours) that are outside the minimum DeDi directory schema.

**Where this shows up in the spec.**
- `docs/ION_Onboarding_and_Auth.md` — uses "ION Registry" throughout
- `schema/core/v2/api/v2.0.0/ion.yaml` — registry references are ION-surfaced
- `schema/extensions/core/participant/v1/attributes.yaml` — captures the extra fields

**Rationale.** Two reasons: (a) participants should not have to learn an additional network's terminology to onboard to ION; (b) ION needs to collect more identity and compliance information than vanilla DeDi specifies, and that collection layer deserves its own name.

**Question for Council.**
> Is it acceptable to call this layer "ION Registry" in all participant-facing material even though the underlying directory is DeDi-compliant? If yes, please ratify the name and the convention of not surfacing DeDi as a participant-facing term.

**If Council disagrees.** The rename to "ION subscribers on dedi.global" is mechanical — it's a single sweep across `docs/` and `ion.yaml`. No schema changes required.

---

## Q2 — Catalog infrastructure: Catalogue Service + Discover Service (two layers) vs single CDS

**Position taken.** ION documents its catalog infrastructure as two logical components:
- **ION Catalogue Service** — a storage/index layer where BPPs publish catalog documents. Hosted by ION (can be sharded per sector or region).
- **Discover Service (CDS)** — the Beckn-compliant discovery query layer that BAPs hit with `/discover` and from which catalog subscriptions flow.

Upstream Beckn v2.0.0 merges these into a single "Catalog Discovery Service (CDS)" that handles both publication ingestion and BAP-facing query. ION's split is ION-specific.

**Where this shows up.**
- `docs/ION_Sector_B_Logistics.md` §2 — "Phase 1 — Catalog"
- `README.md` — two-phase architecture diagram

**Rationale.** ION expects Indonesia-scale catalogs to require sharding by sector (Trade vs Logistics) and by geography, and to need independent scaling of the write-path (BPP publish ingestion) vs the read-path (BAP query). Keeping the two components named separately preserves the ability to deploy and scale them independently.

**Question for Council.**
> Is the two-layer naming ("ION Catalogue Service + Discover Service/CDS") acceptable as an ION-specific architectural refinement of Beckn v2's single-CDS model? Or should ION adopt the single-CDS naming for upstream alignment and treat internal sharding as an implementation detail?

**If Council disagrees.** The rename to a single CDS is mechanical in docs and doesn't affect schemas. The operational consequence of operating it as one service vs two is a decision for the implementation team.

---

## Q3 — `/raise` and `/reconcile` as ION L3 extensions vs upstream contribution

**Position taken.** Both protocols are defined as **ION L3 protocol extensions** in `schema/core/v2/api/v2.0.0/ion-endpoints.yaml` for v0.5.2-draft:
- `/raise` family (6 endpoints: raise, on_raise, raise_status, on_raise_status, raise_details, on_raise_details) — network-level dispute escalation after bilateral resolution fails
- `/reconcile` + `/on_reconcile` — structured financial settlement with tax declarations, COD remittance, FWA rebates

These are not part of Beckn core. ION carries them as extensions so ION can roll out and battle-test them in production before proposing upstream.

**Where this shows up.**
- `schema/core/v2/api/v2.0.0/ion-endpoints.yaml` — all 8 endpoints
- `docs/ION_Beckn_Conformance.md` §2 — ION Protocol Extensions
- `schema/extensions/core/raise/v1/` and `core/reconcile/v1/` — payload packs

**Rationale.** Upstream Beckn v2 explicitly says "this repository is intentionally kept minimal and stable — domain-level transaction schemas and type systems evolve outside." Network-escalation and structured-reconciliation are arguably cross-cutting, but ION needs real production data on them before arguing for upstream inclusion.

**Questions for Council.**
> (a) Does Council ratify `/raise` and `/reconcile` as ION L3 extensions for v0.5.2 and the v0.6 production rollout?
>
> (b) What is the target quarter for proposing `/raise` and/or `/reconcile` upstream to the Beckn Core Working Group? Council should set a review milestone — e.g., "review after 6 months of production network data."

**If Council disagrees.** If Council wants these as Beckn-native from day one, ION would need to submit PRs to `beckn/protocol-specifications-v2` before v0.5.2 goes to production. That significantly slows the rollout.

---

## Q4 — Beckn version target: v2.0.0-rc1 vs waiting for final v2.0.0

**Position taken.** v0.5.2-draft targets [`core-v2.0.0-rc1`](https://github.com/beckn/protocol-specifications-v2/releases/tag/core-v2.0.0-rc1) (the current Beckn Protocol v2 Release Candidate, tagged 2026-01-12). Final Beckn v2.0.0 is expected within ~1 week of this draft.

**Where this shows up.**
- `schema/core/v2/api/v2.0.0/ion.yaml` — `x-ion-compatibility.becknCoreUpstreamTag: core-v2.0.0-rc1`, `becknCoreStatus: RELEASE_CANDIDATE`
- `README.md` — upstream-target callout
- `CHANGELOG.md` — re-validation commitment

**Rationale.** ION needs to publish v0.5.2-draft now to unblock partner BPP/BAP development; waiting for Beckn v2.0.0 final would delay by ~1 week with no structural change expected.

**Commitment.** When final Beckn v2.0.0 releases, ION will re-validate v0.5.2-draft against it and publish either **v0.5.2 GA** (if no changes needed) or **v0.5.3-draft** (if upstream corrections require ION changes).

**Question for Council.**
> Is Council comfortable with v0.5.2-draft targeting a release candidate? Or should GA publication be held until final v2.0.0 is out?

**If Council disagrees.** Hold v0.5.2-draft as a private draft; publish GA only after final v2.0.0 ships.

---

## Q5 — Schema.beckn.io domain schema import: ION uses its own taxonomy

**Position taken.** ION will **not import** the upstream `schema.beckn.io` domain schemas (388 types across 348 modules at time of writing). ION defines its own sector attribute packs (`schema/extensions/{core,trade,logistics}/*/`) that attach to Beckn's native `*Attributes` slots.

**Rationale.**
- Upstream's domain classifications (mobility, local-retail, DEG/energy, etc.) do not match ION's Indonesian sector model (Trade with 13 spines, Logistics with 6 spines, with Indonesian regulatory overlays on both).
- Importing upstream types would force ION users to shift between two taxonomies (Beckn module names vs ION sector names) to find the right field — this is exactly the "two networks to learn" problem Q1 avoids for the registry.
- ION's extension packs already populate Beckn's native slots, so ION is **Beckn-native at the transport level** even without importing upstream domain types.
- ION's commitment is: **we do not invent fields that duplicate Beckn-core properties**. We only add fields that carry Indonesian or sector-specific content not present in Beckn core. The self-audit pass that accompanies this draft confirms no shadows of Beckn-core properties at the ION-pack level.

**Question for Council.**
> Is it acceptable that ION schemas live in ION's own namespace (`schema.ion.id/...`) and are not imported from `schema.beckn.io` — even though both are notionally compatible through the `Attributes` slot mechanism?

**Re-visit.** This position is worth re-examining once Beckn v2.0.0 stabilizes and `schema.beckn.io`'s governance and taxonomy conventions settle. A mid-v0.6 review is reasonable.

---

## Q6 — ONDC comparison table retention

**Position taken.** `docs/ION_Sector_B_Logistics.md` §15 retains the "What ION covers that ONDC Logistics does not" comparison table.

**Rationale.** Many potential ION participants are familiar with ONDC's logistics layer and ask specifically "why not ONDC?" The table answers that directly with coverage gaps (hyperlocal, FIFO agent assignment, slotted delivery, FWA, inter-island water transport, Ro-Ro, warehousing, VAS, cold chain proof, multi-attempt NDR, policy IRIs, reconcile adjustments).

**Question for Council.**
> Is the ONDC comparison table appropriate at this level of detail? Or should it move to a separate positioning document (non-spec), keeping the sector doc purely technical?

---

## Q7 — JSON-LD as ION's semantic model; schema.ion.id publication

**Position taken.** ION commits to being a JSON-LD-first network for cross-country interoperability. v0.5.2-draft makes the commitment concrete by:

1. **Publishing all ION extension vocabulary at `https://schema.ion.id/`.** Every extension pack in `schema/extensions/{layer}/{pack}/{version}/` has a corresponding dereferenceable URL at `https://schema.ion.id/{layer}/{pack}/{version}/`. Every term has a canonical IRI of the form `https://schema.ion.id/{layer}/{pack}/{version}#{term}`.

2. **Making JSON-LD artefacts load-bearing.** `context.jsonld` files are now auto-regenerated from `attributes.yaml` via `tools/regenerate_contexts.py`. The validator enforces context/schema consistency via the `DRIFT_*` check family. No more decorative JSON-LD.

3. **Declaring the semantic model in `ion.yaml`.** The new `x-ion-semantic-model` block documents: vocabulary root URL, URL patterns, content-negotiation map, allowed context prefixes (v0.5.2: `ion:` + `beckn:` core only), cross-network mapping policy.

4. **Deferring full source-of-truth inversion to v0.6.** Today OpenAPI (`attributes.yaml`) remains authoritative for wire validation; JSON-LD is the published vocabulary reference. v0.6 will flip authority so that a vocabulary file (Turtle or JSON-LD graph) generates both OpenAPI and JSON-LD — but only if the tooling investment is justified by cross-network demand at that stage.

5. **Keeping the namespace gate closed for now.** Only `ion:` and `beckn:` are whitelisted. Cross-network vocabularies (`ondc:`, `schema.org:`) will be added one-at-a-time in v0.6+ with Council-ratified mappings published under `https://schema.ion.id/mappings/{other-network}/`.

**Where this shows up.**
- `schema/core/v2/api/v2.0.0/ion.yaml` → `x-ion-semantic-model` block
- `tools/build_schema_site.py` → static-site generator producing `dist/schema.ion.id/`
- `tools/regenerate_contexts.py` → keeps contexts in lockstep with schemas
- `tools/validate.py` → enforces drift via `DRIFT_*` warnings (to be escalated to errors in v0.6)
- `docs/ION_Semantic_Model_Transition.md` → full v0.5→v0.6 transition plan

**Rationale.** ION isn't just publishing an Indonesian network — it's publishing one that can be mapped against by ONDC, by future Southeast Asian Beckn-family networks, and by AI agents doing multi-network reasoning. Without dereferenceable URLs at `schema.ion.id`, every third party that integrates with ION has to reverse-engineer ION's wire format. Publishing is a sovereignty move for ION's semantic identity.

**Questions for Council.**

> (a) Ratify `https://schema.ion.id/` as ION's canonical vocabulary endpoint, and approve the URL pattern `{layer}/{pack}/{version}/` + term IRI pattern `{layer}/{pack}/{version}#{term}`.
>
> (b) Ratify URL stability commitment — once a pack is published at schema.ion.id, its URLs cannot be moved or redefined. Deprecation happens via new versions, never by URL deletion.
>
> (c) Assign an owner for schema.ion.id uptime, TLS certificates, and content-negotiation configuration.
>
> (d) Approve the v0.6 milestone to revisit JSON-LD source-of-truth inversion after upstream Beckn v2.0.0 final ships and ION has at least 3 months of production cross-network traffic data.

---

## Q8 — Kominfo data residency and regulatory overlay

**Position taken.** `ion.yaml` declares `x-ion-regulatory.dataResidency: ID` at the network level. Specific Kominfo PDP (Personal Data Protection) compliance requirements are mentioned in onboarding but not enumerated as a policy category.

**Rationale.** PDP compliance is broader than the protocol and is driven by the ION Operator's agreement with Kominfo rather than the schema.

**Question for Council.**
> Does ION need a dedicated `kominfo-pdp` policy category under `/policies/` with machine-readable policy IRIs? Or is declaration at `ion.yaml` level sufficient for v0.5.2?

---

## Summary — positions taken, items awaiting Council

| # | Topic | Status in v0.5.2-draft | Council action |
|---|---|---|---|
| Q1 | Registry name | "ION Registry" used throughout | Ratify or rename |
| Q2 | Catalog infrastructure split | Two-layer (Catalogue + CDS) | Ratify or merge into single CDS |
| Q3 | /raise and /reconcile as L3 | Implemented as ION extensions | Set upstream-proposal milestone |
| Q4 | Beckn v2.0.0-rc1 target | Declared in `ion.yaml` | Ratify GA publication plan |
| Q5 | No schema.beckn.io import | Not imported | Ratify or schedule import work |
| Q6 | ONDC comparison table | Retained in Logistics doc | Keep or move to positioning doc |
| Q7 | JSON-LD / schema.ion.id | Publication approved; contexts made load-bearing; full inversion deferred to v0.6 | Ratify URL + stability commitment; assign owner |
| Q8 | Kominfo PDP policy category | Declared at network level only | Decide if dedicated category needed |

---

*Last updated v0.5.2-draft — April 2026*
