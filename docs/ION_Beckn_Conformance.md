# Beckn 2.0.0 Conformance and ION Extensions

This document specifies exactly how ION relates to the Beckn 2.0.0 protocol. It distinguishes:

1. **Beckn 2.0.0 native surface** — what we use as-is from Beckn 2.0.0 core
2. **ION protocol extensions** — endpoints ION adds beyond Beckn 2.0.0 core
3. **ION schema extensions** — sector attribute packs via Beckn's native `*Attributes` slots

Any implementation conforming to Beckn 2.0.0 and ION must implement both the native surface and the ION extensions. An implementation conforming to Beckn 2.0.0 alone (30 endpoints) is Beckn-conformant but not ION-conformant.

This doc is the full conformance checklist. For the bigger-picture five-layer model, see `ION_Layer_Model.md`.

---

## 1. Beckn 2.0.0 native endpoints used by ION (30)

All 30 Beckn 2.0.0 endpoints are in scope:

### Transaction flow
`/discover`, `/on_discover`, `/select`, `/on_select`, `/init`, `/on_init`, `/confirm`, `/on_confirm`, `/status`, `/on_status`, `/track`, `/on_track`, `/update`, `/on_update`, `/cancel`, `/on_cancel`, `/rate`, `/on_rate`, `/support`, `/on_support`

### Catalog
`/catalog/publish`, `/catalog/on_publish`, `/catalog/subscription`, `/catalog/subscriptions`, `/catalog/subscription/{subscriptionId}`, `/catalog/pull`, `/catalog/pull/result/{requestId}/{filename}`, `/catalog/master/search`, `/catalog/master/schemaTypes`, `/catalog/master/{masterItemId}`

---

## 2. ION protocol endpoint extensions (8)

These endpoints are ION-specific and NOT in Beckn 2.0.0 core. They are specified in `schema/core/v2/api/v2.0.0/ion-endpoints.yaml`.

### `/raise` family — network dispute adjudication (6 endpoints)

| Endpoint | Purpose |
|---|---|
| `/raise` | BAP or BPP submits a commercial dispute to ION Gateway |
| `/on_raise` | ION Gateway returns ticket ID and timeline |
| `/raise_status` | Poll ticket status |
| `/on_raise_status` | Current ticket status and stage |
| `/raise_details` | Request full ticket thread |
| `/on_raise_details` | Full thread with messages and evidence |

**Rationale for extension:** Beckn 2.0 has no network-adjudication primitive. `/support` is for bilateral customer care only. Commercial dispute escalation to a network operator requires ION-specific protocol support. This pattern mirrors ONDC's grievance / dispute / issue resolution flow but is architected specifically for the ION governance model.

**When `/raise` is used instead of `/support`:**
- Bilateral resolution via `/update` has exceeded policy SLA
- Either party invokes network adjudication with the applicable policy IRI as the resolution basis
- ION Central (network operator) reads the contract's `/update` history and adjudicates

### `/reconcile` — settlement reconciliation (2 endpoints)

| Endpoint | Purpose |
|---|---|
| `/reconcile` | BAP initiates financial settlement reconciliation |
| `/on_reconcile` | BPP returns reconciliation result (AGREED / DISPUTED / PENDING_ADJUSTMENT) |

**Rationale for extension:** Beckn 2.0 has no dedicated reconciliation endpoint. Settlement state transitions (DRAFT → COMMITTED → COMPLETE) can be driven via `/update`, but ION networks require a standardised reconciliation step for regulatory audit, tax reporting (PPN, PPh 23), and FWA rebate calculations. The dedicated `/reconcile` endpoint provides a clear semantic boundary and simplifies compliance workflows.

**ION extension of `context.try`:** Beckn 2.0 defines `context.try=true` for `/update`, `/cancel`, `/rate`, and `/support`. ION extends this to `/reconcile` for settlement preview without committing.

---

## 3. ION schema extensions (via Beckn-native `Attributes` slots)

All ION schema extensions use the native Beckn 2.0.0 extension mechanism — the `Attributes` slot on core schemas. No invented extension mechanisms. These packs are split into **Layer 4** (cross-sector, in `schema/extensions/core/`) and **Layer 5** (sector-specific, in `schema/extensions/{sector}/`).

### Layer 4 — ION core packs (every sector)

