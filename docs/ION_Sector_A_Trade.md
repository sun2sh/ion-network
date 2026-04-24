# ION Sector A — Trade

Trade covers all physical goods commerce on ION — Food & Beverage, Grocery, Fashion, Electronics, Beauty, FMCG, Agritech, Pharmacy, Home & Kitchen, and B2B/Wholesale distribution. If it is a physical product being bought and sold in Indonesia, it belongs in Trade.

---

## 1. Choosing the right commerce pattern

Read the description for each pattern and pick the one that matches how your business actually operates. The differences matter — they determine which fields are required, which branches apply, and how settlement works.

| Pattern | Use when | Key indicator |
|---|---|---|
| **B2C-SF** | Consumer buys a product, delivery or pickup | The default. Start here. |
| **B2C-MTO** | Product is prepared after the order (food QSR, tailoring) | `preparationTime` per item; cancellation closes when preparation starts |
| **B2C-SUB** | Consumer subscribes to recurring delivery | Billing cycle; mandate setup; pause/skip/resume lifecycle |
| **B2C-LIVE** | Order placed during live stream, short video, OTT shoppable moment, affiliate link, group buy | `liveCommerceContext` with source channel + streamer/OTT attribution; flash-style reservation; commission breakup |
| **B2C-DIG** | Digital goods — pulsa, PLN tokens, bill pay, vouchers, gift cards, game currency, streaming access | No shipping; fast fulfilment (<10s typical); target identifier required; `digital` sub-object |
| **B2B-PP** | Business buys wholesale, pays upfront | MOQ; bulk pricing tiers; PO reference; Faktur Pajak mandatory |
| **B2B-CR** | Business buys wholesale, pays in N days | `creditTermsDays`; `paymentDueDate`; dunning flow; settlement after due date |
| **MP-IH** | Marketplace holds physical stock (1P or consignment) | Single BPP represents multiple brands; marketplace FC as origin |
| **MP-IL** | 3P marketplace — sellers hold own inventory | Each seller = independent BPP; marketplace = BAP; PLATFORM_FEE in breakup |
| **AUC-F** | Forward auction — buyers bid up | `/select` = bid submission; highest bid wins |
| **AUC-R** | Procurement/reverse auction — sellers bid down | `/discover` = RFQ publication; lowest bid wins |
| **XB** | Export to international buyer | English catalog required; HS codes; Bea Cukai; PEB |
| **B2G** | Sale to government entity | SP/SPK; DIPA; TKDN; BAST; SP2D; PPh22 withholding |

---

## 2. Indonesian regulatory requirements for Trade

These are network-mandated — not optional. A catalog that violates any of these will fail ION Central validation.

### Product-level requirements

| Requirement | What to declare | Regulatory basis |
|---|---|---|
| Halal status | `halalStatus` on every food/beverage resource | UU 33/2014 tentang Jaminan Produk Halal |
| BPOM registration | `regulatory.registrations[scheme=BPOM_MD/ML]` | PerBPOM 27/2017 |
| Country of origin | `countryOfOrigin` (ISO alpha-3) on every resource | PerBPOM 31/2018 Pasal 36 |
| Packaged goods label | `packaged.netQuantity`, `manufacturerOrPacker`, `expiryDate` | PerBPOM 31/2018 |
| Electronics warranty | `warranty.duration` minimum P1Y | UU 8/1999 Pasal 25; PP 36/2023 |
| Age restriction | `ageRestricted` and `minAge` on restricted products | PP 109/2012 |
| Bahasa Indonesia | `name.id` and `shortDesc.id` on every resource | ION Network Policy |

### Offer-level requirements

| Requirement | What to declare | Regulatory basis |
|---|---|---|
| Return rights | `returnable`, `returnAllowedReasons[]`, `returnPolicy` | UU 8/1999 Pasal 19 |
| Cancellation terms | `cancellable`, `cancellationPolicy` | UU 8/1999 Pasal 19 |
| Consumer care contact | `contactDetailsConsumerCare` (name, email, phone) | UU 8/1999 Pasal 7 |
| Dispute resolution | `disputePolicy` IRI | UU 8/1999 Pasal 45; UU 30/1999 |
| Warranty policy | `warrantyPolicy` IRI | UU 8/1999 Pasal 25 |

