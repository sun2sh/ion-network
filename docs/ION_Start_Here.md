# Start Here — What is ION?

**10-minute read. Assumes you've never heard of ION, Beckn, or commerce protocols.**

If you're an experienced Beckn developer, skip this and go straight to [`ION_Developer_Orientation.md`](ION_Developer_Orientation.md).

---

## The 30-second answer

**ION is an open network for digital commerce in Indonesia.** Any app that sells things (a marketplace, a merchant site, a fleet operator) can connect to any app that helps sell things (a delivery company, a warehouse, a payment provider) — without building a custom integration for each partner.

Think of email. You use Gmail, your friend uses Outlook, your colleague uses Apple Mail. You all send each other email because SMTP is a standard. You don't need Gmail-to-Outlook adapters.

ION is the equivalent for commerce transactions in Indonesia. One app speaks ION; every other app on ION understands it.

---

## Who ION is for

Two kinds of players connect to ION:

- **Buyer-side apps (BAP)** — Tokopedia, Shopee, Lazada, a restaurant's mobile app, a corporate procurement platform. Anywhere a buyer finds products or books services.
- **Seller-side apps (BPP)** — a merchant's e-commerce site, JNE for parcel delivery, a warehouse operator, an LSP (logistics service provider), a B2B wholesaler. Anywhere goods and services are offered.

**BAP** = Beckn Application Platform (the buyer app).
**BPP** = Beckn Provider Platform (the seller app).

You're likely building one of these. Which one decides which sector doc you read next.

---

## How it works (high level)

Here's what happens when someone buys a pair of shoes on Tokopedia from a Jakarta seller with JNE delivery:

```
  Consumer                              ION Network
  taps "buy"
     ↓
┌─────────┐                      ┌─────────────────┐
│  BAP    │ ────/select────────→ │  BPP (seller)   │  "Reserve 1 pair, size 42"
│ Tokope- │                      └─────────────────┘
│  dia    │ ←──/on_select────────────── "Reserved. Total IDR 500k."
│         │                      ┌─────────────────┐
│         │ ────/select────────→ │  BPP (JNE)      │  "Quote me for delivery"
│         │ ←──/on_select────────────── "IDR 15k, next-day"
│         │
│         │ ────/init──→ seller     "Lock in the shoe"
│         │ ←──/on_init── seller     "Locked. Payment link: XYZ"
│         │
│         │ ────/confirm──→ seller   "Payment done, ship it"
│         │ ←──/on_confirm── seller  "Confirmed. Order ID: ORD-123"
│         │ ────/confirm──→ JNE      "Ship this order"
│         │ ←──/on_confirm── JNE     "Booked. AWB: JNE-456"
│         │
│         │ ←──/on_status── JNE      "Picked up"    (pushed as events happen)
│         │ ←──/on_status── JNE      "In transit"
│         │ ←──/on_status── JNE      "Delivered"
└─────────┘                      └─────────────────┘
```

Every arrow is an HTTP call. Messages carry structured JSON. Every participant signs every message cryptographically so no one can forge.

That's the whole picture. The rest is detail.

See [`ION_First_Transaction.md`](ION_First_Transaction.md) for the actual messages exchanged, field by field.

---

## How ION is put together

ION is built on top of an existing open protocol called **Beckn Protocol v2.0.0**. Beckn defines the message envelope (what a commerce message looks like, how participants sign it, how acknowledgements work). ION adds Indonesian-specific fields (tax IDs, address hierarchy, payment rails) and sector-specific fields (logistics rate cards, trade commerce patterns) on top.

There are five logical layers, but you only ever write code against three of them:

| Layer | What it is | Who owns it | Do you write code for it? |
|---|---|---|---|
| **L1** — Beckn core | Message envelope, transport, signing | Beckn Foundation | No, you use it |
| **L2** — ION network profile | Indonesian overrides, mandatory actions | ION Network | No, you comply with it |
| **L3** — ION protocol extensions | `/raise` (disputes), `/reconcile` (settlement) | ION Network | Yes, if you handle these |
| **L4** — ION core attributes | Participant fields, tax, address, payment | ION Network | Yes, you fill these in every message |
| **L5** — ION sector attributes | Trade / Logistics-specific fields | ION Network | Yes, based on your sector |

If this layering is confusing now, skip it. Come back after you've read your sector doc. The full explanation is in [`ION_Layer_Model.md`](ION_Layer_Model.md).

### One rule that spans all layers

ION messages carry JSON-LD `@context` declarations. **Only two context roots are valid:**

- `https://schema.beckn.io/core/v2.0.0/` — Beckn's core vocabulary (envelope, object model). Owned by Beckn Foundation.
- `https://schema.ion.id/{layer}/{pack}/{version}/` — ION's vocabulary (all extensions, policies, states). Owned by ION Network.

Any other `@context` (Beckn's domain modules, other networks' vocabularies) is rejected at the ION Central gate. See [`ION_Council_Open_Questions.md`](ION_Council_Open_Questions.md) Q5 for the rationale. See [`ION_First_Transaction.md`](ION_First_Transaction.md) for this rule in action across a real transaction.