| Extension schema | Beckn slot | Path |
|---|---|---|
| `IONAddressSubdivisions` | *(reusable shape — embedded inside `participantAttributes.addressDetail`, `providerAttributes.availableAt[*].ionSubdivisions`, `performanceAttributes.stops[*].location.ionSubdivisions`)* | `schema/extensions/core/address/v1/` |
| `IONBusinessIdentity` | (mountable on multiple slots) | `schema/extensions/core/identity/v1/` |
| `IONLocalizationAttributes` | various | `schema/extensions/core/localization/v1/` |
| `IONParticipantAttributes` | `Participant.participantAttributes` | `schema/extensions/core/participant/v1/` |
| `PaymentDeclaration` | `Settlement.settlementAttributes` | `schema/extensions/core/payment/v1/` |
| `ProductCertifications` | `Resource.resourceAttributes` | `schema/extensions/core/product/v1/` |
| `IONRaiseAttributes` | raise message payloads | `schema/extensions/core/raise/v1/` |
| `IONRatingAttributes` | `RatingInput.target.targetAttributes` | `schema/extensions/core/rating/v1/` |
| `IONReconcileAttributes` | `Settlement.settlementAttributes` | `schema/extensions/core/reconcile/v1/` |
| `IONSupportTicket` | `Support.channels[*]` (as an `Attributes` entry with `@type=ion:SupportTicket`) | `schema/extensions/core/support/v1/` |
| `IONTaxDetail` | `Consideration.considerationAttributes`, `Contract.contractAttributes` | `schema/extensions/core/tax/v1/` |

### Layer 5 — Trade sector packs

| Extension schema | Beckn slot | Path |
|---|---|---|
| `TradeProviderAttributes` | `Provider.providerAttributes` | `schema/extensions/trade/provider/v1/` |
| `TradeOfferAttributes` | `Offer.offerAttributes` | `schema/extensions/trade/offer/v1/` |
| `TradeResourceAttributes` | `Resource.resourceAttributes` | `schema/extensions/trade/resource/v1/` |
| `TradeCommitmentAttributes` | `Commitment.commitmentAttributes` | `schema/extensions/trade/commitment/v1/` |
| `TradeConsiderationAttributes` | `Consideration.considerationAttributes` | `schema/extensions/trade/consideration/v1/` |
| `TradePerformanceAttributes` | `Performance.performanceAttributes` | `schema/extensions/trade/performance/v1/` |
| `TradeContractAttributes` | `Contract.contractAttributes` | `schema/extensions/trade/contract/v1/` |
| `TradePerformanceStates` | (canonical enum) | `schema/extensions/trade/performance-states/v1/` |

### Layer 5 — Logistics sector packs

| Extension schema | Beckn slot | Path |
|---|---|---|
| `LogisticsProviderAttributes` | `Provider.providerAttributes` | `schema/extensions/logistics/provider/v1/` |
| `LogisticsOfferAttributes` | `Offer.offerAttributes` | `schema/extensions/logistics/offer/v1/` |
| `LogisticsResourceAttributes` | `Resource.resourceAttributes` | `schema/extensions/logistics/resource/v1/` |
| `LogisticsCommitmentAttributes` | `Commitment.commitmentAttributes` | `schema/extensions/logistics/commitment/v1/` |
| `LogisticsConsiderationAttributes` | `Consideration.considerationAttributes` | `schema/extensions/logistics/consideration/v1/` |
| `LogisticsPerformanceAttributes` | `Performance.performanceAttributes` | `schema/extensions/logistics/performance/v1/` |
| `LogisticsContractAttributes` | `Contract.contractAttributes` | `schema/extensions/logistics/contract/v1/` |
| `LogisticsTrackingAttributes` | `Tracking.trackingAttributes` | `schema/extensions/logistics/tracking/v1/` |
| `LogisticsParticipantAddendum` | `Participant.participantAttributes` (alongside `IONParticipantAttributes`) | `schema/extensions/logistics/participant-logistics/v1/` |
| `LogisticsPerformanceStates` | (canonical enum) | `schema/extensions/logistics/performance-states/v1/` |

