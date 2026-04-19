# ION — Indonesia Open Network

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Spec Version](https://img.shields.io/badge/Spec-v0.1.0--draft-orange.svg)](CHANGELOG.md)
[![Beckn](https://img.shields.io/badge/Beckn-v2.0.1-green.svg)](https://beckn.io)

Open network for digital commerce in Indonesia, built on Beckn Protocol v2.0.

ION lets any buyer app and any seller app transact with each other without bilateral integration. A seller onboarded to ION is instantly reachable by every buyer app on the network. A buyer app connected to ION can discover every seller — across Food, Grocery, Fashion, Electronics, Beauty, Agritech, Logistics, Mobility, Finance, and Services.

---

## How ION works — the architecture in 2 minutes

Before you write a single line of code, understand this. ION has two distinct phases and two distinct services. Getting this wrong wastes days.

**Phase 1 — Catalog (async, subscription-based)**

```
BPP publishes catalog → Catalogue Service (Beckn Fabric)
                                ↕
                        Discover Service
                        (hosted by ION  ←→  or hosted by BAP)
                                ↕
BAP subscribes → Discover Service → /on_discover → BAP pipeline
```

- **Catalogue Service** is hosted by Beckn Fabric. BPPs push their catalog here via `/publish_catalog`. This is the single store of all catalogs on the ION network.
- **Discover Service** sits between the Catalogue Service and BAPs. It takes subscriptions from BAPs and delivers matching catalogs via `/on_discover`. Three options exist — the right choice depends on your scale, control needs, and architecture:

| | Who hosts it | Characteristics |
|---|---|---|
| **Option 1 — ION shared DS** | ION Network | No infrastructure to run. Subscribe to ION's endpoint and start receiving catalogs. Simplest way to understand the flow end-to-end. |
| **Option 2 — BAP-hosted DS** | BAP themselves | Full control over filtering, ranking, and caching. BAP runs their own Discover Service instance connected to the Catalogue Service. |
| **Option 3 — Integrated** | BAP (vertically integrated) | BAP and BPP are the same organisation. Still formally subscribes — but to their own DS. |

> **If you are getting started and want to understand the flow:** Option 1 is the fastest path. Subscribe to ION's shared Discover Service, see catalogs arrive, then decide which option fits your production architecture.

- **In all three options, the BAP formally subscribes.** The subscription declares what you want (sector, category, location context). Delivery follows the standard `/on_discover` API into your discovery pipeline.
- **BPPs do not implement `/on_discover`**. They publish to the Catalogue Service via `/publish_catalog`. The Discover Service handles delivery to BAPs. BPP does not send `/on_discover` — it comes from the Discover Service.
- **BAPs do not query BPPs for catalog**. They subscribe once and receive catalog via `/on_discover` as BPPs publish and update.

**Phase 2 — Transaction (direct, BAP ↔ BPP)**

From `/select` onwards, the BAP talks directly to the BPP. No Catalogue Service. No Discover Service. Pure Beckn peer-to-peer.

```
BAP → /select  → BPP
BAP → /init    → BPP
BAP → /confirm → BPP
BAP → /status  → BPP
```

**The YAMLs in this repo cover Phase 2 in full.** The Phase 1 catalog structure (what BPPs publish, what BAPs receive in `/on_discover`) is documented in each YAML's `examples` section — but the routing through Catalogue Service and Discover Service is infrastructure, not something you implement in your application logic.

> **Open question — polygon matching location:** Does the GeoJSON serviceability polygon check (which BPP catalogs reach which BAPs based on consumer GPS) happen in the Catalogue Service, the Discover Service, or both? Pending ION Council decision. Flagged in the Atlas issue tracker.

---

## Before you start — two questions

## Building on ION — start with ONIX

ION provides **ONIX**, a reference implementation that handles the entire Beckn transport layer. It is strongly recommended for all developers building on ION.

**Download:** ION DevLabs — coming soon at `devlabs.ion.id`

**What ONIX handles for you — so you do not have to build it:**
- HTTP signatures on every request and response
- ACK/callback routing and async flow management
- Subscriber registry integration
- `/publish_catalog` to the Catalogue Service — BPP catalog publishing
- `/subscribe` to the Discover Service — BAP catalog subscription
- Request validation and error response formatting

**What you implement on top of ONIX — your actual business logic:**

| Role | What you build |
|---|---|
| **BPP developer** | Your catalog content (resources, offers, policies) · Transaction callback handlers (`on_select`, `on_init`, `on_confirm`, `on_status`) · Fulfilment state updates |
| **BAP developer** | Consumer search and discovery UI · Order flow and payment · `/on_discover` catalog indexing handler |

**The YAML specs in this repo are your reference for exactly what those callbacks should return and what the payloads look like.** ONIX handles the plumbing. The spec tells you what goes inside it.

You can build without ONIX — the spec is complete and implementation-agnostic. But ONIX saves weeks of transport layer work and ensures you are compliant with ION network requirements from day one.

---

## Before you start — two questions

**Are you building a BAP or a BPP?**

| | BAP — Buyer Application | BPP — Seller Application |
|---|---|---|
| **What it is** | The consumer-facing app | The seller or brand-facing app |
| **Examples** | A food delivery app, a grocery super-app, a marketplace | A restaurant ordering system, a brand catalog, a seller fulfillment backend |
| **What it does** | Sends requests (`/discover`, `/select`, `/init`, `/confirm`) | Responds to requests — returns catalog, computes price, creates contract, updates tracking |
| **You are building this if...** | You are building for consumers | You are building for a brand, store, or seller |

Both sides need to understand the full exchange — but you read it from your own perspective. Every YAML in this repo is annotated with `bap_action` and `bpp_action` per API call so you filter to exactly what applies to you.

**Do you have sandbox credentials?**

You need a `bap_id` / `bpp_id`, signing keys, and sandbox endpoint URL before you can send real requests. Contact the ION team to get these. You can read the specs and build your implementation without credentials — you just cannot test against the network yet.

→ *Sandbox registration: contact the ION team*

---

## The journey

### 1 — Orient: understand what ION adds on top of Beckn

You have worked with Beckn before and have context from ONIX. ION is a Beckn v2.0 network with Indonesian-specific extensions — regulatory fields, local payment rails, Indonesian commerce patterns, and a governed field layer on top of the standard Beckn envelope.

Read the Trade Model. It covers:
- The six ION objects: Resource, Offer, Commitment, Consideration, Contract, Performance
- Indonesian regulatory fields and which laws drive them
- Commerce patterns ION supports — single fulfilment, make-to-order, B2B, subscription, and more
- Performance lifecycle and settlement model

**Time:** 30 minutes. Read once. Refer back to specific sections as you build.

→ [`docs/ION_Sector_A_Trade.md`](docs/ION_Sector_A_Trade.md)

---

### 2 — Pick your YAML

Find the file that matches your category. If yours is not listed yet, the closest one shows the pattern — the regulatory fields and resource structure are the main differences between categories.

| File | Category | Key patterns in this example |
|---|---|---|
| [`specs/A01_B2C_MTO_FoodQSR_DominosJakarta.yaml`](specs/A01_B2C_MTO_FoodQSR_DominosJakarta.yaml) | Food & QSR | Multi-store brand, composed resource (pizza = mandatory size + crust + optional toppings), BPP self-fulfilment, central invoicing, per-store GeoJSON delivery zones |
| [`specs/A02_B2C_SF_Grocery_IndomieToko.yaml`](specs/A02_B2C_SF_Grocery_IndomieToko.yaml) | Grocery / FMCG | Plain and variant resources, BPOM MD registration, halal cert, SNI, allergen declaration, PPN 11% |
| [`specs/A03_B2C_SF_Fashion_BatikKeris.yaml`](specs/A03_B2C_SF_Fashion_BatikKeris.yaml) | Fashion / Apparel | Size variants with measurements in cm, batik motif field, fabric composition, care instructions, national courier delivery |
| [`specs/A04_B2C_SF_Electronics_SamsungA55.yaml`](specs/A04_B2C_SF_Electronics_SamsungA55.yaml) | Electronics | Storage/RAM/colour variants, POSTEL registration, TKDN local content %, 1-year warranty (legal minimum), 2-day return with video unboxing evidence |
| [`specs/A05_B2C_SF_Beauty_WardahLipCream.yaml`](specs/A05_B2C_SF_Beauty_WardahLipCream.yaml) | Beauty / Cosmetics | Shade variants with hex codes, BPOM NA notification registration, halal cert, skin type, non-returnable hygiene policy |
| [`specs/A07_B2C_SF_Agritech_BerasPandanWangi.yaml`](specs/A07_B2C_SF_Agritech_BerasPandanWangi.yaml) | Agritech / Produce | Weight variants, Kementan PD registration, produce grade, milling date, PPN-exempt sembako (PP 49/2022) |

---

### 3 — Read your YAML, by role

Each YAML is a complete implementation guide for one commerce pattern. Here is how to navigate it.

**Start with `participants`**

Find `participants` near the top. It lists your responsibilities and — equally important — your must-nots. Read your side only. This is your implementation checklist.

**Understand the flow — `flow.apis[]`**

Every API call has role annotations:

```yaml
- api: on_discover
  bap_action: RECEIVE      # BAP: you receive this and parse the catalog
  bpp_action: SEND         # BPP: you build and send this response
```

As a BAP — focus on `bap_action: SEND` (what you send) and `bap_action: RECEIVE` (what you get back and must parse).

As a BPP — focus on `bpp_action: RECEIVE` (what is coming in that you must validate) and `bpp_action: SEND` (what you must return).

**Read the examples — `examples[]`**

Every API call has a complete payload. Each example is tagged:

```yaml
_role_meta:
  sent_by: BPP
  received_by: BAP
  bap_action: RECEIVE
  bpp_action: SEND
```

Copy the example for your call and your role. Replace values with your real data. The examples use real Indonesian businesses, real Jakarta addresses, and realistic IDR prices — they are designed to be adapted directly, not just read.

**Find field ownership — `_*_field_roles` sections**

Four dictionaries at the end of each YAML map every field to its role metadata:

```yaml
_offer_attribute_field_roles:
  fields:
    cancellation_policy:
      declared_by: BPP        # BPP sets this — declare the IRI in your catalog
      consumed_by: [BAP, ION] # BAP renders it; ION Central enforces it
      enforced_by: ION        # You declare it correctly; ION enforces the terms
    cancellable:
      declared_by: BPP
      consumed_by: BAP
      note: UI HINT — BAP shows or hides cancel button based on this value
```

`declared_by` — who sets the value. `consumed_by` — who reads and acts on it. `enforced_by: ION` — ION Central validates this server-side. You must declare it correctly but you do not implement the enforcement yourself.

**Check validation — `validation` section**

Lists everything ION Central enforces, with the error code it returns. As a BPP, these are the rules you must satisfy or your responses are rejected. As a BAP, these tell you what errors you will receive and why.

---

### 4 — Build. When you hit an error, look it up here.

→ [`errors/ion_error_registry.json`](errors/ion_error_registry.json)

Every ION error code is in this file with: what triggered it, which field is wrong, and exactly what to change to fix it.

The ones you will most likely hit first:

| Code | When it fires | What to do |
|---|---|---|
| `ION-4010` | BAP sent /select without completing a SINGLE_REQUIRED customisation group | Enforce mandatory groups in your UI before allowing /select |
| `ION-5001` | BPP returned a provider whose polygon does not contain the consumer GPS | Run a point-in-polygon check before including a provider in on_discover |
| `ION-5002` | `fulfillingLocationId` appeared in on_discover, on_select, or on_init | Move it to on_confirm only — it is a contract field, not a catalog field |
| `ION-5010` | No TAX_PPN line in quote breakup | Add TAX_PPN at 11% of item subtotal to every on_select, on_init, on_confirm |
| `ION-5020` | BPOM registration missing on a food or personal care resource | Add `bpomRegistrationNumber` — mandatory for all packaged food and personal care |
| `ION-5030` | POSTEL registration missing on a telecom device | Add `postelRegistration` — mandatory for all mobile phones and telecom equipment |

---

### 5 — Reference the Dictionary when you need field detail

When you need the exact type, format, valid enum values, mandatory condition, or Indonesian regulatory source for a specific field — the Dictionary is your reference.

→ [`docs/ION_Trade_Dictionary.xlsx`](docs/ION_Trade_Dictionary.xlsx)

Covers all 126 finalised ION Trade fields grouped by Beckn object. Open it alongside your YAML, not before it.

**Language pattern** — every human-facing text field uses a language object:

```json
{ "id": "Bahasa Indonesia teks", "en": "English text" }
```

The `id` key (Bahasa Indonesia) is always mandatory. The `en` key is mandatory when `displayLanguage` includes `"en"`. Adding other ISO 639-1 keys (e.g. `zh`, `ar`) requires no schema change.

---

### 6 — Understand Atlas when you are ready to go deeper

After you have started building, read the Atlas Orientation. It explains:
- Where these specs come from (Atlas is the schema registry that generates the YAMLs and Dictionary)
- How to propose a new field and get it ratified
- Where AutoPilot developer tooling is heading — and what your early builds contribute to it

→ [`docs/ION_Atlas_Developer_Orientation.md`](docs/ION_Atlas_Developer_Orientation.md)

---

### 7 — Found a gap? Contribute.

If you find a missing field, a wrong example, an edge case the YAML does not cover, or an error code missing from the registry — raise it. Your real implementation experience resolves the open questions faster than any design review.

→ [`CONTRIBUTING.md`](CONTRIBUTING.md)

Use the GitHub Issue templates. ION Council working group reviews proposals fortnightly.

---

## ION object model — quick reference

| Object | What it is | Declared by | Appears in |
|---|---|---|---|
| **Resource** | The thing being sold | BPP | on_discover |
| **Offer** | Terms on a Resource — price, policy, availability | BPP | on_discover |
| **Commitment** | Buyer's selection — links Resource + Offer | BAP | /select |
| **Consideration** | Price breakdown — ITEM, DELIVERY, TAX_PPN | BPP | on_select, on_confirm |
| **Contract** | Confirmed agreement — immutable after on_confirm | BPP | on_confirm |
| **Performance** | Fulfilment tracking — state, agent, proof | BPP | on_status |

---

## Mandatory Indonesian regulatory fields

Get these right or your catalog will be rejected.

| Field | What it is | Required when | Format |
|---|---|---|---|
| `nib` | Nomor Induk Berusaha | Always | 13 digits |
| `npwp` | Tax identity | Always | 16 digits (post-2024 format) |
| `halalCertNumber` | MUI / BPJPH halal cert | `dietaryClassification: HALAL` | Starts with ID |
| `bpomRegistrationNumber` | BPOM MD/ML food registration | All packaged food and personal care | `MD` or `ML` + 12 digits |
| `bpomNaRegistration` | BPOM NA cosmetics notification | All cosmetics | `NA` + 11 digits |
| `postelRegistration` | Kominfo device certification | All telecom devices | `XXXXX/SDPPI/YYYY` |
| `kementanPdRegistration` | Kementan agricultural registration | All raw agricultural produce | Varies by province |

---

## Standard policy IRIs

Declare these in `offerAttributes`. ION Central enforces the terms — you declare, ION enforces.

```
ion://policy/return.7d.sellerpays      7-day return window, seller pays shipping
ion://policy/return.none               Non-returnable
ion://policy/cancel.prepacked.free     Free cancellation before PACKED state
ion://policy/cancel.none               No cancellation (made-to-order)
ion://policy/warranty.1y.manufacturer  1-year manufacturer warranty
ion://policy/warranty.none             No warranty
ion://policy/dispute.consumer.bpsk     B2C dispute via BPSK
ion://policy/dispute.commercial.bani   B2B dispute via BANI
```

---

## API coverage by version

ION is being built incrementally. The table below shows which API groups are in the current release and what is coming next. Build against what is marked **v0.1 — Stable**. The v0.2 group is actively being built and will land in the coming weeks — you will get notice via this repo when specs and sandbox support are ready.

| API group | APIs | v0.1 — Current | v0.2 — In development |
|---|---|---|---|
| Discovery | `/discover` `/on_discover` | ✅ Stable | — |
| Transaction | `/select` `/on_select` `/init` `/on_init` `/confirm` `/on_confirm` | ✅ Stable | — |
| Fulfilment | `/status` `/on_status` `/update` `/on_update` `/cancel` `/on_cancel` | ✅ Stable | — |
| Tracking | `/track` `/on_track` | — | 🔶 In development |
| Settlement | `/reconcile` `/on_reconcile` | — | 🔶 In development |
| Dispute & support | `/support` `/on_support` (RaisedMatter) | — | 🔶 In development |
| Rating | `/rate` `/on_rate` | — | 🔶 In development |

Full version history and what each release adds: [`CHANGELOG.md`](CHANGELOG.md)

**If you are building a BAP today** — implement discovery through confirmation and status. Tracking, reconciliation, dispute, and rating flows are not specced yet. Stubs are fine. You will not break your existing implementation when v0.2 lands — it adds callbacks, it does not change existing ones.

**If you are building a BPP today** — implement catalog publication, the confirm flow, and performance state updates (PENDING → PACKED → DISPATCHED → DELIVERED). Settlement reconciliation and dispute handling will be added as separate callback handlers in v0.2.

---

## What is available now

| Commerce Pattern | Category | YAML |
|---|---|---|
| B2C Make-to-Order | Food & QSR | ✅ A01 |
| B2C Single Fulfilment | Grocery / FMCG | ✅ A02 |
| B2C Single Fulfilment | Fashion | ✅ A03 |
| B2C Single Fulfilment | Electronics | ✅ A04 |
| B2C Single Fulfilment | Beauty | ✅ A05 |
| B2C Single Fulfilment | Agritech | ✅ A07 |
| B2C Subscription | All | 🔶 Coming |
| B2B Wholesale | All | 🔶 Coming |
| Logistics — domestic | Domestic surface, hyperlocal | 🔶 Coming |
| Mobility | Ride hailing | 🔶 Coming |
| Services | Home services | 🔶 Coming |

---

*ION Network Specification — v0.1.0-draft — April 2026*
