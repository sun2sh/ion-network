# ION — Developer Orientation

Everything you need to understand before writing a single line of ION integration code. Read this first regardless of which sector you are building for. It covers the cross-sector concepts — BAP/BPP, two-phase architecture, ONIX, Atlas, spine/branch composition, mandatory actions, Indonesian regulatory requirements, policy resolution, signing, and error handling.

After this, read your sector doc: [`ION_Sector_A_Trade.md`](ION_Sector_A_Trade.md) or [`ION_Sector_B_Logistics.md`](ION_Sector_B_Logistics.md).

It also explains ION Atlas — the schema registry and developer tooling that supports you throughout the build, not just at the end.

---

## 1. What ION is — and what it is not

ION is a network, not a platform. It defines the rules and data structures that allow any buyer app and any seller app to transact with each other without bilateral integration.

There is no ION central server processing transactions. There is no ION database holding orders. ION provides a **registry** (participant identities and public keys), a **catalogue service** (seller catalog distribution), and a **specification** (this repository) that defines what every API call must contain.

The transaction itself happens directly between the buyer app (BAP) and the seller app (BPP). ION infrastructure is only in the path for Phase 1 (catalog distribution). From `/select` onwards, BAP talks directly to BPP.

---

## 2. The two participants

**BAP — Buyer App Platform.** The consumer-facing app. Sends select/init/confirm to BPP, receives status callbacks, handles all consumer-facing UI.

**BPP — Buyer Price Provider.** The seller's system. Manages inventory, pricing, and fulfillment. Publishes catalog; responds to BAP API calls.

Both register on ION with: a subscriber ID, an Ed25519 public key for signature verification, and a callback endpoint URL. Every API call is signed and verified against the registry.

---

## 3. The two phases of every transaction

### Phase 1 — Catalog (async)

```
BPP → /publish_catalog → ION Catalogue Service
                                 ↓
                    ION Discover Service → /on_discover → BAP
```

BPP publishes to the Catalogue Service. BAPs subscribe and receive incremental updates. This is entirely async — there is no real-time catalog query. By the time a consumer opens a BAP, the catalog is already there.

Three Discover Service deployment options:

| Option | Who hosts | Best for |
|---|---|---|
| ION shared DS | ION Network | Getting started — no infrastructure, subscribe and receive |
| BAP-hosted DS | BAP | Production scale — full control over filtering and ranking |
| Integrated | BAP (owns both sides) | Vertically integrated — still formally subscribes, to own DS |

**BPPs do not implement `/on_discover`** — the Discover Service calls this on the BAP.
**BAPs do not query BPPs directly for catalog** — subscribe once, receive via `/on_discover`.

### Phase 2 — Transaction (direct BAP ↔ BPP)

```
BAP → /select  → BPP
BPP → /on_select → BAP    (callback, separate HTTP POST to BAP's endpoint)
BAP → /init    → BPP
BPP → /on_init   → BAP
BAP → /confirm → BPP
BPP → /on_confirm → BAP
BPP → /on_status → BAP   (unsolicited, ×N through all performance states)
```

Every call returns an immediate HTTP 200 ACK. The actual response arrives separately as a callback POST to the caller's endpoint. Beckn is async throughout Phase 2 — there is no synchronous request-response.

**TTL**: every message carries `context.ttl` (ISO 8601 duration, default PT30S). If the callback does not arrive within TTL, apply the appropriate technical cancellation branch.

**Idempotency**: `context.messageId` (UUID) deduplicates within a 30-minute window. Never reuse a message_id.

---

## 4. ONIX — the reference implementation

ONIX handles the entire Beckn transport layer so you do not have to build it. Download from `schema.ion.id` (coming soon).

**ONIX handles**: HTTP Ed25519 signing · ACK/callback routing · Registry integration · `/publish_catalog` to the Catalogue Service · `/subscribe` to the Discover Service · Request validation and error formatting.

**You implement on top of ONIX**: your catalog content and business logic. The spine files in `flows/` define exactly what your callbacks must return.

---

## 5. How schema packs compose

