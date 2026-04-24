# ION Network Specification — Changelog

## v0.5.2-draft (April 2026)

**Theme: Logistics sector merge, five-layer clarity, and schema.ion.id vocabulary publishing.**

Prior to v0.5.2, ION Logistics lived in a separate repository (`ion-logistics`) that duplicated cross-sector concerns already present in `ion-network`. This release unifies them into a single repo structured around an explicit five-layer model. It also introduces `schema.ion.id` as ION's canonical, dereferenceable vocabulary endpoint — a strategic commitment for cross-country interoperability.

Trade readers see no changes to their reading path; logistics readers get a parallel path plus shared network-wide docs. All participants get dereferenceable vocabulary IRIs.

### schema.ion.id — vocabulary publication

ION now publishes its extension vocabulary at `https://schema.ion.id/` with dereferenceable IRIs per pack/term. This is a strategic move for multi-network interoperability: third parties can resolve ION term definitions without reverse-engineering the wire format, and ION can publish cross-network mappings (ION ↔ ONDC, ION ↔ other Beckn networks) as first-class artefacts.

- New `x-ion-semantic-model` block in `ion.yaml` declares URL patterns, content-negotiation, allowed context prefixes
- New tool `tools/build_schema_site.py` generates `dist/schema.ion.id/` — static site with per-pack HTML + context.jsonld + attributes.yaml + root landing page + sitemap + headers file
- New tool `tools/regenerate_contexts.py` keeps `context.jsonld` in lockstep with `attributes.yaml` (fixed 14 pre-existing drifts)
- Validator now catches context↔schema drift via new `DRIFT_*` check family (WARN in v0.5.2, escalated to ERROR in v0.6)
- URL pattern: `https://schema.ion.id/{layer}/{pack}/{version}/` with term IRIs `https://schema.ion.id/{layer}/{pack}/{version}#{term}`
- New doc `docs/ION_Semantic_Model_Transition.md` describes v0.5 → v0.6 → v1.0 evolution plan

Full JSON-LD source-of-truth inversion (vocabulary file → generated OpenAPI) is deferred to v0.6 pending cross-network demand. v0.5.2 makes JSON-LD artefacts load-bearing without flipping authority yet. See Council open question Q7.

### Structural changes

**Five-layer model, now explicit.** The layers were present in code before but never named together. New authoritative doc: `docs/ION_Layer_Model.md`.

- L1 — Beckn core (external, unchanged)
- L2 — ION network profile (`schema/core/v2/api/v2.0.0/ion.yaml`)
- L3 — ION protocol endpoint extensions (NEW canonical home: `schema/core/v2/api/v2.0.0/ion-endpoints.yaml`)
- L4 — ION core attribute packs (`schema/extensions/core/*`)
- L5 — ION sector attribute packs (`schema/extensions/{trade,logistics}/*`)

**Layer 3 file introduced.** `/raise`, `/on_raise`, `/raise_status`, `/on_raise_status`, `/raise_details`, `/on_raise_details`, `/reconcile`, `/on_reconcile` are no longer listed as "optional actions" in `ion.yaml`. They now live in a dedicated `ion-endpoints.yaml` that `ion.yaml` references. Zero behavioural change; big clarity win.

**Two sectors active, four reserved.** `ion.yaml` now declares `x-ion-sectors.active: [trade, logistics]` and `x-ion-sectors.reserved: [mobility, finance, tourism, healthcare]` so the directory placeholders have explicit meaning.

### Breaking changes

**None on the wire.** All changes are additive. Logistics implementations that used the old `ion-logistics` repo paths will need to update references to the new consolidated paths, but payload shapes are preserved.

### Duplicates removed (logistics → core promotion)

The old logistics repo had its own `payment`, `rating`, `support`, `participant` packs duplicating equivalents in `ion-core`. These have been consolidated:

- **`logistics/payment` → dropped.** Cross-sector primitives (`paymentRail`, `paymentGatewayProvider`, `creditTerms`, `refund`, `invoice`, `processingFee`, COD runtime fields) promoted to `core/payment/v1`. COD batch remittance moved to `core/reconcile/v1`. COD offer-time fraud controls (OTP required, denominations, daily limits, hold period, reconciliation variance) moved to `logistics/offer/v1`.
- **`logistics/rating` → dropped.** Use `core/rating/v1`.
- **`logistics/support` → dropped.** Use `core/support/v1`.
- **`logistics/participant` → dropped** and **new `core/participant/v1` created.** The cross-sector fields (20-role taxonomy, NPWP/NIB/NIK/KTP/passport, `authorisedSignatory`, full Indonesian `addressDetail` with RT/RW/patokan/areaType/accessibility/operatingHours) moved to core. Logistics-only licence fields (PPJK customs-broker licence, driver SIM number & category) live in the thin new `logistics/participant-logistics/v1` addendum that mounts on the same `Participant.participantAttributes` slot alongside core.

### New in L4 (core)

- **`core/participant/v1`** — unified cross-sector participant pack. Used by trade participants, logistics participants, and every future sector.
- **`core/payment/v1`** — expanded: `paymentRail`, `paymentGatewayProvider`, `creditTerms` (B2B/FWA), `refund` (with MATI default and fallback methods), `invoice` (proforma + final), `processingFee`. `CashOnDelivery` gains `collectionAmountCollected`, `collectionTimestamp`, `collectionReceiptRef`, `partialCollectionReason`.
- **`core/reconcile/v1`** — expanded: `codRemittance` batch block (amount, batchRef, batchPeriod, timestamp, method, variance with tolerance).

### New in L5 (logistics)

10 logistics attribute packs imported: `commitment`, `consideration`, `contract`, `offer` (now carries COD fraud-control fields), `performance`, `performance-states`, `provider`, `resource`, `tracking`, `participant-logistics` (thin addendum).

