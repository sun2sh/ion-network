# ION — Indonesia Open Network

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Spec Version](https://img.shields.io/badge/Spec-v0.5.2--draft-orange.svg)](CHANGELOG.md)
[![Beckn](https://img.shields.io/badge/Beckn-v2.0.0-green.svg)](https://beckn.io)

Open network for digital commerce in Indonesia, built on Beckn Protocol v2.0.0.

Any buyer app and any seller app on ION can transact with each other without bilateral integration. A seller registered on ION is instantly reachable by every buyer app on the network — across Food, Grocery, Fashion, Electronics, Beauty, Agritech, and the supporting Logistics network that moves goods between them.

> **Upstream target.** This draft targets [`core-v2.0.0-rc1`](https://github.com/beckn/protocol-specifications-v2) — the current Beckn Protocol v2 Release Candidate (tagged 2026-01-12). Final Beckn v2.0.0 is expected within ~1 week of this draft; ION will re-validate and publish v0.5.2 GA (or v0.5.3-draft if corrections are needed) against final v2.0.0 once released.

---

## New to ION? Start here

If you haven't used ION (or Beckn) before, read these in order. The whole sequence takes ~90 minutes and you'll be ready to write code.

1. **[`docs/ION_Start_Here.md`](docs/ION_Start_Here.md)** — 10 minutes. What ION is, for a complete beginner.
2. **[`docs/ION_Glossary.md`](docs/ION_Glossary.md)** — scan once, keep open as a reference.
3. **[`docs/ION_First_Transaction.md`](docs/ION_First_Transaction.md)** — 20 minutes. A realistic end-to-end transaction, annotated message-by-message.
4. **[`docs/ION_Developer_Orientation.md`](docs/ION_Developer_Orientation.md)** — 40 minutes. Cross-sector concepts, ONIX, mandatory actions, policies.
5. **Your sector doc** — 20 minutes. Either [`ION_Sector_A_Trade.md`](docs/ION_Sector_A_Trade.md) or [`ION_Sector_B_Logistics.md`](docs/ION_Sector_B_Logistics.md).

**Already know Beckn?** Skip to step 4.

---

## Architecture at a glance

```
                    ┌──────────────────────────────┐
                    │       ION Council            │  (governance)
                    └──────────────────────────────┘
                                    │
                                    ▼ ratifies
                    ┌──────────────────────────────┐
                    │   ION Network (ion.yaml)     │   L2 — network profile
                    │   + Policy Registry          │
                    │   + Error Registry           │
                    └──────────────────────────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            ▼                       ▼                       ▼
    ┌──────────────┐       ┌──────────────────┐    ┌────────────────┐
    │ ION Registry │       │ ION Catalogue    │    │  Discover      │
    │              │       │  Service         │    │  Service (CDS) │
    │ (on DeDi)    │       │  (Beckn Fabric)  │    │                │
    └──────────────┘       └──────────────────┘    └────────────────┘
         ▲                          ▲                       ▲
         │ registers                │ publishes             │ queries/subscribes
         │                          │                       │
    ┌────┴─────────────────┐  ┌─────┴──────────────┐  ┌────┴──────────────┐
    │  BAP                 │  │  BPP               │  │  BAP              │
    │  (Tokopedia, Shopee, │  │  (Sepatu Juara,    │  │                   │
    │   Lazada, apps)      │◄─┤   JNE, J&T, LSPs,  │  │                   │
    │                      │  │   warehouses)      │  │                   │
    └──────────────────────┘  └────────────────────┘  └───────────────────┘
         ▲        │                   ▲   │
         │        │  /select          │   │  /on_select
         │        └───────────────────┘   │
         │                                │
         │    /init, /confirm, /status,   │
         │    /track, /update, /reconcile │
         │◄───────────────────────────────┘
         │
         ▼
    ┌──────────────┐
    │  Consumer    │
    │  (uses app)  │
    └──────────────┘
```

Messages between BAP and BPP are **direct** after discovery. ION Central is not a message proxy — it's governance, registry, and catalog infrastructure. Transactions flow peer-to-peer.

---

## Frequently asked questions

**Q: Why isn't there a `/search` endpoint?**
A: Beckn v2.0.0 replaced `/search` with `/discover` (active query) and `/catalog/subscription` (push model). BPPs publish catalogs continuously; BAPs subscribe or query the Discover Service. See [`ION_Developer_Orientation.md`](docs/ION_Developer_Orientation.md) §3.

**Q: Do I need to implement all 30 Beckn endpoints?**
A: No. Mandatory actions depend on your role and sector. A BPP selling shoes doesn't need `/track` (no location tracking). A BAP doesn't need to handle callbacks for flows it doesn't initiate. See `ion.yaml → x-ion-actions` and [`ION_Beckn_Conformance.md`](docs/ION_Beckn_Conformance.md).

**Q: What does ION cost?**
A: The protocol is free and open. Any operational fees are set by ION Council. Commercial terms between BAP and BPP are negotiated bilaterally (or via Framework Agreements for enterprise relationships).

**Q: Can I test without registering as a live participant?**
A: Yes. Set `context.try=true` to run against the ION sandbox. Validate conformance there before applying for production registration.

**Q: What's the difference between `/update` and `/raise`?**
A: `/update` is for bilateral changes — address change, dispute between BAP and BPP, weight adjustment. `/raise` is for network escalation when bilateral resolution fails. `/raise` is an ION L3 extension (not core Beckn). See [`ION_Sector_B_Logistics.md`](docs/ION_Sector_B_Logistics.md) §9.

**Q: Why does `Commitment.status` have only 3 values when `Contract.status` has 4?**
A: Beckn design decision. Contract tracks the overall transaction (can be CANCELLED or COMPLETE distinctly); a Commitment is a line item that just CLOSES — whether by cancellation or completion is tracked at the contract level. See [`ION_Beckn_Conformance.md`](docs/ION_Beckn_Conformance.md) §5.

**Q: The digest line says `BLAKE-512`, but the algorithm is BLAKE2b-512?**
A: Yes — Beckn's wire token is `BLAKE-512` (the name in the signing string). The algorithm *is* BLAKE2b-512. Writing `BLAKE2b-512=...` in the signing string fails Beckn's regex. See `ion.yaml → x-ion-security.digest` and [`ION_Onboarding_and_Auth.md`](docs/ION_Onboarding_and_Auth.md).

**Q: Is ION live?**
A: Not yet. This is v0.5.2-draft. Production launch schedule is set by ION Council.

---

## Active sectors

| Sector | What it covers | Schema path | Flows path |
|---|---|---|---|
| **Trade** (Sector A) | B2C, B2B, MP, AUC, XB, B2G commerce | `schema/extensions/trade/` | `flows/trade/` |
| **Logistics** (Sector B) | Hyperlocal, parcel, freight, Ro-Ro, cross-border, warehousing | `schema/extensions/logistics/` | `flows/logistics/` |

Mobility, finance, tourism, and healthcare sector slots are reserved in the repo structure and will be populated as their working groups ratify.

---

## How ION composes with Beckn — the five-layer model

ION does not fork Beckn. It composes with it in five layers. Knowing which layer a given rule, endpoint, or field belongs to is the most useful piece of orientation.

| Layer | What it is | Where it lives | Example |
|---|---|---|---|
| **L1** — Beckn core | Upstream protocol v2.0.0 (targeting `core-v2.0.0-rc1`). Transport, object model, native `*Attributes` extension slots. Never forked. | External: <https://github.com/beckn/protocol-specifications-v2> | `Provider`, `Offer.offerAttributes` slot, `/select` endpoint |
| **L2** — ION network profile | Policy overlay on Beckn — rules that apply to every participant regardless of sector. | `schema/core/v2/api/v2.0.0/ion.yaml` | Ed25519 signing, NPWP mandatory, data residency Indonesia |
| **L3** — ION protocol endpoint extensions | New endpoints ION adds to Beckn. | `schema/core/v2/api/v2.0.0/ion-endpoints.yaml` | `/raise` family (6), `/reconcile`, `/on_reconcile` |
| **L4** — ION core attribute packs | Cross-sector fields mounting on Beckn's `*Attributes` slots. | `schema/extensions/core/*/v1/` | `address`, `identity`, `participant`, `payment`, `tax` |
| **L5** — ION sector attribute packs | Sector-specific fields mounting on the same slots. | `schema/extensions/{trade,logistics}/*/v1/` | Trade: `cancellationPolicy`, Logistics: `serviceLevel` |

The one rule that makes it all work: every ION attribute pack carries an `x-beckn-attaches-to: <BecknObject>.<slot>` annotation. That annotation **is** the extension contract.

For the full explanation, read [`docs/ION_Layer_Model.md`](docs/ION_Layer_Model.md). For the conformance checklist, read [`docs/ION_Beckn_Conformance.md`](docs/ION_Beckn_Conformance.md).

---

## Two-phase architecture (common to both sectors)

**Phase 1 — Catalog (async, subscription-based)**

```
BPP publishes catalog → Catalogue Service (Beckn Fabric)
                                ↕
                        Discover Service
                        (ION-hosted  ←→  or BAP-hosted)
                                ↕
BAP subscribes → Discover Service → /on_discover → BAP pipeline
```

BAPs may also perform active queries via `/discover` when they need spot pricing (common in logistics freight rate shopping).

**Phase 2 — Transaction (direct, BAP ↔ BPP)**

From `/select` onwards, the BAP talks directly to the BPP. No Catalogue Service. No Discover Service.

```
BAP → /select  → BPP → /on_select
BAP → /init    → BPP → /on_init
BAP → /confirm → BPP → /on_confirm
BPP → /on_status (×N, unsolicited, through all performance states)
BAP ↔ BPP → /update, /cancel, /track, /rate, /support
BAP → /reconcile → BPP → /on_reconcile        (ION L3 extension)
BAP → /raise     → ION → /on_raise            (ION L3 extension, for escalation)
```

---

## Building on ION — start with ONIX

ION provides **ONIX**, a reference implementation that handles the entire Beckn transport layer.

**Download:** ION DevLabs — `schema.ion.id` (coming soon)

ONIX handles HTTP signatures, ACK/callback routing, registry integration, `/publish_catalog`, `/subscribe`, validation, and error formatting. You implement catalog content, transaction callback handlers, and fulfilment state updates on top.

You can build without ONIX — the spec is complete and implementation-agnostic. ONIX saves weeks of transport layer work.

---

## Trade developer journey

If you are building a consumer marketplace, brand catalog, or trade-sector BPP/BAP:

1. **Orient** — 20 min — [`docs/ION_Developer_Orientation.md`](docs/ION_Developer_Orientation.md)
2. **Understand your sector** — [`docs/ION_Sector_A_Trade.md`](docs/ION_Sector_A_Trade.md)
3. **Pick your commerce pattern and read the spine** — [`flows/trade/README.md`](flows/trade/README.md)

| Pattern | When to use | Spine |
|---|---|---|
| B2C-SF | Standard consumer purchase | `flows/trade/spines/B2C-SF/v1/` |
| B2C-MTO | Made-to-order (food QSR, tailoring) | `flows/trade/spines/B2C-MTO/v1/` |
| B2C-SUB | Recurring subscription | `flows/trade/spines/B2C-SUB/v1/` |
| B2C-LIVE | Live / social commerce | `flows/trade/spines/B2C-LIVE/v1/` |
| B2C-DIG | Digital goods | `flows/trade/spines/B2C-DIG/v1/` |
| B2B-PP | Wholesale, prepaid | `flows/trade/spines/B2B-PP/v1/` |
| B2B-CR | Wholesale, credit terms | `flows/trade/spines/B2B-CR/v1/` |
| MP-IH | Marketplace, platform holds inventory | `flows/trade/spines/MP-IH/v1/` |
| MP-IL | Marketplace, sellers hold inventory | `flows/trade/spines/MP-IL/v1/` |
| AUC-F | Forward auction | `flows/trade/spines/AUC-F/v1/` |
| AUC-R | Procurement reverse auction | `flows/trade/spines/AUC-R/v1/` |
| XB | Cross-border export | `flows/trade/spines/XB/v1/` |
| B2G | Government procurement | `flows/trade/spines/B2G/v1/` |

---

## Logistics developer journey

If you are building an LSP, carrier, warehouse operator, or logistics-consuming platform:

1. **Orient** — 25 min — [`docs/ION_Sector_B_Logistics.md`](docs/ION_Sector_B_Logistics.md)
2. **Understand your sector** — [`docs/ION_Sector_B_Logistics.md`](docs/ION_Sector_B_Logistics.md)
3. **Learn catalog discovery patterns** — [`docs/ION_Sector_B_Logistics.md`](docs/ION_Sector_B_Logistics.md)
4. **Pick your spine**:

| Code | Archetype | Spine |
|---|---|---|
| LOG-HYPERLOCAL | Sub-day rider-based (GoSend, GrabExpress, Paxel) | `flows/logistics/spines/LOG-HYPERLOCAL/` |
| LOG-PARCEL | Hub-routed parcel, B2C and B2B (JNE, J&T, SiCepat) | `flows/logistics/spines/LOG-PARCEL/` |
| LOG-FREIGHT | Capacity-based freight (FTL/FCL/air/rail/river) | `flows/logistics/spines/LOG-FREIGHT/` |
| LOG-RORO | Self-accompanied cargo on Ro-Ro ferries | `flows/logistics/spines/LOG-RORO/` |
| LOG-XB | Cross-border with Bea Cukai customs | `flows/logistics/spines/LOG-XB/` |
| LOG-WAREHOUSE | Storage, FBA-style fulfilment, value-added services | `flows/logistics/spines/LOG-WAREHOUSE/` |

**LOG-PARCEL is the reference spine.** Every other spine is defined as a delta from it.

---

## Network-wide references

These apply to every sector:

- [`docs/ION_Layer_Model.md`](docs/ION_Layer_Model.md) — the 5-layer model, full explanation
- [`docs/ION_Beckn_Conformance.md`](docs/ION_Beckn_Conformance.md) — full conformance checklist: Beckn-native endpoints, ION extensions, attachment table for every pack
- [`docs/ION_Onboarding_and_Auth.md`](docs/ION_Onboarding_and_Auth.md) — subscriber registration, Ed25519 signing, CounterSignature, conformance testing
- [`docs/ION_Council_Open_Questions.md`](docs/ION_Council_Open_Questions.md) — v0.5.2-draft decisions awaiting ION Council ratification (registry naming, catalog split, L3 extensions upstream plan, schema.beckn.io import decision, etc.)
- [`docs/ION_Semantic_Model_Transition.md`](docs/ION_Semantic_Model_Transition.md) — v0.5 → v0.6 → v1.0 plan for JSON-LD vocabulary publishing at `schema.ion.id`

## Vocabulary publication — schema.ion.id

ION publishes its extension vocabulary at `https://schema.ion.id/`. Every pack in this repo under `schema/extensions/{layer}/{pack}/{version}/` has a dereferenceable URL at `https://schema.ion.id/{layer}/{pack}/{version}/`, and every term has a canonical IRI of the form `https://schema.ion.id/{layer}/{pack}/{version}#{term}`.

Beckn core transport types come from [`schema.beckn.io`](https://schema.beckn.io). ION extensions come from `schema.ion.id`. Beckn's domain-specific schemas (mobility, retail, DEG, etc.) are deliberately NOT imported — see [Q5 in ION_Council_Open_Questions.md](docs/ION_Council_Open_Questions.md) for rationale.

To rebuild the site locally: `python3 tools/build_schema_site.py` (output at `dist/schema.ion.id/`). To serve it for testing: `python3 tools/build_schema_site.py --serve`.

---

## What is in this repository

```
ion-network/
├── schema/
│   ├── core/v2/api/v2.0.0/
│   │   ├── ion.yaml                 ← L2 network profile overlay on Beckn
│   │   ├── ion-endpoints.yaml       ← L3 ION protocol endpoint extensions (/raise, /reconcile)
│   │   └── ion-with-beckn.yaml      ← composed spec (Beckn + ION), generated
│   └── extensions/
│       ├── core/                    ← L4 cross-sector attribute packs (11)
│       ├── trade/                   ← L5 trade sector packs (8)
│       ├── logistics/               ← L5 logistics sector packs (10)
│       └── {mobility,finance,tourism,healthcare}/  ← reserved
├── flows/
│   ├── trade/                       ← 13 spines + branches
│   ├── logistics/                   ← 6 spines + 13 branch families
│   └── {mobility,finance,tourism,healthcare}/  ← reserved
├── policies/                        ← ratified commercial & operational terms (16 categories)
├── errors/                          ← error registry (cross-sector + logistics)
├── docs/                            ← developer & conformance docs
└── tools/                           ← validate.py, generate_composed.py, generate_registry.py
```

Schema, flows, policies, and errors are designed to be read together. A spine in `flows/` references schema packs in `schema/`. An error entry in `errors/` references both a schema field and a flow step. The schema packs define field structure; the flows define which fields are required when; the policies define commercial terms; the errors define what the network rejects and why.

---

## Policy Terms Registry

Since v0.4, ION has a machine-enforceable policy model. Every offer declares policy IRIs that resolve to ratified terms documents; ION Central enforces at every API boundary.

Trade-originated categories (cross-sector where applicable):
- RETURN, CANCELLATION, WARRANTY, DISPUTE, GRIEVANCE_SLA, PAYMENT_TERMS, PENALTY

Logistics-originated categories (new in v0.5.2):
- EVIDENCE, INSURANCE, SLA, RE_ATTEMPT, WEIGHT_DISPUTE, LIABILITY, INCIDENT, RTS_HANDOFF, LOGISTICS_FWA

See [`policies/README.md`](policies/README.md) and [`policies/registry.json`](policies/registry.json).

---

## Mandatory Indonesian regulatory fields

These are network-mandated. A catalog or transaction missing any of these will be rejected by ION Central.

| Field | What it is | Required when | Format |
|---|---|---|---|
| `npwp` | Nomor Pokok Wajib Pajak | Always at confirm | 16 digits (post-2024 format per PMK 112/2022) |
| `nib` | Nomor Induk Berusaha | Always at confirm | 13 digits |
| `halalStatus` | MUI/BPJPH halal declaration | All food and beverage resources | `HALAL / HALAL_PENDING / NON_HALAL / NOT_APPLICABLE` |
| `halalCertNumber` | MUI halal cert number | When `halalStatus = HALAL` | Starts with ID |
| `countryOfOrigin` | Country of production | All resources | ISO alpha-3 (e.g. IDN) |
| `bpomRegNumber` | BPOM food/drug/cosmetic registration | All packaged food, personal care, pharma | `MD-` or `ML-` prefix |
| `ageRestricted` | Age verification flag | All resources | boolean |
| `name.id` | Bahasa Indonesia product name | All resources | Language object with `id` key |
| `contactDetailsConsumerCare` | Consumer care contact | All offers | name, email, phone comma-separated |

Tax rates (PPN, PPnBM, PPh) are **not hardcoded**. Implementations source the applicable rate from current Indonesian tax regulation (DJP / PMK). Current PPN standard is 11% under PMK 131/2024, but spec language treats this as illustrative, not prescriptive.

---

## Beckn Protocol

ION extends Beckn Protocol v2.0.0 without forking it. Core transport spec:
<https://github.com/beckn/protocol-specifications-v2>

`schema/core/v2/api/v2.0.0/ion.yaml` is the ION network profile overlay (L2). `schema/core/v2/api/v2.0.0/ion-endpoints.yaml` is the ION endpoint extensions spec (L3). Implementations must satisfy `beckn.yaml` + both ION files.

The composed spec `schema/core/v2/api/v2.0.0/ion-with-beckn.yaml` merges all three + every attribute pack (L4 + L5) into a single OpenAPI document. Run a standard OpenAPI validator against it to check Beckn conformance, ION profile conformance, and field-level correctness in one pass.

---

*ION Network Specification — v0.5.2-draft — April 2026*