ION does not add fields directly to Beckn objects. It uses the `{object}Attributes` extension point that Beckn v2.0 defines on every core object. ION extension fields are packaged as **packs** — each pack attaches to one extension point and covers one concern.

Multiple packs compose at the field level. A single `resourceAttributes` object carries fields from several packs simultaneously:

```json
{
  "resourceAttributes": {

    // ← core/localization/v1
    "name": { "id": "Nasi Goreng Spesial", "en": "Special Fried Rice" },
    "shortDesc": { "id": "Nasi goreng dengan ayam dan telur" },

    // ← core/product/v1
    "halalStatus": "HALAL",
    "halalCertNumber": "ID38010000151020",
    "ageRestricted": false,

    // ← trade/resource/v1
    "resourceType": "COMPOSED",
    "availability": { "status": "IN_STOCK", "maxOrderQty": 10 },
    "images": ["https://seller.ion.id/items/nasigoreng.jpg"],
    "logisticsServiceType": "HYPERLOCAL",
    "countryOfOrigin": "IDN",
    "food": { "classification": "HALAL", "spiceLevel": "MEDIUM" },
    "customisationGroups": [...]

  }
}
```

**Pack composition at each API step:**

| Step | Beckn object | Packs |
|---|---|---|
| publish_catalog | Provider | `core/identity/v1` + `trade/provider/v1` |
| publish_catalog | Resource | `core/localization/v1` + `core/product/v1` + `trade/resource/v1` |
| publish_catalog | Offer | `trade/offer/v1` |
| on_select | Consideration | `core/tax/v1` + `trade/consideration/v1` |
| on_select | Performance | `trade/performance/v1` |
| init | Address | `core/address/v1` |
| init | Settlement | `core/payment/v1` |
| init | Contract | `trade/contract/v1` |
| confirm | Contract | `core/identity/v1` + `trade/contract/v1` |
| on_confirm | Contract | `core/identity/v1` + `trade/contract/v1` |
| on_status | Performance | `trade/performance/v1` |
| reconcile | Settlement | `core/payment/v1` + `core/reconcile/v1` |
| rate | Rate | `core/rating/v1` |
| support | Support | `core/support/v1` |
| raise | (network channel) | `core/raise/v1` |

---

## 6. How spines and branches work together

Every transaction follows one **spine** — the happy path from catalog to contract complete. The spine declares which API calls happen, in what order, and what fields are required at each step.

**Branches** are conditional sub-flows that activate when something happens outside the happy path. They attach to a running spine transaction at a defined window. Multiple branches can be active simultaneously on the same transaction.

```
SPINE:
  publish → select → init → confirm → PACKED → DISPATCHED → DELIVERED → COMPLETE

BRANCHES active simultaneously on a single transaction:
  payment-prepaid-BAP-collected   window: init → on_confirm
  on-network-LSP                  window: on_confirm (one-time trigger)
  fulfillment-delay               window: on_confirm → DELIVERED (BPP may push anytime)
  track/on_track                  window: on_confirm → DELIVERED (consumer polls)
  support/on_support              window: on_confirm → COMPLETE (if issue raised)
  reconcile/on_reconcile          window: DELIVERED → settlement window
```

Three branch categories:

- **During-transaction** (10 branches): activate between select and on_confirm — payment method selection, fulfillment type, multi-FC, technical cancellations
- **Post-confirm** (21 branches): activate after on_confirm — cancellation, returns, RTO, updates, price adjustments, exchange, replacement
- **Cross-cutting** (4 branches + 1 network channel): available on all spines — track, support, rating, reconcile, and raise (participant→ION)

Full branch map with all windows and triggers: [`flows/trade/README.md`](flows/trade/README.md)

---

## 7. ION Atlas — use it throughout your build

**ION Atlas** is the schema registry and developer tooling for ION. It is not something you read at the end of your build — it is a tool you use from day one.

### What Atlas does

**Semantic search** — find the right field by describing what you need in plain English. Atlas searches all ION and Beckn core schemas by meaning, not just keywords. "Delivery agent phone number" finds `agentPhone` even if you didn't know that was the field name.

```bash
ion search "halal certification status"
ion search "delivery agent contact"
ion search "government procurement reference"
```