### Transaction-level requirements

| Requirement | What to declare | When | Regulatory basis |
|---|---|---|---|
| Seller NPWP | `contractAttributes.npwp` (16 digits) | confirm / on_confirm | PMK 136/2023 |
| Seller NIB | `contractAttributes.nib` (13 digits) | confirm / on_confirm | PP 5/2021 |
| PKP status | `identity.pkpStatus` | onboarding | UU 8/1983 |
| PPN (current standard rate, e.g. 11%) | `considerationAttributes.ppnRate` set to the applicable decimal (e.g. 0.11 under PMK 131/2024 — source from DJP) | on_select breakup | UU 7/2021 HPP; current applicable PMK |
| Faktur Pajak | `contractAttributes.fakturPajakReference` | on_confirm (PKP sellers) | PMK 168/2023 |

---

## 3. Schema pack composition for Trade

### Publishing a catalog (publish_catalog)

```
providers[].providerAttributes:
  ← core/identity/v1        NPWP, NIB, PKP status, legal entity name
  ← trade/provider/v1       storeStatus, operatingHours, providerCategory, invoicingModel

providers[].items[].resourceAttributes:
  ← core/localization/v1    name.id, shortDesc.id (language objects)
  ← core/product/v1         halalStatus, bpomRegNumber, ageRestricted
  ← trade/resource/v1       resourceType, availability, images, countryOfOrigin
                             + category sub-object (food / electronics / fashion / etc.)

providers[].offers[].offerAttributes:
  ← trade/offer/v1          cancellable, returnable, returnPolicy, cancellationPolicy,
                             warrantyPolicy, disputePolicy, timeToShip, availableOnCod,
                             returnAllowedReasons, contactDetailsConsumerCare
```

### select → on_select

```
on_select adds:
  quote.breakup[].considerationAttributes:
    ← core/tax/v1            ppnRate on TAX lines (applicable decimal, e.g. 0.11), taxIncluded
    ← trade/consideration/v1 breakupLineType (ITEM/DELIVERY/TAX/PROVIDER_BENEFIT/etc.)

  performance[].performanceAttributes:
    ← trade/performance/v1   supportedPerformanceModes[], sla, handling[]
```

### init → on_init

```
init adds:
  performance[].performanceAttributes.stops[].location:
    ← core/address/v1        provinsiCode, kelurahan, kecamatan, RT, RW

  payment:
    ← core/payment/v1        PaymentDeclaration (method, collectedBy, timing)

  contractAttributes:
    ← trade/contract/v1      invoicePreferences, deliveryPreferences, gift

on_init adds:
  payment.settlement_details[]:
    ← core/payment/v1        QRIS string / VA number / EWallet deep link
```

### confirm → on_confirm

```
confirm adds:
  contractAttributes:
    ← core/identity/v1       npwp, nib (buyer and seller)
    ← trade/contract/v1      purchaseOrderReference (B2B), subscriptionBillingCycle (SUB)

on_confirm adds:
  contractAttributes:
    ← trade/contract/v1      fulfillingLocationId
    ← core/identity/v1       fakturPajakReference (PKP sellers)
```

### on_status (during fulfilment)

```
on_status[DISPATCHED] adds:
  performance[].performanceAttributes:
    ← trade/performance/v1   awbNumber, trackingUrl, estimatedDeliveryTime,
                             agentName, agentPhone, agentPhoto

on_status[DELIVERED] adds:
  ← trade/performance/v1    deliveryProofUrl (if PHOTO type)
  Contract status → COMPLETE
```

### Post-delivery

```
rate:
  ← core/rating/v1          ratingCategory (PROVIDER/ITEM/FULFILLMENT/AGENT), ratingValue

reconcile:
  ← core/reconcile/v1       reconId, amounts, adjustments[], reconStatus

support:
  ← core/support/v1         SupportTicket (category, description, issueActions)

raise:
  ← core/raise/v1           IONTicket (type, priority, thread) — participant → ION
```

---

## 4. Availability model

Stock count is never transmitted over ION. The BPP manages actual inventory internally. What the network carries is a signal:

```json
"availability": {
  "status": "IN_STOCK",          // or LOW_STOCK / OUT_OF_STOCK / PREORDER / DISCONTINUED
  "maxOrderQty": 10,             // per-order cap — NOT stock count
  "nextAvailableAt": "...",      // for PREORDER or OUT_OF_STOCK with restock date
  "backorderAllowed": false,
  "preorderAllowed": true,
  "substitutionAllowed": false
}
```

`LOW_STOCK` is a BAP signal only — BAP may show urgency messaging ("only a few left"). The BPP decides when to flip from IN_STOCK to LOW_STOCK based on its own thresholds.

---

## 5. Resource type model

Every resource must declare its structural type. This determines which other fields are required.

**PLAIN** — A single SKU. No choices. Buyer just buys it.
```
Required: images[], availability.status, countryOfOrigin, logisticsServiceType, ageRestricted
```

**VARIANT** — One option in a family. Size M is a VARIANT of a base pizza.
```
Additional required: parentResourceId, variantGroup{id, name, variantOn}, isDefaultVariant
```

**WITH_EXTRAS** — Base item plus optional add-ons.
```
Additional required: customisationGroups[] with SINGLE_OPTIONAL or MULTIPLE_OPTIONAL groups
```

**COMPOSED** — Base item with mandatory and optional choice groups. Build-your-pizza.
```
Additional required: customisationGroups[] including at least one SINGLE_REQUIRED group
```

---

## 6. Performance state machines

ION Trade defines six canonical state machines. Choose based on your fulfilment mode:

| Machine | When to use |
|---|---|
| **standard** | All packaged goods delivery — FMCG, electronics, fashion, agritech |
| **mto** | Made-to-order — food QSR, bakery, tailoring |
| **self_pickup** | Consumer collects from seller location |
| **return** | Post-delivery return flow |
| **replacement** | Seller sends replacement instead of refund |
| **rto** | Delivery failed — package returning to seller |

Full state definitions and allowed transitions: `schema/extensions/trade/performance-states/v1/states.yaml`

---

## 7. Policy IRI reference

ION uses IRI strings for standardised policies. This makes policies machine-readable and removes ambiguity from free-text policy descriptions.

**Return policies** (`offerAttributes.returnPolicy`)
- `ion://policy/return.7d.sellerpays` — 7-day window, seller arranges and pays for return pickup
- `ion://policy/return.15d.sellerpays` — 15-day window, seller pays
- `ion://policy/return.30d.sellerpays` — 30-day window, seller pays
- `ion://policy/return.7d.buyerpays` — 7-day window, buyer ships back at own cost
- `ion://policy/return/standard/none` — no returns accepted

**Cancellation policies** (`offerAttributes.cancellationPolicy`)
- `ion://policy/cancel/prepacked/free` — Free cancellation before packed state
- `ion://policy/cancel/mto/nofee-before-prepare` — MTO: free before preparation starts
- `ion://policy/cancel/standard/none` — No cancellation permitted after confirm

**Warranty policies** (`offerAttributes.warrantyPolicy`)
- `ion://policy/warranty.1y.manufacturer`
- `ion://policy/warranty.2y.manufacturer`
- `ion://policy/warranty.3y.manufacturer`
- `ion://policy/warranty.1y.seller`
- `ion://policy/warranty/standard/none`

**Dispute policies** (`offerAttributes.disputePolicy`)
- `ion://policy/dispute/consumer/bpsk` — B2C disputes via BPSK (Badan Penyelesaian Sengketa Konsumen)
- `ion://policy/dispute/commercial/bani` — B2B disputes via BANI arbitration
- `ion://policy/dispute/commercial/odr` — Online Dispute Resolution via ION platform

---


---

## Using Atlas to look up fields

When you need to find a field by describing what it does in plain English — rather than already knowing the field name — use ION Atlas.

```bash
ion search "halal certification number"
ion search "government purchase order reference"
ion search "delivery agent phone number"
ion search "BPOM food registration"
ion search "credit terms days"
```

Atlas searches all ION and Beckn core schemas semantically. It tells you which pack contains the field, what the field is called, and its regulatory basis — all in one result.

Before adding a new field to a schema pack, always run:
```bash
ion validate yourProposedFieldName
```

This checks for clashes with reserved Beckn terms and near-matches in existing packs.

Web Explorer: `schema.ion.id/atlas` (coming soon)



## 7b. Policies and penalties