---

## The six docs you'll read (in order)

You don't read everything. Here's the actual reading order based on your role:

### If you're building a BAP or BPP

1. **This doc** — you're here
2. **[`ION_Glossary.md`](ION_Glossary.md)** — bookmark it, you'll come back constantly
3. **[`ION_Developer_Orientation.md`](ION_Developer_Orientation.md)** — cross-sector concepts (two-phase architecture, signing, policies). 40 min read.
4. **Your sector doc** — either [`ION_Sector_A_Trade.md`](ION_Sector_A_Trade.md) (if you sell goods/services) or [`ION_Sector_B_Logistics.md`](ION_Sector_B_Logistics.md) (if you move things)
5. **[`ION_First_Transaction.md`](ION_First_Transaction.md)** — a real end-to-end walkthrough. Most useful when you're about to code.
6. **[`ION_Onboarding_and_Auth.md`](ION_Onboarding_and_Auth.md)** — how to actually register, sign messages, and go live. Read when you're ready to implement.

### If you're a product manager or analyst

1. **This doc**
2. **[`ION_Glossary.md`](ION_Glossary.md)**
3. **[`ION_Sector_A_Trade.md`](ION_Sector_A_Trade.md)** §1 *or* **[`ION_Sector_B_Logistics.md`](ION_Sector_B_Logistics.md)** §1 — scope of your sector

### If you're doing conformance testing

1. This doc
2. [`ION_Beckn_Conformance.md`](ION_Beckn_Conformance.md) — the 15-point checklist

---

## What ION is not

- **Not a platform.** ION doesn't host shops or accept orders. ION is a set of standards that apps implement.
- **Not a single company.** The ION Network is governed by ION Council. No single company owns or controls it.
- **Not a consumer app.** Consumers don't download ION. They use Tokopedia, Shopee, or any BAP that speaks ION behind the scenes.
- **Not a replacement for Beckn.** ION is built on Beckn. ION participants are Beckn participants.
- **Not a payments network.** ION carries payment metadata (which rail, what amount), but actual money movement goes through QRIS, BI-FAST, or bank transfer outside ION.

---

## A word on the Indonesian bits

ION is deliberately Indonesian. You'll see references to:

- **NPWP** — 16-digit tax ID (every business)
- **NIB** — 13-digit business registration
- **PKP** — VAT registration status
- **PPN** — VAT (standard rate is 11% per PMK 131/2024, but check current regulation)
- **QRIS, BI-FAST** — Indonesian payment rails
- **Provinsi, Kabupaten, Kecamatan, Kelurahan, RT/RW** — administrative hierarchy down to neighborhood-group level
- **Bea Cukai** — customs authority (matters for cross-border)
- **DJP** — tax authority
- **Kominfo** — ministry of communications (data residency regulation)

These are non-negotiable. If you're building for Indonesia, you need to handle them. If you're building for a different country and want to adapt ION, you'll replace these with your country's equivalents.

---

## The common questions people ask at this point

**"Do I have to support every endpoint in the spec?"**
No. ION defines mandatory actions per role (BAP vs BPP) and per sector. Most BPPs never implement `/raise` (that's for disputes). Most BAPs don't handle state-machine callbacks for flows they don't initiate. Mandatory lists are in `ion.yaml → x-ion-actions`.

**"Why aren't there `/search` and `/on_search` endpoints?"**
Beckn v2.0.0 replaced `/search` with `/discover` (active query) and `/catalog/subscription` (push model). Discovery works differently now — BPPs publish catalogs continuously, BAPs subscribe or query. See [`ION_Developer_Orientation.md`](ION_Developer_Orientation.md) §3.

**"What does ION cost?"**
The protocol is free and open. ION Network operational fees (if any) and participant registration fees are set by ION Council. Commercial terms between BAP and BPP are negotiated between them (or governed by a Framework Agreement for enterprise relationships).

**"Can I test without registering?"**
Yes. ION provides a sandbox. Messages carry `context.try=true` to indicate sandbox mode. You build against the sandbox, validate conformance, then apply for production registration.

**"Does ION work outside Indonesia?"**
The protocol is exportable — the Beckn core is universal, and ION's extensions are clearly Indonesian. Another country could publish its own network (e.g., "ION-Thailand") using a similar structure. But the `schema.ion.id/` vocabulary is specifically Indonesia's.

**"How do I actually run a test message?"**
Install ONIX (the reference implementation):
```bash
npm install -g @beckn/onix
onix init my-bap
# see ION_Developer_Orientation.md §4 for the full walkthrough
```

---

## Next step

Open [`ION_Glossary.md`](ION_Glossary.md) now. Scan it once so the acronyms in other docs don't surprise you. Then go to [`ION_Developer_Orientation.md`](ION_Developer_Orientation.md).

If you're impatient to see a real transaction, skip ahead to [`ION_First_Transaction.md`](ION_First_Transaction.md) — it's readable on its own.

---

*Last updated v0.5.2-draft.*