**Flow navigation** — the Atlas Explorer at `schema.ion.id/atlas (coming soon)` lets you browse schemas and flow definitions side by side. See not just what a field is but where in the transaction lifecycle it appears, which spine requires it, and which branch sets it.

**Clash detection before you add** — before adding any new field, check whether it already exists or would conflict with a reserved Beckn term.

```bash
ion validate agentPhone        # → field exists in trade/performance/v1
ion validate deliveryPersonId  # → near-match warning, see agentPhone
ion validate myNewField        # → clear to propose if truly new
```

**Propose new fields** — if you genuinely need something that does not exist, Atlas drafts all three required schema files and raises a PR to the ION Council in one flow.

```bash
ion propose
# → describe in plain English
# → review existing matches
# → AI drafts attributes.yaml + context.jsonld + vocab.jsonld
# → PR raised on ion-schema-trade
# → ION Council reviews fortnightly
```

### Install the CLI

```bash
npm install -g @ion-network/cli

ion search "what you need"
ion validate fieldName
ion propose
ion status <github-pr-url>
```

Web Explorer: `schema.ion.id/atlas (coming soon)`

### What Atlas does not do

Atlas does not auto-approve fields. Every proposal goes to the ION Council — which includes the Beckn team for decisions with upstream implications. No schema enters the network without that review. Atlas makes the proposal fast and well-formed; governance ensures it is right.

---

## 8. Mandatory actions

**BPP mandatory:**
`publish_catalog`, `on_select`, `on_init`, `on_confirm`, `on_status`, `on_cancel`, `on_support`

**BAP mandatory:**
`subscribe`, `select`, `init`, `confirm`, `status`, `support`

**Optional (both):** `track/on_track`, `rate/on_rate`, `update/on_update`, `reconcile/on_reconcile`, `raise/on_raise` and related status/details calls.

---

## 9. Indonesian regulatory requirements

These are mandatory at the network level. Not optional.

| Requirement | Field | Regulatory basis |
|---|---|---|
| Seller tax ID | `npwp` (16 digits) at confirm | PMK 136/2023 |
| Business registration | `nib` (13 digits) at confirm | PP 5/2021 |
| Halal declaration | `halalStatus` on all food/beverage | UU 33/2014 |
| Country of origin | `countryOfOrigin` on all resources | PerBPOM 31/2018 |
| PPN (current standard rate, e.g. 11% under PMK 131/2024) | `ppnRate` (decimal, sourced from current DJP/PMK) on all taxable goods | UU 7/2021 HPP; current applicable PMK |
| Consumer protection | `cancellable`, `returnable`, `returnAllowedReasons` | UU 8/1999 |
| Consumer care contact | `contactDetailsConsumerCare` on all offers | UU 8/1999 Pasal 7 |
| Bahasa Indonesia | `name.id`, `shortDesc.id` on all catalog items | ION Network Policy |
| Age restriction | `ageRestricted` on all resources | PP 109/2012 |

---

## 10. Sector-specific patterns

The cross-sector primitives covered above compose differently across sectors. For the full pattern catalog, deep-dives on sector-specific commerce patterns (B2C-LIVE social/OTT commerce, B2C-DIG digital goods, LOG-HYPERLOCAL instant delivery, LOG-XB cross-border, etc.), and the sector's spine chooser, read the sector doc:

- **Trade** — [`ION_Sector_A_Trade.md`](ION_Sector_A_Trade.md) (13 spines: B2C-SF, B2C-MTO, B2C-SUB, B2C-LIVE, B2C-DIG, B2B-PP, B2B-CR, MP-IH, MP-IL, AUC-F, AUC-R, XB, B2G)
- **Logistics** — [`ION_Sector_B_Logistics.md`](ION_Sector_B_Logistics.md) (6 spines: LOG-HYPERLOCAL, LOG-PARCEL, LOG-FREIGHT, LOG-RORO, LOG-XB, LOG-WAREHOUSE, plus 13 branch families and discovery intent patterns)

## 11. Policy Terms Resolution

ION has 67 ratified policy terms documents across 7 categories that sellers reference from catalog offers. The terms documents are the authoritative definition of what each policy means — sellers never author policy prose.