Every offer declares policy IRIs. These are not free text — they reference ratified terms documents in the ION Policy Terms Registry. Sellers pick from a menu; ION Central enforces the terms.

### Policy categories (7)

| Category | Purpose | Who selects | Ratified set size |
|---|---|---|---|
| RETURN | Return window, reasons, evidence, QC, refund timeline | Seller | 15 |
| CANCELLATION | Cancellation window, fee, reasons, refund % | Seller | 10 |
| WARRANTY | Warranty type, duration, coverage, service mode | Seller (or brand) | 8 |
| DISPUTE | Where disputes resolve (BPSK / BANI / ODR / UNCITRAL / LKPP) | Seller | 5 |
| GRIEVANCE_SLA | Response + resolution SLA, escalation path, breach consequences | Seller subject to marketplace minimum | 4 |
| PAYMENT_TERMS | Payment timing, methods, deposit/credit, late fees | Seller (BAP may constrain) | 8 |
| PENALTY | Fee schedules for violations — referenced by other policies | Auto-derived from seller tier | 17 |

Registry total: **67 ratified policy documents** as of v0.4.

### Declaring policies on an offer

```
offerAttributes:
  returnPolicy:       ion://policy/return/standard/7d-sellerpays
  cancellationPolicy: ion://policy/cancel/prepacked/free
  warrantyPolicy:     ion://policy/warranty/manufacturer/1y-distance-service
  disputePolicy:      ion://policy/dispute/consumer/bpsk
  grievanceSlaPolicy: ion://policy/grievance-sla/consumer/standard
  paymentTermsPolicy: ion://policy/payment-terms/upfront/full
  customTermsAddendum: "Optional seller-specific addendum text (max 1000 chars)."
```

Each spine declares which policy categories are required. For example:

- B2C-SF: all six categories required
- B2C-MTO: cancellation + dispute + grievance-sla + payment-terms (no returns for prepared food; no manufacturer warranty)
- B2C-DIG: cancellation + dispute + grievance-sla + payment-terms (digital goods, no returns or warranty)

See each spine's `profile.json` for the `requiredPolicyCategories` list.

### Versioning

ION Council ratifies one version of the registry at a time. New versions announced with 90 days notice, all sellers auto-upgrade on cutover. No per-seller version pinning.

### Penalty policies

Sellers are onboarded into a tier (Standard, Mall, Premium). Each tier has a minimum penalty commitment for grievance SLA breaches:

- Standard: `penalty.seller.sla_breach.standard`
- Mall: `penalty.seller.sla_breach.mall` (stricter)
- Premium: `penalty.seller.sla_breach.premium` (strictest)

Buyer-side penalties (restocking fees, failed delivery, COD refusal, chargeback abuse) are referenced by return and cancellation policies — they fire automatically at reconcile or account-flag time.

The `penaltyPolicy` field on the offer is normally not declared — ION derives the applicable penalty chain from the seller's tier and the other policies they declared. Explicit declaration is allowed only for approved per-offer overrides.

### SLA breach — auto enforcement

This is where the policy model earns its keep. When a grievance ticket is filed:

```
T+0      Ticket opened
         policy = ion://policy/grievance-sla/consumer/standard (firstResponseSla=PT2H)

T+2h     No response from seller
         ION auto-escalates to MARKETPLACE_MEDIATION
         Penalty policy queued: penalty.seller.sla_breach.standard, MINOR tier, 5%

T+24h    No resolution
         Already at MARKETPLACE_MEDIATION
         
T+72h    Marketplace mediation SLA missed
         ION auto-escalates to BPSK
         Penalty upgraded: MAJOR tier, 10%

At reconcile:
         reconcile.slaPenaltyDeduction = 10% of order value
         Deducted from BPP settlement, paid to consumer as goodwill
```

No human has to push these escalations. The policy terms document tells ION exactly when to escalate and what penalty to apply.

### Resolver API

```
GET /policies/{iri}             Resolve IRI to terms document
GET /policies?category=RETURN   List all return policies
```

### Atlas search

```bash
ion search "return policy for fashion"
ion search "grievance SLA for flash sale"
ion search "penalty for seller late dispatch"
ion search "COD payment terms"
```


## 8. Live and OTT commerce patterns (B2C-LIVE)