6 logistics spines imported into `flows/logistics/spines/`: LOG-HYPERLOCAL, LOG-PARCEL, LOG-FREIGHT, LOG-RORO, LOG-XB, LOG-WAREHOUSE.

13 logistics branch families imported into `flows/logistics/branches/`: attempts, cancellation, cod, cold-chain, cross-cutting, customs, during-transaction, ekyc, exception, incident, reverse, rts-handoff, value-added, weight-dispute.

### New policy categories

9 logistics-originated policy categories added: `evidence`, `insurance`, `sla`, `re-attempt`, `weight-dispute`, `liability`, `incident`, `rts-handoff`, `logistics-fwa`. Total ratified policies across trade + logistics: 97.

### Errors

`errors/logistics.yaml` imported. Logistics errors use the `ION-LOG-Nxxx` format and are compiled into a separate `errors/logistics-registry.json`. The cross-sector `ION-Nxxx` registry is unchanged.

### EXPERIMENTAL — spine/pattern on the wire

New optional block in the profile: `x-ion-context-extensions`. When populated on a request `context`, carries:

- `spine` — the spine code claimed by this transaction (e.g. `B2C-SF`, `LOG-PARCEL`)
- `spineVersion` — spine version in force
- `activeBranches` — branch families active for this transaction
- `policyIris` — snapshot of applicable policy IRIs at contract time

Enables deterministic validation at ION Central: "payload claims pattern X → load the spine → verify required fields per step." Optional in v0.5.2 (status `EXPERIMENTAL`), targeted to become mandatory in v0.6 after Council ratification. Feedback welcome via ION Council issue tracker.

### Tax rate language — softened

Hardcoded tax rates in schema descriptions, doc prose, flow README notes, and vocab comments have been rewritten as illustrative. Example transformation: "Standard rate is 0.11 (11%)" → "Applicable rate MUST be sourced from current DJP/PMK regulation. Current standard is 0.11 (11%) per PMK 131/2024." This affects `core/tax/v1`, `trade/consideration/v1`, `logistics/consideration/v1`, and several docs. Enum values, schema field names, and concrete worked-example payloads (which show the actual rate charged on a specific transaction) are preserved as-is.

### Beckn version