Every extension pack carries:
- `@context` pointing to its JSON-LD context document
- `@type` declaring the extension class IRI
- All properties namespaced under the `ion:` JSON-LD prefix
- `x-beckn-attaches-to` annotation naming the exact Beckn slot it mounts on — this is the extension contract

---

## 4. Address handling — attach to Participant, not Address

Beckn 2.0.0's `Address` schema is strict — `additionalProperties: false` and no `addressAttributes` slot. Indonesian administrative hierarchy (provinsi / kabupaten / kecamatan / kelurahan / RT / RW / patokan) therefore attaches to **`Participant.participantAttributes`** via `IONParticipantAttributes.addressDetail` (defined in `core/participant/v1`).

Each participant that has a physical location (BUYER, SELLER, CONSIGNOR, CONSIGNEE, MERCHANT, WAREHOUSE, AGENT) carries its full Indonesian address detail inside its participant attributes. The Beckn-native `Address` fields (streetAddress, addressLocality, postalCode) remain as the standard postal address.

Example (same shape for trade or logistics — the core/participant pack is sector-neutral):
```yaml
participants:
  - role: CONSIGNEE
    id: "buyer-a1b2c3"
    participantAttributes:
      "@context": "https://schema.ion.id/core/participant/v1/context.jsonld"
      "@type": "ion:ParticipantAttributes"
      role: CONSIGNEE
      addressDetail:
        # Beckn-native fields (on the beckn:Address object next to this participant)
        # streetAddress: "Jl. Gatot Subroto 45"
        # addressLocality: "Jakarta Selatan"
        # postalCode: "12190"
        # addressCountry: "ID"
        # ION core/participant extension fields
        provinsiCode: "31"
        kabupatenCode: "3174"
        kecamatanCode: "3174010"
        kelurahanCode: "3174010001"
        rt: "005"
        rw: "002"
        patokan: "Seberang Masjid Al-Ikhlas"
```

---

## 5. Key Beckn 2.0.0 usage patterns

### JSON-LD
Every extension `Attributes` block MUST carry `@context` and `@type`. Per Beckn 2.0.0 `Attributes` schema, both are required.

### Context schema
`context.version` MUST match the Beckn core version in force — for v0.5.2 of this ION profile that is `"2.0.0"` (matches Beckn `Context.version` `const: "2.0.0"`). The upstream Beckn target is `core-v2.0.0-rc1`. See `x-ion-compatibility.becknCore` in `schema/core/v2/api/v2.0.0/ion.yaml`.

### Contract / Commitment / Settlement status enums — three different enums

Beckn 2.0.0 defines three distinct status enums at three different levels. They are NOT identical — implementers must NOT conflate them.

| Level | Where | Enum values | Count |
|---|---|---|---|
| `Contract.status.descriptor.code` | `Contract.status` | `DRAFT`, `ACTIVE`, `CANCELLED`, `COMPLETE` | 4 |
| `Commitment.status.descriptor.code` | each `Contract.commitments[*].status` | `DRAFT`, `ACTIVE`, `CLOSED` | 3 |
| `Settlement.status.descriptor.code` | each `Settlement.status` | `DRAFT`, `COMMITTED`, `COMPLETE` | 3 |

**Contract.status** is the rollup for the transaction. Progresses DRAFT (at `/init`) → ACTIVE (at `/confirm`) → COMPLETE (on fulfilment close) or CANCELLED (on cancel).

**Commitment.status** is per-line-item. Uses `CLOSED` rather than `CANCELLED`/`COMPLETE` — a single committed line closes when either the goods/service is delivered or the commitment is withdrawn. A commitment does NOT distinguish CANCELLED from COMPLETE — that distinction lives at the contract level.

**Settlement.status** is per-settlement-object. Moves DRAFT → COMMITTED at `/reconcile` agreement; COMMITTED → COMPLETE on fund transfer confirmation.

**Performance.status** is open-ended — Beckn types it as a `Descriptor`, not an enum. ION's spine-specific state codes (`PICKED_UP`, `OUT_FOR_DELIVERY`, `RIDER_ASSIGNED`, etc.) go inside `Performance.status.descriptor.code` and are free-form per ION's state machine definitions. The rollup from `Performance.status` to `Contract.status` is an ION convention, not a Beckn rule — see `schema/extensions/logistics/performance-states/v1/states.yaml` for the state machines and their contract-status rollup rules.