ION supports orders placed from live streams, short videos, OTT-embedded shoppable content, affiliate links, and group buys through the **B2C-LIVE** spine.

**OTT-embedded commerce example**: Consumer watches a match on Vidio. A jersey appears as a shoppable moment. Tap → ION `/select` fires with `liveCommerceContext.sourceChannel=OTT_EMBEDDED`, `ottPlatform=VIDIO`, `ottContentId=VIDIO-MATCH-PERSIJA-PERSIB-2026-04-19`, `ottTimestampSeconds=2847`. The seller BPP confirms as usual; the OTT platform earns an `AFFILIATE_COMMISSION` line at reconcile.

**Live stream example**: Consumer watches a Shopee Live session. Streamer pins a product. `sourceChannel=LIVE_STREAM`, `liveSessionId`, `streamerId`, `streamerCommissionPercent` populated. `STREAMER_COMMISSION` line in breakup, settled to streamer at reconcile.

**Group buy example**: Consumer joins a group-buy for a product. `sourceChannel=GROUP_BUY`, `groupBuyId`, `groupBuyMinParticipants`. Order is `ACTIVE_PENDING_GROUP` until minimum reached, then normal fulfilment proceeds.

Fields: `contract.liveCommerceContext`, `offer.isFlashSale`, `offer.totalStockCap`, `offer.queueEnabled`, `offer.reservationWindowSeconds`, new consideration line types `STREAMER_COMMISSION` and `AFFILIATE_COMMISSION`.

See `flows/trade/spines/B2C-LIVE/v1/` for complete spec.

Regulatory note — **Kemendag Permen 31/2023** requires social commerce to operate as e-commerce. ION's `sourceChannel` field captures origin attribution transparently while keeping the transaction as a compliant e-commerce flow, not a social media transaction.


## 9. Digital goods (B2C-DIG)

Digital goods — pulsa, PLN tokens, bill payments, gift cards, game currencies, streaming vouchers — are covered by the **B2C-DIG** spine. These use the `digital` performance state machine (PENDING_OPERATOR → DELIVERED / DELIVERY_FAILED) rather than the standard physical-goods machine.

**Fields**: `resource.resourceType` includes new values `DIGITAL_VOUCHER`, `DIGITAL_TOP_UP`, `DIGITAL_SUBSCRIPTION`. Each digital resource carries a `digital` sub-object with:
- `digitalCategory` (MOBILE_PULSA, ELECTRICITY_TOKEN, GAME_VOUCHER, STREAMING_VOUCHER, etc.)
- `operatorOrIssuer` (TELKOMSEL, PLN, Moonton, Netflix, etc.)
- `denomination` (value + unit: IDR, MB, GB, DIAMONDS, COINS)
- `deliveryMethod` (PUSH_TO_TARGET, CODE_TO_BUYER, ACCOUNT_CREDIT, QR_VOUCHER)
- `target` (mobile number, meter number, game user ID)
- `redemptionCode` (returned in `on_status[DELIVERED]` for CODE_TO_BUYER)
- `expiryAfterPurchase`, `refundable`, `cancellable`

See `flows/trade/spines/B2C-DIG/v1/` for complete spec.


## 10. Further reading

| Document | What it covers |
|---|---|
| `flows/trade/README.md` | Complete branch map — all 30+ sub-branches with windows |
| `flows/trade/spines/B2C-SF/v1/spine.yaml` | Reference spine — required fields at every step |
| `flows/trade/spines/{pattern}/v1/README.md` | Pattern-specific differences and key fields |
| `schema/extensions/trade/resource/v1/attributes.yaml` | Complete product field definitions |
| `schema/extensions/trade/offer/v1/attributes.yaml` | Complete offer and policy field definitions |
| `schema/extensions/core/` | Cross-sector fields — address, identity, payment, tax, etc. |
| `errors/registry.json` | All error codes with resolution guidance |

## Operations-readiness notes (v0.5)

Production operation requires attention to these operational aspects beyond the schema and flow spec itself:

### Policy IRI is authoritative — stop duplicating terms on offer

In v0.5 the offer stops carrying duplicative policy fields. **The policy IRI is the single source of truth.**