### The lifecycle

1. **Seller declares IRIs at publish_catalog.**
   ```yaml
   offerAttributes:
     returnPolicy:       ion://policy/return/standard/7d-sellerpays
     cancellationPolicy: ion://policy/cancel/prepacked/free
     warrantyPolicy:     ion://policy/warranty/manufacturer/1y-distance-service
     disputePolicy:      ion://policy/dispute/consumer/bpsk
     grievanceSlaPolicy: ion://policy/grievance-sla/consumer/standard
     paymentTermsPolicy: ion://policy/payment-terms/upfront/full
   ```

2. **ION Central validates at catalog publish.**
   - Unknown IRI → ION-2010
   - Deprecated IRI → ION-2011 (response includes supersededBy)

3. **BAP resolves IRI to render consumer-facing text.**
   ```
   GET /policies/ion%3A%2F%2Fpolicy%2Freturn.standard.7d.sellerpays

   → { displayText: { id: "Pengembalian 7 hari...", en: "7-day return..." },
       returnWindowDays: 7, ... }
   ```

4. **Enforcement at runtime.** Every action checked against the terms document. Examples:
   - Buyer sends /cancel after DISPATCHED on an offer with `cancellationWindowCloses: PACKED` → ION-5001
   - Buyer sends /update[RETURN_INITIATED] with reason CHANGE_OF_MIND on fashion.7d.fit_only (doesn't include CHANGE_OF_MIND) → ION-5002
   - Buyer sends /update[RETURN_INITIATED] 10 days after DELIVERED with a 7-day policy → ION-5004
   - Any action not permitted by the declared policy → ION-5008

5. **Penalty application at reconcile.** When policies are violated or SLAs breached, the linked penalty policy fires. Deduction applied to reconcile; penalty breakdown published for transparency.

### Field mapping

Each new policy field is on `offerAttributes`:
- `returnPolicy`, `cancellationPolicy`, `warrantyPolicy`, `disputePolicy` — existed in v0.3, now expanded enums
- `grievanceSlaPolicy` — **new in v0.4**
- `paymentTermsPolicy` — **new in v0.4**
- `penaltyPolicy` — **new in v0.4** (usually auto-derived; rarely declared explicitly)
- `customTermsAddendum` — **new in v0.4**, free text up to 1000 chars for edge cases

Each spine's profile.json declares which policy categories are required via `requiredPolicyCategories`.

### Versioning

Single registry version at any time. Council ratifies new version with 90-day notice. All catalog entries auto-upgrade on cutover. Sellers notified at ratification time and may re-declare if they want different terms before cutover.

No per-seller version pinning. It doesn't scale past a few hundred sellers.

### Penalty tiers

Sellers are onboarded into Standard / Mall / Premium tiers. Each tier has a minimum penalty commitment. Sellers cannot opt out of their tier's penalty floor — consumer protection compliance is non-negotiable.

### Using Atlas to find policies

```bash
ion search "return policy for fashion"
ion search "grievance SLA for flash sale"
ion search "penalty for seller late dispatch"
ion search "COD payment terms"
```

Web Explorer: `schema.ion.id/atlas/policies` (coming soon)


## 12. Operations readiness — v0.5

Before going to production, review `docs/ION_Sector_A_Trade.md` → "Operations-readiness notes (v0.5)". It covers:

- Policy IRI authority (stop duplicating terms on offer)
- KYC lifecycle and category licenses
- Refund timelines by payment method (DO NOT assume uniform P3D)
- Age verification flow at delivery
- Data residency enforcement
- Batch reconcile with tax withholding
- Variant matrix for multi-axis products
- Payment milestone schedules
- Logistics events that do NOT surface on Trade

Failure to implement these will cause production incidents in the first 30 days.

## 13. Signing and security

Every API call must carry an Ed25519 signature in the `Authorization` header. The receiving party verifies against the sender's public key in the ION registry.

- Clock skew tolerance: 30 seconds — ensure NTP synchronisation
- Message TTL: include `context.ttl` in every message; receiver rejects expired messages
- Idempotency: `context.messageId` (UUID) deduplicates within 30 minutes

ONIX handles all of this automatically.

---

## 14. Error handling

Error format: `ION-XXXX`. First digit = category:

| Prefix | Category |
|---|---|
| ION-1xxx | Transport — signature, registry, TTL |
| ION-2xxx | Catalog — payload size, missing images |
| ION-3xxx | Transaction — item unavailable, bad customisation, below MOQ |
| ION-4xxx | Fulfillment — invalid GPS, bad state transition |
| ION-5xxx | Post-order — cancellation or return window closed |
| ION-6xxx | Settlement — amount mismatch, unsupported payment rail |
| ION-7xxx | Network policy — NIB invalid, currency not IDR |
| ION-8xxx | Schema validation — required field missing, format wrong |
| ION-9xxx | System — internal error, BPP timeout |

Full registry: `errors/registry.json`. Each entry has `resolution.en` — what to change to fix it.

---

## 15. Next steps

| What to read | Where |
|---|---|
| Trade sector regulatory context and pack composition | `docs/ION_Sector_A_Trade.md` |
| Reference spine — required fields at every step | `flows/trade/spines/B2C-SF/v1/spine.yaml` |
| Your commerce pattern | `flows/trade/spines/{pattern}/v1/README.md` |
| Complete branch map | `flows/trade/README.md` |
| Field search and proposal | `schema.ion.id/atlas (coming soon)` or `ion search` |
| Error lookup | `errors/registry.json` |
| Reporting a spec issue | `.github/ISSUE_TEMPLATE/spec_issue.md` |


## Protocol Layer — Ack / Nack / CounterSignature (B-8)

Every Beckn v2.0 action has a **two-step response cycle**: a synchronous
Ack/Nack immediately from the receiver, followed (when relevant) by an
asynchronous callback action.

**ION flow diagrams describe the callback step only.** The synchronous Ack
is implicit on every action — this section explains it so the picture is
complete.

### The two-step cycle

```
BAP → POST /select                        ─── action
      ← 200 OK with Ack { counterSignature }   ← synchronous response
                                               (receipt + HTTP signature proof)
      ...time passes, BPP processes...
BPP → POST /on_select (to bapUri)         ─── callback
      ← 200 OK with Ack { counterSignature }
```

### What the Ack contains

The Ack response body is a small JSON object with:

- `message.ack.status`: `ACK` (accepted for processing) or `NACK` (rejected)
- `counterSignature`: the receiver's signature over the request digest,
  proving they received the original payload unmodified

For rejections, the response uses one of Beckns error response shapes:
`NackBadRequest`, `NackUnauthorized`, `AckNoCallback`, `ServerError`.

### ION error codes in Beckn Error.code

When an ION error (e.g. `ION-3013 — Item reservation window expired`) is
surfaced as a Nack response, it goes into Beckns `Error.code` field:

```json
{
  "error": {
    "code": "ION-3013",
    "message": "Item reservation window expired. Restart from /select.",
    "type": "BUSINESS"
  }
}
```

See `errors/README.md` for the full wire mapping.

### HTTP Signature

Every request AND every Ack MUST carry an `Authorization: Signature ...`
header per the Beckn HTTP Signature spec. ION uses Ed25519 signatures with
BLAKE2b-512 digests (see `ion.yaml#x-ion-security`).

### Clock skew tolerance

Signature timestamps are validated against a 30-second clock skew tolerance
per ION profile. NPs running more than 30 seconds out of sync will see every
request fail signature validation.

### When Ack is enough (no callback)

Some actions only have a synchronous Ack — no callback follows. Currently
this applies to: `/rate` (one-way submission, no on_rate required if BPP
chooses not to respond), and sandbox mode (`context.try: true`) actions
which never produce side effects.

## 16. Beckn Protocol Layer — Ack/Nack, Context, and Wire Format

ION sits on top of Beckn Protocol v2.0. A developer implementing an ION BAP or BPP must also conform to the Beckn wire protocol. This section covers the parts of Beckn that affect every ION call.

### 17.1 Ack / Nack — every action has two responses

Every Beckn action receives **two** responses:

1. **Synchronous Ack or Nack** — returned immediately in the HTTP response body when the peer receives the request. Proves receipt.
2. **Asynchronous callback** — returned later via a separate HTTP call to the sender's callback URL. Carries the actual business response.

```
BAP → POST /select → BPP
                     ← 200 OK { Ack, CounterSignature }     (synchronous, proves receipt)
                     ...
BAP ← POST /on_select ← BPP                                 (asynchronous, actual response)
BAP → 200 OK { Ack }                                        (BAP acks the callback)
```

Three important points:

- **Ack is not optional.** A peer that sends a `200 OK` without an `Ack` body is non-conformant.
- **Nack is for request-level failures** (bad signature, malformed JSON, unauthorized sender). ION-level business errors (`ION-3xxx` etc.) are returned in the asynchronous callback, not in the Nack.
- **CounterSignature** in the Ack body proves the receiver actually processed the request. Mandatory under Beckn's signature scheme.

Flow documents in `flows/trade/spines/` describe only the asynchronous half of the pattern because the Ack/Nack half is boilerplate. Implementers must handle both.

### 17.2 Context — camelCase, not snake_case

Beckn Context fields are camelCase: `bapId`, `bppId`, `bapUri`, `bppUri`, `transactionId`, `messageId`, `networkId`, `requestDigest`, `schemaContext`. ION flow documents use these names.

The older snake_case format (`bap_id`, `transaction_id`, etc.) is Beckn v1.x and **must not be used** on ION — HTTP Signature digests are computed over the serialized JSON, so the bytes must match exactly.

### 17.3 Message wrapper — `contract`, not `order`

Beckn v2.0 renamed the transaction object from `Order` to `Contract`. Every action message now carries a `contract` field:

```json
{
  "context": { ... },
  "message": {
    "contract": {
      "id": "...",
      "status": { "descriptor": { "code": "ACTIVE" } },
      "commitments": [ ... ],
      "consideration": { ... },
      "performance": [ ... ],
      "settlements": [ ... ],
      "participants": [ ... ],
      "contractAttributes": { ... }
    }
  }
}
```

There is no `message.order`, `message.items`, `message.fulfillments`, `message.payment`, `message.quote`, or `message.billing` in Beckn v2.0. Those were v1.x paths. If you see them in older docs or tutorials, translate:

| Beckn v1.x path | Beckn v2.0 path |
|---|---|
| `message.order.items[]` | `message.contract.commitments[].resources[]` |
| `message.order.fulfillments[]` | `message.contract.performance[]` |
| `message.order.quote` | `message.contract.consideration` |
| `message.order.payment` | `message.contract.settlements[]` |
| `message.order.billing` | `message.contract.participants[?role=BUYER]` |

### 17.4 Attributes — the extension slot

Beckn core is domain-neutral. Every extension point is a slot named `*Attributes` that holds a JSON-LD-typed object:

- `Resource.resourceAttributes`
- `Offer.offerAttributes`
- `Provider.providerAttributes`
- `Commitment.commitmentAttributes`
- `Consideration.considerationAttributes`
- `Performance.performanceAttributes`
- `Settlement.settlementAttributes`
- `Contract.contractAttributes`

Each Attributes object carries `@context` (URI to a JSON-LD context) and `@type` (compact IRI of the schema). ION's schema packs publish their context files at `https://schema.ion.id/{pack-path}/v1` (coming soon); context.jsonld files in the repo give the local mapping.

Every ION field goes inside the appropriate `*Attributes` slot, not at the top level of the Beckn object.

### 17.5 HTTP Signature — every request signed

Beckn requires HTTP Signatures on every inter-peer call. The signing scheme:

- Algorithm: `ed25519` on ION (declared in `x-ion-security` in `ion.yaml`)
- Digest: BLAKE2b-512 of the full request body
- Clock skew tolerance: 30 seconds

Signatures are verified against the sender's public key registered in ION's subscriber registry (registry.ion.id). Signatures MUST cover the Context fields and the Message body. CounterSignatures on the Ack MUST be verified by the sender.

---

## 17. Policy IRI Grammar

ION policy IRIs follow a canonical grammar so that registry lookups and resolver implementations can parse them deterministically.

### Format

```
ion://policy/{category}.{subcategory}.{specifier}[.{qualifier}]
```

Examples:
```
ion://policy/return.standard.7d.sellerpays
ion://policy/cancel.mto.nofee.before_prepare
ion://policy/warranty.manufacturer.1y.distance_service
ion://policy/dispute.consumer.bpsk
ion://policy/grievance.sla.standard
ion://policy/payment.upfront.full
ion://policy/penalty.seller.sla_breach.standard
```

### Rules

- **Segments are `.`-separated.** No `/` inside the IRI body; the scheme is always `ion://policy/`.
- **First segment is category**, drawn from: `return | cancel | warranty | dispute | grievance | payment | penalty`.
- **Second segment is subcategory.** Free-form but lowercase, alphanumeric + underscore.
- **Third segment is specifier.** Typically duration/condition (`7d`, `14d`, `none`) or business model (`consumer`, `commercial`, `b2b`, `manufacturer`, `seller`).
- **Optional qualifier.** Adds further detail where needed (`sellerpays`, `before_prepare`, `distance_service`, `15pct`).
- **Maximum length:** 100 characters.
- **No versioning in the IRI.** ION runs single-version registry; new versions supersede previous ones (see single-version policy in `ion.yaml`).

### Resolver

Clients resolve IRIs via:

```
GET /policies/{urlEncodedIri}
```

Example:
```
GET /policies/ion%3A%2F%2Fpolicy%2Freturn.standard.7d.sellerpays
```

Returns the full terms document with `displayText`, `returnWindowDays`, `refundTimelineFromReturnDelivered`, etc.

---

## 18. ION Error Codes in Beckn Nack

ION's error registry (`errors/registry.json`) defines ~45 error codes like `ION-3013`, `ION-5005`. Beckn's `Nack` response body carries an `Error` object with `code`, `message`, `type` fields.

### Mapping

ION errors surface in Beckn Nack as:

```json
{
  "message": { "ack": { "status": "NACK" } },
  "error": {
    "code": "ION-3013",
    "type": "DOMAIN-ERROR",
    "message": "Item reservation window expired",
    "path": "message.contract.commitments[0].offer"
  }
}
```

### Rules

- **`code` field** carries the ION-prefixed code verbatim.
- **`type` field** is one of Beckn's error categories: `CONTEXT-ERROR`, `CORE-ERROR`, `DOMAIN-ERROR`, `POLICY-ERROR`. ION-level errors are `DOMAIN-ERROR`; network infrastructure errors are `CORE-ERROR`; policy violations are `POLICY-ERROR`.
- **`message` field** uses the English title from the ION registry. The Indonesian title may be surfaced by the BAP to end users but is not the wire-level message.
- **`path` field** points to the offending field in Beckn v2.0 field path notation.

### Ack vs callback placement

Not all ION errors surface in Nack. The rule:

| Error severity | Where it surfaces |
|---|---|
| Request is structurally invalid (bad signature, malformed JSON, missing required field at Beckn level) | Synchronous Nack |
| Request is structurally valid but business rule fails (stock expired, return window closed, policy violation) | Asynchronous callback with error payload |
| Internal BPP failure (DB down, third-party timeout) | Asynchronous callback, error code `ION-9xxx` |

The error registry documents expected placement per code — check `affected_apis` in each error entry.


---

## See also

- **New to ION?** [`ION_Start_Here.md`](ION_Start_Here.md) — 10-minute landing page
- **Term unclear?** [`ION_Glossary.md`](ION_Glossary.md)
- **Want to see a real transaction?** [`ION_First_Transaction.md`](ION_First_Transaction.md)
- **Building for Trade?** [`ION_Sector_A_Trade.md`](ION_Sector_A_Trade.md)
- **Building for Logistics?** [`ION_Sector_B_Logistics.md`](ION_Sector_B_Logistics.md)
- **Implementing signing?** [`ION_Onboarding_and_Auth.md`](ION_Onboarding_and_Auth.md)
- **Conformance testing?** [`ION_Beckn_Conformance.md`](ION_Beckn_Conformance.md)