### Commitments required
`Contract.commitments[]` is required with `minItems: 1`. Every transaction must carry at least one commitment.

### Commitment.resources[*].quantity is required
Beckn 2.0.0 defines `Commitment.resources[*]` with required properties `[id, quantity]`. `Resource` itself does NOT define `quantity` — it lives in `resourceAttributes`. ION sector resource packs (`trade/resource/v1`, `logistics/resource/v1`) therefore include a mandatory `quantity` field with a unit of measure.

### Settlement states
Beckn 2.0.0 `Settlement.status` has 3 values: `DRAFT`, `COMMITTED`, `COMPLETE`. Reconciliation via `/reconcile` moves DRAFT → COMMITTED; funds transfer moves COMMITTED → COMPLETE.

### context.try
Beckn 2.0.0 defines on: `/update`, `/cancel`, `/rate`, `/support` (four actions).
ION adds on: `/reconcile` (ION extension).

### Signatures
HTTP `Authorization` header MUST carry the Beckn 2.0 Signature scheme with `keyId` in the format `{subscriberId}|{uniqueKeyId}|{algorithm}` — pipe-separated triple. Algorithm MUST be `ed25519`. Every `Ack` response body MUST carry a `CounterSignature` (see Beckn 2.0 `CounterSignature` schema).

### Registry
Network participants register on `dedi.global` per Beckn 2.0.0 convention. ION operates as a namespace on dedi.global (e.g. `ion.id/{sector}@dedi.global` where `{sector}` is `trade`, `logistics`, etc). Network IDs follow `{namespace_id}/{registry_id}@{dedi-host}`.

### Offer targeting
Enterprise / FWA-targeted offers use Beckn's native `Offer.availableTo[]` with `{type: PARTICIPANT, id: "buyer-platform.co.id"}` for visibility constraints. The FWA policy IRI governs commercial terms; the availability constraint uses Beckn-native fields.

### Catalog discovery
BAPs may use either:
- **Active query** — `/discover` with `DiscoverAction.intent` → `/on_discover` callback
- **Subscription** — `/catalog/subscription` for push-based updates

Beckn 2.0.0 supports both; ION recommends BPPs support both.

---

## 6. What a conformance test checks

1. All 30 Beckn 2.0.0 endpoints reachable and pass the Beckn schema test suite
2. All 8 ION extension endpoints (6 raise + 2 reconcile) reachable and pass the ION extension test suite
3. Every request carries a valid `Authorization` signature with correct keyId format
4. Every `Ack` response body carries a valid `CounterSignature`
5. `context.version == "2.0.0"` in every message
6. Every extension `Attributes` payload carries `@context` and `@type`
7. Contract examples have at least one commitment (`minItems: 1`)
8. `Contract.status.descriptor.code` uses only `{DRAFT, ACTIVE, CANCELLED, COMPLETE}` (4 values)
9. `Commitment.status.descriptor.code` uses only `{DRAFT, ACTIVE, CLOSED}` (3 values — **distinct from Contract**)
10. `Settlement.status.descriptor.code` uses only `{DRAFT, COMMITTED, COMPLETE}` (3 values)
11. Every `Commitment.resources[*]` entry carries both `id` and `quantity` (quantity lives in `resourceAttributes`)
12. Wire digest token is `BLAKE-512=...` (NOT `BLAKE2b-512=...`) — algorithm is BLAKE2b-512, wire name differs
13. `context.try=true` supported on update, cancel, rate, support, reconcile
14. No use of deprecated Beckn elements (e.g. `publishDirectives`)
15. All ION extension packs (L4 core and L5 sector) attach to the correct Beckn slots (`x-beckn-attaches-to` annotation matches slot-on-wire)

The `tools/validate.py` checker enforces items 5–15 statically; items 1–4 require runtime conformance testing.

---

## See also

- **New to ION?** [`ION_Start_Here.md`](ION_Start_Here.md)
- **Glossary?** [`ION_Glossary.md`](ION_Glossary.md)
- **Layer model?** [`ION_Layer_Model.md`](ION_Layer_Model.md)
- **Onboarding and signing?** [`ION_Onboarding_and_Auth.md`](ION_Onboarding_and_Auth.md)
- **See it in action?** [`ION_First_Transaction.md`](ION_First_Transaction.md)