- Seller declares `offer.cancellationPolicy` and `offer.returnPolicy` (IRIs). That is it.
- Fee structures, window durations, allowed reasons, partial-refund ratios, refund timelines per payment method — all live in the policy terms document at `/policies/{category}/v1/{variant}.yaml`.
- BAP resolves the IRI to the terms document via Atlas to render consumer-facing text and enforce business rules.
- If a seller has unique terms that no ratified IRI matches, request ION Council ratification of a new policy variant. Never inline prose.

### KYC is a lifecycle, not a boolean

Providers carry `kycStatus`, `kycLevel`, `kycValidUntil`. The implications:

- **Catalog publish blocks** when `kycStatus` ∈ {EXPIRED, SUSPENDED, REJECTED} — error ION-2003.
- **New transactions refuse** against EXPIRED/SUSPENDED providers.
- **Tier determines caps**: BASIC max IDR 5M per order; STANDARD max IDR 50M; ENHANCED max IDR 500M; ENTERPRISE no cap.
- **Category licenses** (BPOM, SIA alcohol, PBF pharmacy) required as separate `categoryLicenses[]` entries for regulated goods.

### Refund timelines are payment-method-specific

v0.5 return policies declare refund timelines keyed by original payment method. BPPs MUST match the method-specific timeline:

- QRIS / EWALLET / BI_FAST: PT1H (near-instant)
- Virtual Account / Bank Transfer: P3D
- Credit Card: P14D (bank-dependent, up to 14 calendar days)
- Debit Card: P7D
- BNPL: P5D
- COD refund to wallet: PT0S (instant), to bank: P3D

Communicating P3D uniformly will break credit-card refunds and create dispute load.

### Age-restricted delivery

Items with `resource.ageRestricted=true` require verification at door. Delivery agent confirms age via KTP sighting (or scanned for enhanced verification). Failed verification → `DELIVERY_FAILED` → RTO, and buyer may be flagged for category restriction per platform policy.

Methods: KTP_SIGHTED, KTP_SCANNED, SIM_SIGHTED, PASSPORT_SIGHTED, SELFIE_COMPARISON, BIOMETRIC_API. Evidence stored per data residency rules.

### Data residency for pharmacy and health data

Resources with `dataResidency: DOMESTIC_ONLY` may only be transacted by BAPs processing data within Indonesia per UU 27/2022. BAPs with foreign processing must filter these from discovery or refuse transactions — error ION-5011.

### Batch settlement at scale

Per-order reconcile does not scale to marketplace volume. Use `isBatch: true` with `contractIds[]` and `batchPeriod`. Include `taxWithholdings[]` with NTPN references for PPh22, PPh23, PPN remittance. Buktit potong documents attached per tax line.

### Variant explosion is solved by matrix

For products with more than ~30 potential variants (multi-axis electronics, apparel), use `resource.variantMatrix` on a parent PLAIN resource rather than publishing every VARIANT as a separate resource. BPP computes the specific variant at on_select from the matrix.

### Payment milestone schedules

For down-payment + balance orders (furniture, pre-order, services), use `contract.paymentSchedule[]`. Contract does not move to COMPLETE until all milestones are PAID. Missed milestones trigger ION-3021; seller decides retry or cancel.

### Logistics events stay on Logistics protocol

The Trade protocol does NOT surface: rider reassignments, pickup failures at seller premises, hub handoffs, LSP-internal SLA clocks, cold-chain sensor excursions, multi-package tracking. BPP aggregates only the events that affect the consumer view (final DELIVERED, final RTO, consumer-facing ETA delay) into Trade performance. For full logistics visibility, BAPs subscribe to the Logistics sector transactions linked via `contractAttributes.linkedContractId`.


---

## See also

- **First time here?** [`ION_Start_Here.md`](ION_Start_Here.md)
- **Confused by an acronym?** [`ION_Glossary.md`](ION_Glossary.md)
- **End-to-end transaction example?** [`ION_First_Transaction.md`](ION_First_Transaction.md)
- **Cross-sector concepts?** [`ION_Developer_Orientation.md`](ION_Developer_Orientation.md)
- **Layer model (L1-L5)?** [`ION_Layer_Model.md`](ION_Layer_Model.md)
- **Signing and auth?** [`ION_Onboarding_and_Auth.md`](ION_Onboarding_and_Auth.md)
- **Doing logistics instead?** [`ION_Sector_B_Logistics.md`](ION_Sector_B_Logistics.md)