All references normalized to Beckn `2.0.0` (targeting [`core-v2.0.0-rc1`](https://github.com/beckn/protocol-specifications-v2/releases/tag/core-v2.0.0-rc1) upstream). `context.version` in messages is `"2.0.0"` (matches Beckn `Context.version` `const: "2.0.0"`). Prior ION drafts had incorrectly labeled this as `2.0.1` — corrected here.

**Target status.** Beckn v2.0.0 is currently a Release Candidate (RC1 tagged 2026-01-12). Final v2.0.0 is expected within ~1 week of this draft. ION will re-validate v0.5.2-draft against final v2.0.0 when released and publish v0.5.2 GA (or v0.5.3-draft if corrections are needed). The upstream target is declared in `schema/core/v2/api/v2.0.0/ion.yaml → x-ion-compatibility.becknCoreUpstreamTag`.

### Tooling

- **`tools/generate_composed.py`** — `PACK_MAP` expanded to include both sectors and the new `core/participant` pack; `participantAttributes` and `trackingAttributes` slots activated. Output now merges 40 ION extension schemas (up from the trade-only baseline) + 69 Beckn core schemas = 109 total, 30 paths.
- **`tools/validate.py`** — replaced with the logistics-superset validator (15 checks vs. 7 previously); duplicate-error-code check generalized to walk every `errors/*.yaml` rather than a single file.
- **`policies/generate_registry.py`** — now handles both the trade per-file `iri:` format and the logistics multi-doc `id:` format; emits a unified `policies/registry.json`.
- **`errors/generate_registry.py`** — emits the cross-sector `registry.json` unchanged plus a new `logistics-registry.json` for `ION-LOG-Nxxx` codes.

### Doc renames (logistics docs lifted to top-level `docs/`)

- `ion-logistics/logistics/docs/ION_Developer_Orientation.md` → `docs/ION_Sector_B_Logistics.md`
- `ion-logistics/logistics/docs/02-sector-guide.md` → `docs/ION_Sector_B_Logistics.md`
- `ion-logistics/logistics/docs/03-onboarding-and-auth.md` → `docs/ION_Onboarding_and_Auth.md` *(generalized to cover every sector)*
- `ion-logistics/logistics/docs/04-beckn-conformance-and-ion-extensions.md` → `docs/ION_Beckn_Conformance.md` *(generalized; attachment table now covers both trade and logistics)*
- `ion-logistics/logistics/docs/ION_Sector_B_Logistics.md (§11)` → `docs/ION_Sector_B_Logistics.md`

Trade docs (`ION_Developer_Orientation.md`, `ION_Sector_A_Trade.md`) are unchanged except for the PPN language sweep noted above.

---

## v0.5.1-draft (April 2026)

**Theme: Beckn Protocol v2.0 alignment.**

This release makes ION wire-compatible with Beckn Protocol v2.0. Prior drafts used Beckn v1.x vocabulary (`order`, `items`, `fulfillments`, `quote`, `billing`, `payment`) and snake_case context fields; implementations against those paths would fail schema validation and signature verification against a Beckn v2.0 peer. v0.5.1 corrects this across all flow documents, examples, and reference material.

### Breaking changes (wire format)

**Context fields — camelCase.** Beckn v2.0 uses `bapId`, `bppId`, `bapUri`, `bppUri`, `transactionId`, `messageId`, `networkId`, `requestDigest`, `schemaContext`. The snake_case variants (`bap_id`, `transaction_id`, etc.) were v1.x and must not be used.

**Message wrapper — `contract`, not `order`.** Beckn v2.0 renamed the canonical transaction object from `Order` to `Contract`. Every action message now carries a single `contract` field:

| Beckn v1.x (pre-v0.5.1) | Beckn v2.0 (v0.5.1+) |
|---|---|
| `message.order.items[]` | `message.contract.commitments[].resources[]` |
| `message.order.fulfillments[]` | `message.contract.performance[]` |
| `message.order.quote` | `message.contract.consideration` |
| `message.order.quote.breakup[]` | `message.contract.consideration.considerationAttributes.breakup[]` |
| `message.order.payment` | `message.contract.settlements[]` |
| `message.order.billing` | `message.contract.participants[?role=BUYER]` |
| `message.order.status` | `message.contract.status.descriptor.code` |
| `message.order.contractAttributes` | `message.contract.contractAttributes` |
| `message.cancel.reason.*` | `message.contract.contractAttributes.cancellationReason.*` |
| `message.cancel.items[]` | `message.contract.contractAttributes.cancelledCommitmentIds[]` |
| `message.update.target.fulfillment.*` | `message.contract.performance[].*` |
| `message.update.target.order.*` | `message.contract.*` |

All thirteen spines, all six branch files, the cross-cutting branch, and example JSON payloads have been migrated.

**Extension attachment points renamed.** `location.fulfillmentAttributes` → `location.address.ionAddressAttributes` (B-9). `baseOrderAmount` → `baseContractAmount` in reconcile pack (B-3).

**Resource type split.** `resourceType` (enum of 8 values conflating structure + tangibility) is deprecated. New fields: `resourceStructure` (PLAIN, VARIANT, WITH_EXTRAS, COMPOSED, BUNDLE) and `resourceTangibility` (PHYSICAL, DIGITAL_VOUCHER, DIGITAL_TOP_UP, DIGITAL_SUBSCRIPTION). Old field kept as deprecated alias for one cycle (B-11).

**Policy IRI grammar canonicalized.** All policy IRIs now use `.` (dot) separators: `ion://policy/{category}.{subcategory}.{specifier}[.{qualifier}]`. Previous mix of `/` and `.` normalized. 67 policy documents and all offer enum references updated (B-14).

### New artifacts

- **`context.jsonld`** populated for all 17 schema packs with @context mappings (ion:, beckn:, schema:, xsd: prefixes + per-field/per-type entries). Enables JSON-LD validation by generic tools (B-4).
- **`vocab.jsonld`** populated for all 17 schema packs with @graph containing rdfs:Class for each schema and rdf:Property for each field.
- **`tools/validate.py`** — spec conformance validator. Checks: YAML/JSON parseable, no empty files, `x-ion-mandatory` on every property, no duplicate error codes, @context/@graph non-empty, no Beckn v1.x paths in flows, all policy IRIs resolve. Use in CI (B-16, B-47 from earlier op review).

### New documentation

Three new Developer Orientation sections (17, 18, 19):

- **Section 17 — Beckn Protocol Layer.** Ack/Nack dual-response model, Context camelCase requirement, `message.contract` wrapper, Attributes extension slots, HTTP Signature scheme with ed25519 and BLAKE2b-512. Includes v1.x→v2.0 field translation table (B-8).
- **Section 18 — Policy IRI Grammar.** Canonical format, segment rules, resolver endpoint, examples (B-14).
- **Section 19 — ION Error Codes in Beckn Nack.** Mapping of ION-prefixed codes into Beckn `Error.code`, `type` enum usage, sync Nack vs async callback placement rules (B-19).

### Documentation quality

- State-machine ↔ Beckn-status field mapping table added to `performance-states/v1/states.yaml` header. Clarifies that ION state codes populate `Performance.status.descriptor.code`, not `Commitment.status` or `Contract.status` (B-7).
- `PaymentDeclaration` attachment point documented in `core/payment/v1` header (attaches to `Settlement.settlementAttributes`; wire path is `message.contract.settlements[].settlementAttributes.*`) (B-10).
- Flow step names normalized — parenthetical suffixes converted to structured `stepContext` field for machine readability (B-20).
- Deprecation comment blocks unified to single-line form with CHANGELOG cross-reference (B-17).

### Validation coverage (CI-ready)

Run `python3 tools/validate.py` in CI to enforce:

- All YAML/JSON parses
- No empty files
- Every schema property has `x-ion-mandatory` (values: always, conditional, optional)
- No duplicate error codes
- All `context.jsonld` and `vocab.jsonld` populated
- No Beckn v1.x field paths leak into flows
- Every policy IRI referenced in offer schema has a corresponding policy document

Current state: **all 7 checks pass**.

### B-5 resolved in v0.5.1

- **B-5.** Composed `ion-with-beckn.yaml` — built by `tools/generate_composed.py`. Merges Beckn Protocol v2.0 core (69 schemas, 30 paths) with all 26 ION extension schemas. Each Beckn `*Attributes` slot is replaced with an `allOf` discriminated union of the relevant ION schema(s). Single validator pass checks both Beckn core conformance and ION field correctness. Slots with multiple possible schemas (e.g., `Settlement.settlementAttributes` carries either `PaymentDeclaration` or `ReconcileAttributes`) use `@type`-discriminated `if/then` within the `allOf`.

### Known gaps — deferred to v0.6

- **B-5 generator:** `generate_composed.py` needs beckn.yaml available at a known path — currently uses `/mnt/project/beckn__1_.yaml`. Wire into CI with `--beckn` flag pointing to canonical registry download. — a merged OpenAPI that inlines Beckn core + ION extensions under one validator. Pending tooling work.
- **B-6.** Settlement-model reconcile cleanup — current `message.contract.settlements[]` path is correct per Beckn, but reconcile-branch payloads retain some ION-specific shorthand that will be normalized in v0.6.
- **B-12.** Complete removal of `fulfillments[]` hybrid naming — still present in some spine READMEs as historical context; will be swept to `performance[]` in v0.6.

---

## v0.5.0-draft (April 2026)

**Theme: Operations-readiness — schema cleanup, policy consolidation, marketplace-scale reconciliation, regulated categories.**

Based on operations review from Amazon Indonesia / Tokopedia / Shopee perspective. Removes schema redundancies, formalises refund timelines per payment method, adds batch settlement, KYC lifecycle, age verification at delivery, data residency controls, and tax withholding declarations. Delivers production-ready spec that can support real-world Day-1 operation.

### BREAKING CHANGES — schema cleanup

- **Removed `offer.cancellable`** (Op-46). Derived from `cancellationPolicy` IRI. The policy IRI equaling `ion://policy/cancel/standard/none` signals non-cancellable.
- **Removed `offer.cancellationFee` and `offer.cancellationFeeApplicableStates`** (Op-44). The cancellationPolicy IRI terms document is now authoritative for fee mechanics. Migrate by pointing to the appropriate policy IRI (e.g. `cancel.b2b.until_dispatched.15pct` for 15% restocking fee).
- **Removed `offer.returnWindow` and `offer.returnAllowedReasons`** (Op-45). The returnPolicy IRI terms document is now authoritative — `returnWindowDays` and `returnReasonsAllowed` live in the policy document, not the offer.
- **Removed `resource.isAvailable`** (Op-5). Availability derived solely from `availability.status`. `OUT_OF_STOCK` and `DISCONTINUED` are the off states.
- **Removed `contract.gift`** (Op-42). Use `contract.giftingDetails` (structured object added in v0.3).
- **Removed `contract.invoiceTypeExtended`** (Op-43). Values `SURAT_TAGIHAN` and `KOMERSIAL_INVOICE` merged into `contract.invoicePreferences.invoiceType` enum.

### New schema fields — operations essentials

- **Op-2 Price schedule** — `offer.priceValidFrom`, `offer.priceValidUntil`, `offer.priceChangeSchedule[]`. Enables mid-campaign price changes, flash-sale pricing phases, and countdown UI on BAPs.
- **Op-3 Variant matrix** — `resource.variantMatrix` with axes + combinationRules. Avoids SKU explosion for multi-axis products (8 colors × 15 models × 2 materials). Supports both SUM_AXIS_DELTAS and EXPLICIT_PRICE calculation modes.
- **Op-9 Tiered payment eligibility** — `offer.paymentMethodEligibility` restructured from flat enum to array of rich constraint objects with minAmount, maxAmount, requiresBuyerTier, requiresAddressVerification, excludedCategories, requiredBnplProvider per method.
- **Op-10 Payment schedule** — `contract.paymentSchedule[]` for multi-milestone payments (down-payment + balance, services with milestones). Contract moves to COMPLETE only when all milestones are PAID.
- **Op-22 Exchange-variant-doorstep** — New sub-branch in returns for single-leg same-SKU-different-variant swaps (size M → L at door). New state machine `exchange_variant` with 6 states. Halves logistics trips vs the return→refund→reorder pattern.

### New schema fields — compliance and risk

- **Op-35 KYC lifecycle** — `provider.kycStatus` (PENDING, APPROVED, APPROVED_WITH_CAVEATS, REJECTED, SUSPENDED, EXPIRED), `kycLevel` (BASIC, STANDARD, ENHANCED, ENTERPRISE), `kycValidUntil`, `kycCaveats[]`, `categoryLicenses[]` (SIA, SIKA, PBF, BPOM_COSMETICS, BPOM_FOOD, etc.).
- **Op-36 Counterfeit flagging** — `COUNTERFEIT_FLAG` added to `raise.type` enum. Brand owners, consumers, marketplaces can flag suspicious listings. Auto-delist pending ION Central arbitration.
- **Op-37 Age verification at delivery** — `performance.ageVerificationRequired`, `ageVerificationMethod` (KTP_SIGHTED, KTP_SCANNED, SIM_SIGHTED, SELFIE_COMPARISON, BIOMETRIC_API), `ageVerifiedAt`, `ageVerifiedByAgentId`, `ageVerificationEvidence`, `ageVerificationFailedReason`. Required for alcohol, tobacco, adult products, certain medicines.
- **Op-38 Data residency** — `resource.dataResidency` (DOMESTIC_ONLY, INTERNATIONAL_ALLOWED). BAPs with foreign data processing must filter DOMESTIC_ONLY resources. Required for pharmacy, health data, financial services per UU 27/2022 PDP Law.

### New schema fields — settlement scalability

- **Op-27 Batch reconcile** — `reconcile.isBatch`, `contractIds[]`, `batchPeriod`, `contractDetails[]`. Enables daily/weekly batched settlement covering thousands of orders in a single reconcile transaction.
- **Op-29 Adjustments and clawbacks** — `reconcile.parentReconId`, `adjustmentType` (CLAWBACK, ADDITIONAL_PAYMENT, CORRECTION, LATE_FEE_CHARGE, GOODWILL_CREDIT), `adjustmentReason`, `adjustmentEvidence[]`. Supports post-reconcile corrections with audit trail.
- **Op-30 Tax withholdings** — `reconcile.taxWithholdings[]` with taxType (PPH22, PPH23, PPH_FINAL_05, PPN_REMIT, PPN_PMSE), rate, basis, amount, remittedTo (DJP, OJK, BI), remittanceRef (NTPN), buktiPotongUrl. Required for Mall-tier and above sellers.
- **Consideration breakup types added**: `PPH_WITHHOLDING`, `PPN_REMIT_PMSE`, `PAYMENT_MILESTONE`.

### Policy document updates

- **Op-19 Refund timeline by payment method** — All 15 RETURN policy documents updated. `refundTimelineFromReturnDelivered` is now an object keyed by payment method: QRIS/EWALLET = PT1H, VA/BANK_TRANSFER = P3D, CREDIT_CARD = P14D, DEBIT_CARD = P7D, BNPL = P5D, COD_TO_WALLET = PT0S. BPP MUST honour the method-specific window.

### Flow updates

- **Op-12 Logistics-domain events documented** — during-transaction `on-network-LSP` sub-branch now explicitly lists events that happen entirely in the Logistics sector and do NOT surface on the Trade protocol: agent reassignment, pickup failure at seller, inter-hub handoffs, LSP-side SLA breaches, cold-chain excursions, multi-package tracking. BPP aggregates net effects (final DELIVERED, final RTO, consumer-visible ETA delay) into the Trade performance record.

### Tooling

- **Op-47 Error registry fail-hard validation** — `errors/generate_registry.py` now exits with non-zero status on: duplicate codes, missing required fields (code, http_status, category, title, description, resolution), malformed code format, missing bilingual title/description/resolution. Previously only warned.
- **Op-48 Version compatibility matrix** — `ion.yaml` now declares `x-ion-compatibility` with pinned versions for Beckn core, all schema packs, all policy categories, error registry, and all spine versions. Also documents the single-version-running policy with 90-day upgrade notice period.

### New error codes

| Code | Title |
|---|---|
| ION-2003 | Seller KYC expired or suspended |
| ION-2004 | Listing suspended — counterfeit flag under investigation |
| ION-2005 | Category license missing or expired |
| ION-3020 | Invalid variant matrix combination |
| ION-3021 | Payment schedule milestone failed or overdue |
| ION-5010 | Age verification failed at delivery |
| ION-5011 | Data residency violation |
| ION-6004 | Batch reconcile contract detail mismatch |
| ION-6005 | Parent reconId not found for adjustment |
| ION-6006 | Tax withholding evidence missing |
| ION-6007 | Clawback attempted past adjustment window |

### Migration guide

**For BPPs:**
- Remove `cancellable`, `cancellationFee`, `cancellationFeeApplicableStates`, `returnWindow`, `returnAllowedReasons`, `isAvailable`, `gift`, `invoiceTypeExtended` from existing catalog payloads. Set `cancellationPolicy` and `returnPolicy` to the correct ratified IRI instead.
- If your return policies charged different timelines per payment method, confirm your policy IRI matches the per-method schedule in the ratified document. If not, request ION Council to ratify a new return policy variant.
- Add `kycStatus`, `kycLevel`, `kycValidUntil` to provider payloads — REQUIRED in v0.5.
- For age-restricted items, populate `performance.ageVerification*` fields at DELIVERED state.
- For pharmacy and regulated categories, add `resource.dataResidency: DOMESTIC_ONLY` and `provider.categoryLicenses[]`.

**For BAPs:**
- Update UI to render `offer.priceChangeSchedule[]` as countdown.
- Implement tiered payment eligibility filtering (check buyer tier + amount + address verification against each `paymentMethodEligibility` entry).
- For `resource.variantMatrix`, render multi-axis selection UI and compute final price via declared calculation mode.
- Handle new error codes ION-2003/2004/2005/3020/3021/5010/5011/6004/6005/6006/6007.

**For reconcile/settlement:**
- Adopt `isBatch=true` for daily/weekly settlement runs.
- Include `taxWithholdings[]` with NTPN references for Mall-tier sellers.
- Adjustments against prior reconciles require `parentReconId` + `adjustmentType` + reason/evidence.

---

## v0.4.0-draft (April 2026)

**Theme: Policy Terms Registry — static terms for return, cancellation, warranty, dispute, grievance SLA, payment terms, and penalties.**

Introduces a machine-enforceable policy model. Sellers no longer author policy prose — they declare IRIs that resolve to ratified terms documents. ION Central enforces the structured terms at every API boundary from catalog publish through reconcile.

### New: Policy Terms Registry

New top-level directory `/policies/` with 7 categories and **67 ratified policy documents**:

| Category | Count | Purpose |
|---|---|---|
| RETURN | 15 | Return window, reasons, evidence requirements, QC outcomes, refund timeline |
| CANCELLATION | 10 | Cancellation window, fee structure, reasons, refund percentages |
| WARRANTY | 8 | Warranty type, duration, coverage scope, service mode |
| DISPUTE | 5 | BPSK, BANI, ODR, UNCITRAL, LKPP — jurisdictions and escalation paths |
| GRIEVANCE_SLA | 4 | First response and resolution SLAs, auto-escalation, penalty references |
| PAYMENT_TERMS | 8 | Upfront, deposit+balance, COD, NET7/30/60 credit, installment, subscription autopay |
| PENALTY | 17 | Seller SLA breach (Standard/Mall/Premium tiers), late dispatch, wrong item, cancel without cause, RTO seller fault; buyer restocking, failed delivery, COD refusal, chargeback abuse; marketplace escalation miss; creator misleading claims, counterfeit products |

### New schema fields on `offerAttributes`

- `grievanceSlaPolicy` — **mandatory** IRI pointing to Grievance SLA terms
- `paymentTermsPolicy` — **mandatory** IRI pointing to Payment Terms terms
- `penaltyPolicy` — optional explicit override (normally auto-derived from tier)
- `customTermsAddendum` — optional free text up to 1000 chars for edge cases

Expanded enums for existing IRI fields:
- `returnPolicy`: 5 → 15 ratified values
- `cancellationPolicy`: 3 → 10 ratified values
- `warrantyPolicy`: 5 → 8 ratified values
- `disputePolicy`: 3 → 5 ratified values

### New error codes

| Code | Title |
|---|---|
| ION-2010 | Invalid policy IRI at catalog publish |
| ION-2011 | Policy IRI deprecated |
| ION-5008 | Action not permitted by declared policy |
| ION-5009 | SLA violated - auto escalation triggered |
| ION-6003 | Penalty settlement applied (informational) |

### Enforcement model

**At catalog publish:** Every policy IRI validated against `policies/registry.json`. Unknown IRIs rejected with ION-2010. Deprecated IRIs rejected with ION-2011 and supersededBy returned.

**At runtime:** Every action checked against the declared policy's terms document. Cancellations outside window → ION-5001. Return reasons not in allowed list → ION-5002. Returns outside window → ION-5004. Any action not permitted by the declared policy → ION-5008.

**At grievance SLA:** ION Central timer auto-escalates on SLA breach per the policy's `escalationLevels` list. Penalty policies fire automatically at reconcile — no manual action needed.

**At reconcile:** Penalty deductions applied per linked penalty IRI. ION-6003 informational code surfaces the deduction reason.

### Versioning model

Single registry version active at any time. Council ratifies new version with **90 days notice**. On cutover date, all catalog entries auto-upgrade. No per-seller version pinning — it does not scale.

### Spine profile changes

Every spine's `profile.json` now declares `requiredPolicyCategories`:

- B2C-SF: all 6 categories
- B2C-MTO: 4 (cancellation + dispute + grievance + payment-terms)
- B2C-SUB: 5 (no returns)
- B2C-LIVE: all 6
- B2C-DIG: 4 (cancellation + dispute + grievance + payment-terms — no returns or warranty)
- B2B-PP / B2B-CR / MP-IH / MP-IL / AUC-R / XB / B2G: all 6
- AUC-F: 5 (no warranty — auction model)

### New resolver API

Added to ION network profile `ion.yaml`:
- `GET /policies/{iri}` — resolve a policy IRI to its full terms document
- `GET /policies?category=RETURN` — list/filter registry

### Penalty tier system

Sellers onboarded into Standard / Mall / Premium tiers. Each tier has a minimum penalty commitment. Tier-specific penalty IRIs:
- `penalty.seller.sla_breach.standard` (5-25% depending on severity)
- `penalty.seller.sla_breach.mall` (5-30%, stricter)
- `penalty.seller.sla_breach.premium` (10-40%, strictest)

Sellers cannot opt out of their tier's penalty minimum.

### Documentation

- New `policies/README.md` explaining the registry model
- New `Sector A Trade doc § 7b Policies and penalties` — complete developer-facing explanation
- New `Developer Orientation § 12 Policy Terms Resolution` — lifecycle walkthrough
- Each policy YAML includes `displayText.id` and `displayText.en` for BAP rendering, regulatory basis, applicability, and lifecycle metadata (supersededBy, deprecatedAt)

---

## v0.3.0-draft (April 2026)

**Theme: Marketplace-grade mechanics and new commerce surfaces.**

Based on critical review from Amazon Indonesia / Tokopedia / Shopee implementation perspective. Adds production-grade fields and flows needed to run the three largest Indonesian marketplaces on ION.

### New spines

- **B2C-LIVE** — Live / OTT / social commerce. Covers Shopee Live, Tokopedia Play, TikTok Shop-style sessions, OTT-embedded shoppable content (Vidio, Netflix, Disney+ Hotstar in-video commerce where watching a movie or match surfaces products for purchase), short-form video commerce, affiliate links, and group-buy mechanics. Includes streamer/affiliate commission handling.
- **B2C-DIG** — Digital goods. Covers pulsa, mobile data packages, PLN electricity tokens, utility bill payments (water, PDAM, internet, BPJS), gift cards, game currencies (Mobile Legends, Free Fire, Valorant, Genshin), streaming service vouchers (Netflix, Disney+ Hotstar, Spotify), e-wallet top-ups. New `digital` performance state machine: PENDING_OPERATOR → DELIVERED or DELIVERY_FAILED.

### New schema fields — CRITICAL gaps (from marketplace review C1-C6)

- **Stock reservation** (`offer.reservationWindowSeconds`) — documented soft/hard reservation window. Errors ION-3013 (window expired) and ION-3014 (sold out during transaction).
- **Flash sale mechanics** (`offer.totalStockCap`, `offer.perUserQuantityCap`, `offer.isFlashSale`, `offer.queueEnabled`, `offer.queuePosition`, `offer.estimatedWaitSeconds`) — error ION-3015 for cap reached.
- **Voucher stacking** (`offer.stackingGroup`, `offer.stackingRules`) — replaces simple `stackable` boolean. New breakup types: `PLATFORM_VOUCHER`, `SELLER_VOUCHER`, `PAYMENT_VOUCHER`, `SHIPPING_VOUCHER`, `CASHBACK_VOUCHER`, `BRAND_VOUCHER`. Error ION-3019.
- **Buy Box / canonical product** (`resource.canonicalId`, `resource.featuredOfferEligible`, `resource.featuredOfferScore`) — enables cross-provider selection.
- **COD pre-verification** (`offer.codEligibilityForBuyer`, `offer.codEligibilityReason`) — error ION-3016 for buyer-specific decline.
- **Shipping insurance** (`performance.shippingInsurance` structured object) — mandatory for items >IDR 5M.

### New schema fields — HIGH gaps (H1-H6)

- **Returns extensions**: `returnEvidenceRequirement` enum, `partial-return` sub-branch, `qcResult` enum (QC_PASSED, QC_FAILED_TAMPERED, QC_FAILED_MISSING_PARTS, QC_FAILED_DIFFERENT_ITEM, QC_FAILED_USED_DAMAGED, QC_PARTIAL, QC_PENDING), `qcNotes`, `qcEvidence[]`, new `return-qc-resolution` sub-branch. Errors ION-5005 (evidence insufficient) and ION-5006 (QC failed).
- **Live commerce context** (`contract.liveCommerceContext` — sourceChannel, liveSessionId, streamerId, ottPlatform, ottContentId, ottTimestampSeconds, groupBuyId). Error ION-3017 (live session ended).
- **Digital goods** (`resource.digital` sub-object with digitalCategory, operatorOrIssuer, denomination, deliveryMethod, target, redemptionCode, refundable). Error ION-3018 (target invalid).
- **Marketplace-managed logistics** (`provider.preferredLogisticsProvider`, `provider.marketplaceManagedLogistics`, `performance.marketplaceManagedLogistics`) — distinguishes BAP-orchestrated from BPP-orchestrated on-network LSP.
- **Expanded cancellation reasons**: added PAYMENT_METHOD_CHANGE, ORDERED_WRONG_VARIANT, SELLER_UNRESPONSIVE, ITEM_NO_LONGER_NEEDED, BUYER_FRAUD_SUSPECTED, QUALITY_ISSUE_AT_PREVIEW.
- **Expanded return reasons**: added QUALITY_ISSUE, SIZE_MISMATCH, COLOR_MISMATCH, PERFORMANCE_NOT_AS_EXPECTED, AUTHENTICITY_DOUBT.
- **Refund destination** (`contract.refundDestination` structured: ORIGINAL_PAYMENT_METHOD, PLATFORM_WALLET, BANK_TRANSFER, LOYALTY_POINTS, STORE_CREDIT, VOUCHER).

### New schema fields — MEDIUM gaps (M1-M9)

- **Address extensions**: `postalCode` (Indonesian kodepos), `addressType` enum including BOARDING_HOUSE (kost), `receiverInstructions`, `gpsAccuracyMeters`, `landmark`, `blockUnit`.
- **Agent verification**: `performance.agentId`, `agentVehicleType`, `agentPlateNumber`, `agentBadgeNumber`, `liveAgentLocationUrl`.
- **Subscription extensions**: `subscriptionTrialDays`, `subscriptionPauseType`, `subscriptionPauseUntil`.
- **Gift details**: `contract.giftingDetails` structured object with recipientName, recipientPhone, giftMessage, hideSenderInfo, priceDisplayOnPackage.
- **Payment providers**: added ISAKU, FLIP, ALLOBANK, SEABANK_WALLET, BLU, LIVIN (e-wallets); TRAVELOKA_PAYLATER, HOME_CREDIT, UANGME, AKULAKU_PAYLATER (BNPL).
- **Dispute escalation** (`support.escalationLevel` enum: SELLER, MARKETPLACE_MEDIATION, BPSK, KOMINFO, ION_NETWORK): plus `escalationTimestamp`, `escalationSlaHours`, `bpskReference`, `kominfoReference`.
- **Invoice type extended** (`contract.invoiceTypeExtended`): added SURAT_TAGIHAN (PKP→non-PKP) and KOMERSIAL_INVOICE (bilingual).
- **Rating extensions**: `ratingSubCategory`, `ratingImages[]`, `ratingVideos[]`, `verifiedPurchase`, `helpfulCount`, `sellerResponse`.
- **SLA penalty** (`performance.slaBreachCount`, `slaBreachDetails[]`, `reconcile.slaPenaltyDeduction`, `slaPenaltyBreakdown[]`). Error ION-5007 (SLA penalty applied). Streamer/affiliate commission in reconcile.

### New schema fields — LOW gaps (L1-L7)

- **Handling time** (`offer.handlingTimeHours`) for non-QSR sellers (custom-print, made-to-measure).
- **Sub-national origin** (`resource.regionOfOrigin` ISO 3166-2, `geographicIndicationCert`) for Kopi Gayo / Beras Cianjur GI products.
- **Image roles** (`resource.imageSet[]` with role enum) — PRIMARY, GALLERY, SIZE_CHART, LIFESTYLE, UNBOXING, NUTRITION_FACTS, etc.
- **Videos** (`resource.videos[]` with role).
- **Bundle composition** (`resource.bundleComposition[]`) for bundle SKUs.
- **Structured brand** (`resource.brandIdentity`) for Official Store / Brand Registry programmes.

### Error registry additions

| Code | Title |
|---|---|
| ION-3013 | Item reservation window expired |
| ION-3014 | Item sold out during transaction |
| ION-3015 | Offer total stock cap reached |
| ION-3016 | COD not eligible for this buyer |
| ION-3017 | Live session ended |
| ION-3018 | Digital target invalid or inactive |
| ION-3019 | Voucher stacking not permitted |
| ION-5005 | Return evidence insufficient |
| ION-5006 | Return QC failed |
| ION-5007 | SLA breach — penalty applied |

### State machines

- New `digital` state machine for B2C-DIG.

---

## v0.2.0-draft (April 2026)

### Architecture

- Repository restructured from individual example YAML files (A01–A07) into a layered `schema/` + `flows/` + `errors/` architecture
- `beckn.yaml` no longer copied — referenced externally from Beckn Foundation repository
- `ion.yaml` added as ION network profile overlay on top of Beckn v2.0.0
- Schema extensions reorganised into `core/` (cross-sector) and `trade/` (sector-specific)
- Flow specs restructured into `spines/` (happy path) + `branches/` (conditional sub-flows)
- Error registry restructured into category YAML files with generated `registry.json`

### Schema packs added

**Core packs (10)** — cross-sector, apply to every ION sector:

| Pack | Version | Key additions |
|---|---|---|
| `core/address/v1` | 1.0.0 | provinsiCode (34 BPS provinces), kabupatenCode, kelurahan, kecamatan, RT, RW |
| `core/identity/v1` | 1.0.0 | npwp (16-digit post-2024 format), nib, nikNumber, pkpStatus, legalEntityName, businessType |
| `core/payment/v1` | 1.0.0 | PaymentDeclaration wrapper, QRIS, VirtualAccount, EWallet (10 providers), COD, BankTransfer, BISettlement, BNPL, CardPayment |
| `core/tax/v1` | 1.0.0 | taxRegime (PPN/PPnBM/PPh22/PPh23/EXEMPT), taxCategory (BKP/JKP/NON_BKP), taxRate, taxAmount, eFakturRef |
| `core/localization/v1` | 1.0.0 | LocalisedText pattern — language objects keyed by ISO 639-1 |
| `core/product/v1` | 1.0.0 | halalStatus, halalCertNumber, bpomRegNumber, sniCertNumber, spPIRTNumber, ageRestricted, minAge |
| `core/support/v1` | 1.0.0 | IONSupportTicket — consumer complaint: category, complainantInfo, issueActions, resolution |
| `core/raise/v1` | 1.0.0 | IONTicket — NP-to-NP and NP-to-ION ticketing: type, priority, thread, SLA |
| `core/rating/v1` | 1.0.0 | ratingCategory (PROVIDER/ITEM/FULFILLMENT/AGENT), ratingValue 1-5, feedbackText, feedbackUrl |
| `core/reconcile/v1` | 1.0.0 | reconId, amounts (baseContractAmount, finderFee, withholding), adjustments[], recon_status (01/02/03) |

**Trade packs (7 + states)** — Trade sector (Sector A):

| Pack | Version | Key additions |
|---|---|---|
| `trade/provider/v1` | 1.0.0 | storeStatus, operatingHours, holidayCalendar, serviceabilityByCategory, averagePreparationTime, providerCategory (17 values), nibRegistered, invoicingModel |
| `trade/resource/v1` | 1.0.0 | Full product model: resourceType (PLAIN/VARIANT/WITH_EXTRAS/COMPOSED), availability signal (no stock count), category sub-objects for food/fashion/electronics/beauty/agritech/pharmacy/packaged/regulatory/installation/warranty/usage |
| `trade/offer/v1` | 1.0.0 | Policy IRIs (return/cancel/warranty/dispute), cancellationFee, returnAllowedReasons, cancellationAllowedReasons, MOQ, weightSlabs, promotions (offerType, subsidyBreakup, stackable) |
| `trade/consideration/v1` | 1.0.0 | breakupLineType (15 types including PPNBM, LOYALTY_REDEEM, FINANCE_CHARGE, PLATFORM_FEE), ppnRate, ppnbmRate, discountType |
| `trade/performance/v1` | 1.0.0 | performanceMode, sla, handling, readyToShip, awbNumber, agentName/Phone/Photo, deliveryOtp, deliveryProofUrl, installationScheduling, realTimeGps, lspSubscriberId |
| `trade/contract/v1` | 1.0.0 | fulfillingLocationId, invoicePreferences, fakturPajakReference, purchaseOrderReference, quoteTrail[], creditTermsDays, subscriptionBillingCycle, beaCukaiReference |
| `trade/commitment/v1` | 1.0.0 | lineId, resourceId, offerId, quantity, price (locked at on_select), customisationSelections, specialInstructions |
| `trade/performance-states/v1` | 1.0.0 | 6 canonical state machines: standard, mto, self_pickup, return, replacement, rto |

### Flows added

**11 spines:**
B2C-SF (reference), B2C-MTO (complete — MTO state machine, preparation window, cancellation boundary), B2C-SUB, B2B-PP, B2B-CR, MP-IH, MP-IL, AUC-F, AUC-R, XB, B2G

**6 branch files with complete sub-branch definitions:**

| Branch file | Sub-branches |
|---|---|
| `during-transaction` | 10: fulfillment-type, payment-prepaid-BAP-collected, payment-prepaid-BPP-collected, payment-COD-BAP-collected, payment-COD-BPP-collected, multi-fulfillment, cancellation-terms, on-network-LSP, technical-cancellation-confirm-failure-BAP (999), technical-cancellation-confirm-failure-BPP (998) |
| `cancellation` | 4: cancel-full-buyer, cancel-full-seller, cancel-partial-fulfillment, technical-cancellation-force |
| `returns` | 6: return-initiated, return-picked-up, return-delivered, replacement, exchange, cancel-return-request |
| `RTO` | 4: RTO-initiated, RTO-delivered, RTO-disposed, RTO-reattempt |
| `updates` | 7: fulfillment-delay, update-delivery-address, update-delivery-authorization, buyer-instructions, update-sale-invoice, price-adjustment, ready-to-ship |
| `cross-cutting` | 5: track, support, rating, reconcile, raise (participant→ION channel) |

### Error registry

30 errors across 9 category files (ION-1xxx through ION-9xxx). All entries bilingual (id + en) with `resolution.en` guidance.

### Breaking changes from v0.1

- YAML filenames: `A01_B2C_MTO_FoodQSR.yaml` → `flows/trade/spines/B2C-SF/v1/spine.yaml` etc.
- Field `_field_roles` dictionaries: replaced by `x-ion-mandatory` / `x-ion-condition` / `x-ion-regulatory` annotations on each field in `attributes.yaml`
- Example payloads: moved from inline YAML to `examples/` directories (content TBA)
- API terminology: `on_rate` → `on_rate` (Beckn canonical name)
- Stock count: removed — availability signal only (`IN_STOCK / LOW_STOCK / OUT_OF_STOCK / PREORDER / DISCONTINUED`)

---

## v0.1.0-draft (April 2026)

- Initial release
- 6 example specs (A01-A07) covering B2C-SF and B2C-MTO patterns
- Trade sector dictionary v1.0 (ION_Trade_Dictionary.xlsx)
- Error registry v1 (ion_error_registry.json)
