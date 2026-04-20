# ION — Indonesia Open Network

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Spec Version](https://img.shields.io/badge/Spec-v0.5.1--draft-orange.svg)](CHANGELOG.md)
[![Beckn](https://img.shields.io/badge/Beckn-v2.0.1-green.svg)](https://beckn.io)

Open network for digital commerce in Indonesia, built on Beckn Protocol v2.0.

Any buyer app and any seller app on ION can transact with each other without bilateral integration. A seller registered on ION is instantly reachable by every buyer app on the network — across Food, Grocery, Fashion, Electronics, Beauty, Agritech, Logistics, Mobility, Finance, and Services.

---

## How ION works — understand this before writing any code

ION has two distinct phases and two distinct services. Getting this wrong wastes days.

**Phase 1 — Catalog (async, subscription-based)**

```
BPP publishes catalog → Catalogue Service (Beckn Fabric)
                                ↕
                        Discover Service
                        (ION-hosted  ←→  or BAP-hosted)
                                ↕
BAP subscribes → Discover Service → /on_discover → BAP pipeline
```

The **Catalogue Service** is hosted by Beckn Fabric. BPPs push their catalog here via `/publish_catalog`. The **Discover Service** sits between the Catalogue Service and BAPs. Three deployment options:

| | Who hosts | Characteristics |
|---|---|---|
| **Option 1 — ION shared DS** | ION Network | No infrastructure to run. Subscribe and start receiving catalogs. Best for getting started. |
| **Option 2 — BAP-hosted DS** | BAP themselves | Full control over filtering, ranking, and caching. BAP runs their own instance. |
| **Option 3 — Integrated** | BAP (vertically integrated) | BAP and BPP are the same organisation — still formally subscribes, to their own DS. |

Key rules: BPPs do not implement `/on_discover` — they publish to the Catalogue Service; the DS delivers to BAPs. BAPs do not query BPPs for catalog — they subscribe once and receive via `/on_discover`.

**Phase 2 — Transaction (direct, BAP ↔ BPP)**

From `/select` onwards, the BAP talks directly to the BPP. No Catalogue Service. No Discover Service.

```
BAP → /select  → BPP → /on_select
BAP → /init    → BPP → /on_init
BAP → /confirm → BPP → /on_confirm
BPP → /on_status (×N, unsolicited, through all performance states)
```

Every call is a POST returning an immediate ACK. The actual response arrives later as a callback to the caller's endpoint — Beckn is async all the way through Phase 2.

**The flow files in this repo define exactly what each Phase 2 call must contain.** Phase 1 catalog structure is documented in each spine's examples section.

---

## Building on ION — start with ONIX

ION provides **ONIX**, a reference implementation that handles the entire Beckn transport layer.

**Download:** ION DevLabs — `devlabs.ion.id` (coming soon) (coming soon) (coming soon)

ONIX handles for you: HTTP signatures on every request and response · ACK/callback routing and async flow management · Subscriber registry integration · `/publish_catalog` to the Catalogue Service · `/subscribe` to the Discover Service · Request validation and error formatting.

**You implement on top of ONIX:**

| Role | What you build |
|---|---|
| **BPP developer** | Catalog content (resources, offers, policies) · Transaction callback handlers (`on_select`, `on_init`, `on_confirm`, `on_status`) · Fulfilment state updates |
| **BAP developer** | Consumer search and discovery UI · Order flow and payment · `/on_discover` catalog indexing handler |

You can build without ONIX — the spec is complete and implementation-agnostic. But ONIX saves weeks of transport layer work and ensures compliance from day one.

---

## Are you a BAP or a BPP?

| | BAP — Buyer Application | BPP — Seller Application |
|---|---|---|
| **What it is** | The consumer-facing app | The seller-facing app |
| **Examples** | Food delivery app, grocery super-app, marketplace | Restaurant ordering system, brand catalog, seller fulfillment backend |
| **What it does** | Sends requests (`/select`, `/init`, `/confirm`, `/status`) | Responds to requests — returns catalog, computes price, creates contract, updates tracking |
| **Build this if...** | You are building for consumers | You are building for a brand, store, or seller |

Both sides need to understand the full exchange, but read it from your own perspective. Every spine in `flows/` declares `requiredFields` and `conditionalFields` per step, annotated by who sets them and who receives them.

---

## What is in this repository

```
ion-network/
  schema/     ← What things ARE   — field definitions extending Beckn v2.0
  flows/      ← What things DO    — API sequences and field requirements per step
  errors/     ← What went wrong   — machine-readable error registry
  docs/       ← Why things are    — regulatory context, architecture, orientation
```

These layers are designed to be read together. A spine in `flows/` references schema packs in `schema/`. An error entry in `errors/` references both a schema field and a flow step. The schema packs define field structure; the flows define which fields are required when.

---

## The developer journey

### Step 1 — Orient: understand the ION architecture

Read the Developer Orientation. Covers the two-phase architecture, the BAP/BPP model, how schema packs compose, how spines and branches work together, the mandatory action sets, and Indonesian regulatory requirements.

**Time: 20 minutes.**

→ [`docs/ION_Atlas_Developer_Orientation.md`](docs/ION_Atlas_Developer_Orientation.md)

---

### Step 2 — Understand your sector

Read the Trade sector guide. Covers choosing the right commerce pattern, all Indonesian regulatory requirements with field names and legal basis, schema pack composition table (which packs attach at which API step), the availability model, resource type model, state machine selection, and policy IRI reference.

→ [`docs/ION_Sector_A_Trade.md`](docs/ION_Sector_A_Trade.md)

---

### Step 3 — Pick your commerce pattern and read the spine

Find the spine for your commerce pattern. The spine defines the full API sequence, required and conditional fields at every step, applicable branches, and the state machine in use.

| Pattern | When to use | Spine |
|---|---|---|
| B2C-SF | Standard consumer purchase | `flows/trade/spines/B2C-SF/v1/` |
| B2C-MTO | Made-to-order (food QSR, tailoring) | `flows/trade/spines/B2C-MTO/v1/` |
| B2C-SUB | Recurring subscription | `flows/trade/spines/B2C-SUB/v1/` |
| B2C-LIVE | Live / OTT / social commerce (Shopee Live, Tokopedia Play, Vidio shoppable) | `flows/trade/spines/B2C-LIVE/v1/` |
| B2C-DIG | Digital goods (pulsa, PLN tokens, vouchers, game currency) | `flows/trade/spines/B2C-DIG/v1/` |
| B2B-PP | Wholesale, prepaid | `flows/trade/spines/B2B-PP/v1/` |
| B2B-CR | Wholesale, credit terms | `flows/trade/spines/B2B-CR/v1/` |
| MP-IH | Marketplace, platform holds inventory | `flows/trade/spines/MP-IH/v1/` |
| MP-IL | Marketplace, sellers hold inventory | `flows/trade/spines/MP-IL/v1/` |
| AUC-F | Forward auction (buyers bid up) | `flows/trade/spines/AUC-F/v1/` |
| AUC-R | Procurement reverse auction | `flows/trade/spines/AUC-R/v1/` |
| XB | Cross-border export | `flows/trade/spines/XB/v1/` |
| B2G | Government procurement | `flows/trade/spines/B2G/v1/` |

## Policy Terms Registry

Since v0.4, ION has a machine-enforceable policy model. Every offer declares policy IRIs that resolve to ratified terms documents; ION Central enforces the terms at every API boundary.

Seven policy categories, **67 ratified policy documents**:

| Category | Count | Examples |
|---|---|---|
| RETURN | 15 | `return.standard.7d.sellerpays`, `return.fashion.7d.fit_only.sellerpays`, `return.electronics.14d.unopened_or_defective.sellerpays`, `return.pharmacy.nonreturnable` |
| CANCELLATION | 10 | `cancel.prepacked.free`, `cancel.mto.nofee.before_prepare`, `cancel.flash_sale.none_after_confirm`, `cancel.b2b.until_dispatched.15pct` |
| WARRANTY | 8 | `warranty.manufacturer.1y.distance_service`, `warranty.seller.1y`, `warranty.refurbished.30d.limited`, `warranty.none` |
| DISPUTE | 5 | `dispute.consumer.bpsk`, `dispute.commercial.bani`, `dispute.international.uncitral`, `dispute.b2g.lkpp` |
| GRIEVANCE_SLA | 4 | `grievance.sla.standard`, `grievance.sla.premium_mall`, `grievance.sla.flash_critical`, `grievance.sla.b2b_businesshours` |
| PAYMENT_TERMS | 8 | `payment.upfront.full`, `payment.cod.full`, `payment.credit.net30`, `payment.installment.3mo`, `payment.subscription.monthly_autopay` |
| PENALTY | 17 | Seller SLA breach (Standard/Mall/Premium tiers), restocking fees, late dispatch, COD refusal, chargeback abuse, creator misconduct |

Registry at `/policies/` with per-file YAML terms and generated `registry.json` index.

Seller declares IRIs; ION enforces:
```yaml
offerAttributes:
  returnPolicy:       ion://policy/return/standard/7d-sellerpays
  cancellationPolicy: ion://policy/cancel/prepacked/free
  warrantyPolicy:     ion://policy/warranty/manufacturer/1y-distance-service
  disputePolicy:      ion://policy/dispute/consumer/bpsk
  grievanceSlaPolicy: ion://policy/grievance-sla/consumer/standard
  paymentTermsPolicy: ion://policy/payment-terms/upfront/full
```

See `policies/README.md` for the full model, `docs/ION_Sector_A_Trade.md § 7b` for the developer guide, and `docs/ION_Atlas_Developer_Orientation.md § 12` for the complete lifecycle walkthrough.


Start with `README.md` in the spine folder for a summary. Read `spine.yaml` for the full field-level specification.

For the complete branch map — all 30+ sub-branches with their windows and triggers:

→ [`flows/trade/README.md`](flows/trade/README.md)

---

### Step 4 — Look up field definitions

When you need the exact type, format, valid enum values, mandatory condition, or Indonesian regulatory source for a specific field — go to the schema pack.

**Search fields semantically using ION Atlas:**
→ `devlabs.ion.id/atlas (coming soon)` — type what you need in plain English ("halal certification status", "delivery agent phone") and Atlas returns the exact field, which pack it belongs to, and its regulatory basis.

**Browse directly:**
- Cross-sector fields (address, identity, payment, tax, localization, halal, support, raise, rating, reconcile): `schema/extensions/core/`
- Trade sector fields (resource, offer, provider, consideration, performance, contract, commitment): `schema/extensions/trade/`

Each pack has an `attributes.yaml` (OAS 3.1 schema), a `README.md` (summary and key rules), and `docs/01-overview.md` (design rationale and regulatory context).

---

### Step 5 — Build. When you hit an error, look it up.

→ [`errors/registry.json`](errors/registry.json)

Every ION error code is in this file with: what triggered it, which field is wrong, and exactly what to change to fix it.

Error category by prefix: ION-1xxx=transport · ION-2xxx=catalog · ION-3xxx=transaction · ION-4xxx=fulfillment · ION-5xxx=post-order · ION-6xxx=settlement · ION-7xxx=network policy · ION-8xxx=schema validation · ION-9xxx=system

---

### Step 6 — Use Atlas throughout

**ION Atlas** is the schema registry and developer tooling for ION. Use it at any point in your build — not just when you finish.

**Search**: `ion search "halal certification"` — semantic search finds the right field by meaning, not just keyword. Searches all ION and Beckn core schemas simultaneously.

**Validate before you add**: `ion validate harvestDate` — four-tier clash detection tells you whether a field already exists, conflicts with a reserved term, or is clear to propose.

**Propose a new field**: `ion propose` — interactive flow: describe in plain English → review existing matches → AI drafts all three required schema files → raises a PR to the ION Council for review.

**Navigate flows**: Atlas Explorer at `devlabs.ion.id/atlas (coming soon)` lets you browse and search flow definitions alongside schemas — so you can see not just what a field is but where in the transaction lifecycle it appears.

```bash
npm install -g @ion-network/cli

ion search "delivery agent contact"
ion validate agentPhone
ion propose
ion status <github-pr-url>
```

→ Full Atlas architecture: [`docs/ION_Atlas_Developer_Orientation.md`](docs/ION_Atlas_Developer_Orientation.md)

---

### Step 7 — Found a gap? Contribute.

If you find a missing field, a wrong example, an edge case the spec does not cover, or a missing error code — raise it. Real implementation experience resolves open questions faster than any design review.

→ [`CONTRIBUTING.md`](CONTRIBUTING.md)

Use the GitHub Issue templates in `.github/ISSUE_TEMPLATE/` or go through `ion propose` for field additions.

---

## ION object model — quick reference

| Object | What it is | Set by | First appears |
|---|---|---|---|
| **Resource** | The thing being sold | BPP | publish_catalog / on_discover |
| **Offer** | Terms on a Resource — price, policy, availability | BPP | publish_catalog / on_discover |
| **Commitment** | Buyer's selection — links Resource + Offer + quantity | BAP | select |
| **Consideration** | Price breakdown — ITEM, DELIVERY, TAX, DISCOUNT | BPP | on_select |
| **Contract** | Confirmed agreement — immutable after on_confirm | BPP | on_confirm |
| **Performance** | Fulfilment tracking — state, agent, proof | BPP | on_status |

---

## Mandatory Indonesian regulatory fields

These are network-mandated. A catalog or transaction missing any of these will be rejected by ION Central.

| Field | What it is | Required when | Format |
|---|---|---|---|
| `npwp` | Nomor Pokok Wajib Pajak | Always at confirm | 16 digits (post-2024 format) |
| `nib` | Nomor Induk Berusaha | Always at confirm | 13 digits |
| `halalStatus` | MUI/BPJPH halal declaration | All food and beverage resources | `HALAL / HALAL_PENDING / NON_HALAL / NOT_APPLICABLE` |
| `halalCertNumber` | MUI halal cert number | When `halalStatus = HALAL` | Starts with ID |
| `countryOfOrigin` | Country of production | All resources | ISO alpha-3 (e.g. IDN) |
| `bpomRegNumber` | BPOM food/drug/cosmetic registration | All packaged food, personal care, pharma | `MD-` or `ML-` prefix |
| `ageRestricted` | Age verification flag | All resources | boolean |
| `name.id` | Bahasa Indonesia product name | All resources | Language object with `id` key |
| `contactDetailsConsumerCare` | Consumer care contact | All offers | name, email, phone comma-separated |

---

## Standard policy IRIs

Declare these in `offerAttributes`. ION Central enforces the terms — you declare, ION enforces.

```
# Return policies
ion://policy/return.7d.sellerpays      7-day return window, seller arranges and pays pickup
ion://policy/return.15d.sellerpays     15-day window, seller pays
ion://policy/return.7d.buyerpays       7-day window, buyer ships back
ion://policy/return/standard/none               No returns

# Cancellation policies
ion://policy/cancel/prepacked/free     Free cancellation before PACKED state
ion://policy/cancel/mto/nofee-before-prepare   MTO: free before preparation starts
ion://policy/cancel/standard/none               No cancellation after confirm

# Warranty policies
ion://policy/warranty.1y.manufacturer  1-year manufacturer warranty (legal minimum for electronics)
ion://policy/warranty.2y.manufacturer  2-year manufacturer warranty
ion://policy/warranty/standard/none             No warranty

# Dispute resolution policies
ion://policy/dispute/consumer/bpsk     B2C: BPSK (Badan Penyelesaian Sengketa Konsumen)
ion://policy/dispute/commercial/bani   B2B: BANI arbitration
ion://policy/dispute/commercial/odr    Online Dispute Resolution via ION platform
```

---

## API coverage

| API group | APIs | Status |
|---|---|---|
| Discovery | publish_catalog, subscribe, on_discover | ✅ Spec complete |
| Transaction | select, on_select, init, on_init, confirm, on_confirm | ✅ Spec complete |
| Fulfilment | status, on_status, update, on_update, cancel, on_cancel | ✅ Spec complete |
| Tracking | track, on_track | ✅ Spec complete |
| Post-order | rate, on_rate | ✅ Spec complete |
| Settlement | reconcile, on_reconcile | ✅ Spec complete |
| Support | support, on_support | ✅ Spec complete |
| Raise | raise, on_raise, raise_status, on_raise_status, raise_details, on_raise_details | ✅ Spec complete |

---

## Beckn Protocol

ION extends Beckn Protocol v2.0.1 without forking it. Core transport spec:
https://github.com/beckn/protocol-specifications-v2

`schema/core/v2/api/v2.0.0/ion.yaml` is the ION network profile overlay. Implementations must satisfy both `beckn.yaml` and `ion.yaml`.

---

*ION Network Specification — v0.5.1-draft — April 2026*


## Composed spec

`schema/core/v2/api/v2.0.0/ion-with-beckn.yaml` — Beckn v2.0 core + all ION extension schemas composed. Generated by `tools/generate_composed.py`. Validates both protocol conformance and field correctness in one pass.
