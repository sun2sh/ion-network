# ION Sector A — Trade
**Version:** 1.0  
**Date:** April 2026  
**Status:** Working Document — for ION Council review  
**Sector code:** A  
**Resource type:** TradeResource

---

## 1. What is Trade?

The Trade sector covers all transactions involving physical products — things that are manufactured, grown, packaged, or crafted, and transferred from a seller to a buyer. If something has a SKU, weighs something, and needs to be delivered or collected, it belongs in Trade.

Trade is the broadest sector on ION and the one with the most commerce pattern variations — from a consumer buying groceries to a government procuring electronics in bulk.

---

## 2. Resource Type — TradeResource

One resource type covers all physical product categories. The category of product (Food & QSR, Grocery, Fashion, Electronics, Beauty, FMCG, Agritech, B2B Wholesale, Cross-border) is a value inside the resource — not a separate schema.

### 2.1 What makes a TradeResource

Every TradeResource has:

**Core identity**
- SKU — seller's internal product code
- Name in English and Bahasa Indonesia (localizedName)
- Description in English and Bahasa Indonesia (localizedDesc)
- Images — primary thumbnail and media gallery
- Category — which product type this belongs to

**ION Core fields (Indonesian regulatory, apply to all sectors)**
- Halal certification number (halalCertNumber) — MUI issued, required for food, cosmetics, pharmaceuticals
- BPOM registration number (bpomRegNumber) — required for packaged food and personal care
- NIB — business identity of the seller
- NPWP — tax identity, used in settlement and PPN computation
- Provinsi code, Kabupaten code — for serviceability and tax zone

**Attribute groups populated by product type**

| Attribute group | Attributes | When to populate |
|---|---|---|
| Food & perishable | dietaryClassification (VEG/NON_VEG/HALAL), allergens[], shelfLife, cuisineType | All F&B products |
| Packaged goods | netQuantity, manufacturerName, packingDate, countryOfManufacture | All packaged products |
| Electronics & durables | warrantyDuration, warrantyType, installationRequired, installationBySeller | Electronics, appliances |
| Agritech | harvestDate, produceGrade, mandiReferencePrice, pesticideDeclaration | All agri produce |
| Fashion | fabricComposition, careInstructions, fitType | Apparel and textiles |
| Beauty & personal care | ingredients[], skinType, expiryDate | Cosmetics and personal care |

### 2.2 Four resource types within TradeResource

Every TradeResource is one of four structural types. The type is derived from the customisation group structure — it is never declared as a field.

**Plain** — one thing, one price, no choices. The buyer adds it to their order as-is. No customisation groups. Example: a bag of Indomie, a specific phone model, a bottle of hand sanitiser.

**Variant** — one product expressed as multiple pre-defined orderable options. Each variant has its own stock count and potentially its own price. Options point to existing Resource IDs (that is what makes it a variant). Example: blue shirt in S/M/L/XL, refrigerator in 400L or 600L.

**With-extras** — a fixed orderable base item with optional additions. The base is self-sufficient — it can be ordered without selecting any extras. Extras have their own Resource IDs. Example: laptop with optional extended warranty, garlic bread with optional extra cheese.

**Composed** — a base item assembled at order time from mandatory choices. The final product does not pre-exist as a SKU. Options have price deltas, not independent inventory. Example: pizza with mandatory size and crust selection, custom cake with flavour and inscription.

### 2.3 Customisation groups

Customisation groups define what choices the buyer makes before ordering. Each group has a selection rule (SINGLE_REQUIRED, SINGLE_OPTIONAL, MULTIPLE_OPTIONAL, FIXED), a sequence number for display, and min/max selection counts.

Each option has either a `resourceId` (variant or extras — points to existing inventory) or a label and price delta (composed — an ingredient added at order time). This structural difference makes wrong classification impossible — there is no type field to misuse.

Input types for composed options: select (dropdown), text (free input for cake inscriptions, garment measurements), number (numeric measurements), date (appointment date), boolean (yes/no flags).

### 2.4 Bundles

Bundles are an Offer type, not a Resource type.

**Pre-packaged bundle** — multiple items physically packaged together by the manufacturer. This is a plain Resource with `netQuantity` declaring contents. Example: Maggi 12-pack, skincare gift set.

**Seller-created bundle offer** — independent items linked by an Offer that gives a combined price. Each item retains its own Resource ID and stock. Example: "Pizza + Drink = Rp 50.000 off."

---

## 3. Commerce Patterns

### 3.1 B2C single fulfilment

**What it is:** Consumer discovers, selects, and purchases a product. Delivery or pickup follows.

**Indonesian examples:** GoFood, GrabFood, Tokopedia, Shopee, Blibli, Alfagift, Indomaret Digital

**Categories:** Food & QSR, Grocery, Fashion, Electronics, Beauty, FMCG

**Flow:** discover → select → init → confirm → fulfil → post-fulfil

**ION model status:** No gaps. Spec immediately.

**Key attributes:**
- Serviceability radius on Offer
- Cancellable / returnable flags on Offer
- TAX line type: PPN 11% computed at select time
- DELIVERY, HANDLING line types in Consideration
- Performance: PLANNED → PACKED → DISPATCHED → DELIVERED

---

### 3.2 B2C make-to-order

**What it is:** Consumer composes an order from mandatory choices. The product does not pre-exist as a SKU — it is assembled at order time.

**Indonesian examples:** Dominos Indonesia, HokBen custom meals, kue artisan platforms, bespoke batik ateliers

**Categories:** Food & QSR, Custom bakery, Tailoring, Custom furniture

**Flow:** discover → select (with customisation group completion) → init → confirm → fulfil

**ION model status:** No gaps. Spec immediately.

**Key attributes:**
- Mandatory customisation groups with SINGLE_REQUIRED selection
- Price deltas accumulate on base price
- prepTime / estimatedReadyTime on Performance
- shelfLife on Resource for F&B (limits valid delivery slots)

---

### 3.3 B2C subscription

**What it is:** Consumer signs up for recurring deliveries on a billing cycle. Auto-renewal until cancelled.

**Indonesian examples:** Kopi subscription boxes, Say Veggie weekly produce, meal plan platforms, supplement auto-delivery

**Categories:** Grocery, FMCG, F&B, Health supplements

**Flow:** discover → select → init → confirm (subscription started) → recurring fulfilment → cancel or pause

**ION model status:** Extended — attribute additions required.

**Additions needed:**
- `billingCycle` on Contract (WEEKLY, FORTNIGHTLY, MONTHLY, ANNUAL)
- `renewalTerms` — auto-renew yes/no, renewal notice period
- `cancellationNoticePeriod` — how far in advance to cancel
- `nextBillingDate` on Settlement
- SUBSCRIPTION_FEE line type in Consideration
- PAUSED status on Contract

---

### 3.4 B2B wholesale — prepaid

**What it is:** Retailer or business purchases from a distributor or manufacturer, paying upfront. Order volumes are higher than B2C, pricing may be tiered by buyer type.

**Indonesian examples:** Tokopedia Mitra, GudangAda, Ula — distributor-to-kirana prepaid orders

**Categories:** Agritech, FMCG, Electronics, B2B Wholesale

**Flow:** discover → select → init (buyer identity verification) → confirm → fulfil

**ION model status:** Extended — attribute additions required.

**Additions needed:**
- `minimumOrderQuantity` (MOQ) on Offer — order rejected if below MOQ
- `buyerEligibility` condition on Offer — distributor-specific pricing (Distributor A gets different price from Distributor B)
- NPWP as mandatory buyer identity field at init (already ION Core)
- `purchaseOrderReference` on Contract for B2B compliance
- Tax invoice (Faktur Pajak) reference in post-confirm

---

### 3.5 B2B wholesale — credit / BNPL

**What it is:** Retailer or business purchases from a distributor on credit terms. Payment due after a defined period, not at confirm.

**Indonesian examples:** GudangAda Bayar Nanti, Ula BNPL for warung, Waizly distributor credit terms

**Categories:** FMCG, Agritech, B2B Wholesale, Electronics

**Flow:** discover → select → init (credit limit check) → confirm → fulfil → payment due

**ION model status:** Extended — attribute additions required.

**Additions needed:**
- `creditTermsDays` as flow attribute (e.g., Net 30, Net 60)
- `paymentDueDate` on Settlement
- CREDIT payment type on Consideration (payment_type: POST_FULFILMENT with credit terms)
- Credit limit verification at init — BPP NACKs if buyer exceeds limit
- Late payment charge declaration on Contract

---

### 3.6 Marketplace — inventory held

**What it is:** Platform intermediates between multiple sellers and buyers. Each seller holds their own inventory. The BAP is the marketplace operator.

**Indonesian examples:** Tokopedia, Shopee, Lazada — seller holds own stock, platform intermediates transaction

**Categories:** Fashion, Electronics, Beauty, Home & Kitchen

**Flow:** discover (across multiple BPPs) → select → init → confirm → fulfil

**ION model status:** Extended — attribute additions required.

**Additions needed:**
- Platform fee (finder fee) declaration in Contract — what % the marketplace retains
- Multi-seller cart handling — one consumer order spanning multiple BPP contracts
- `linkedCartId` to group multiple contracts from one consumer session

---

### 3.7 Marketplace — inventory less

**What it is:** Platform lists products it can source but does not hold in stock. Seller is assigned at or after order confirmation.

**Indonesian examples:** JD.ID fulfilled-by-marketplace, Blibli sourced items, brand aggregator platforms

**Categories:** Electronics, Fashion, FMCG

**Flow:** discover (by product code) → init → confirm → seller assignment → fulfil

**ION model status:** New pattern — structural work required before spec.

**Structural gaps:**
- `productCode` (GTIN or barcode) needed on TradeResource as a network-wide product identifier that is not seller-specific. Enables BAP to broadcast to all suppliers of a specific product.
- `SELLER_PENDING` contract state — seller not yet assigned at confirm. Seller assignment happens via `/on_update` post-confirm.
- `sellerAssignmentDeadline` on Contract — if no seller assigned by deadline, contract auto-cancels.
- Order type field on Context — ILBN (Inventory Less Buy Now), ILFP (Inventory Less Fulfiller Pre-assigned) to differentiate flows.

---

### 3.8 Forward auction

**What it is:** Seller lists produce or goods at a reserve price. Buyers bid up. Highest bid above reserve wins.

**Indonesian examples:** TaniHub live produce auction, agri marketplace bidding, online art auctions

**Categories:** Agritech, Collectibles, Art, Rare commodities

**Flow:** discover (auction listing) → bid (multiple /select calls) → auction close → confirm (winning bidder)

**ION model status:** New pattern — structural work required before spec.

**Structural gaps:**
- `reservePrice` on Offer — minimum acceptable price
- `auctionCloseTime` on Offer — when bidding ends
- Consideration is PENDING status until auction closes — no confirmed price until close
- `/select` carries a bid amount (not a fixed quantity selection). Commitment is a bid record with `bidAmount` and `bidTimestamp`.
- Multiple BAPs can be in-flight on the same BPP offer — currently Beckn assumes one BAP per transaction.

---

### 3.9 Procurement auction (reverse)

**What it is:** Buyer announces a procurement requirement. Sellers compete by bidding down. Lowest qualifying bid wins.

**Indonesian examples:** LKPP e-procurement (government), Mbiz B2B sourcing, corporate procurement platforms

**Categories:** FMCG, Electronics, B2B Wholesale, Government procurement

**Flow:** buyer publishes RFQ → sellers discover and bid (via /init) → buyer selects winner → confirm

**ION model status:** New pattern — structural work required before spec.

**Structural gaps:**
- Buyer-initiated flow — /init starts the transaction, not /discover. Buyer is the BAP, sends requirements.
- `lowestBid` tag on /init for multi-round bidding — BAP shares current lowest with all sellers.
- `bidRound` field on Commitment — tracks auction round number.
- Auction winner selection is BAP-side logic — not a protocol action.

---

### 3.10 Export / cross-border

**What it is:** Indonesian seller exports goods to an international buyer. Customs, Incoterms, and international payment apply.

**Indonesian examples:** Batik export platforms, Kopi Luwak international sales, Indonesian craft exporters, Rajawalisinh agri export

**Categories:** Agritech, Fashion (Batik), Beauty, Coffee & Spices, FMCG

**Flow:** discover → select → init (export documentation) → confirm → customs clearance → international shipping → delivery

**ION model status:** New pattern — structural work required before spec.

**Structural gaps:**
- Export regulatory fields needed at ION Core (cross-sector): `hsCode` (HS tariff code), `incoterms` (EXW/FOB/CIF/DDP), `countryOfOrigin`, `APE` (Angka Pengenal Ekspor — exporter registration number).
- Export document references on Contract: `ska` (Surat Keterangan Asal / Certificate of Origin), `phytosanitaryCertRef`, `healthCertRef` for food/agri exports.
- Performance states: EXPORT_CUSTOMS_SUBMITTED → EXPORT_CUSTOMS_CLEARED → SHIPPED → IN_TRANSIT → IMPORT_CUSTOMS_CLEARED → DELIVERED.
- International payment rails — SWIFT, Letter of Credit, or escrow. SNAP does not apply cross-border. Settlement model needs to accommodate international wire or documentary collection.
- PPN zero-rated on exports — tax treatment differs from domestic.

---

### 3.11 B2G procurement

**What it is:** Business sells to a government entity. Government procurement has specific identity, compliance, and payment requirements.

**Indonesian examples:** e-Katalog LKPP, Bela Pengadaan (UKM to government), LPSE tender platforms

**Categories:** FMCG, Electronics, Agritech, Office supplies, PPE

**Flow:** discover (government catalogue) → select → init (procurement compliance) → confirm → fulfil

**ION model status:** New pattern — structural work required before spec.

**Structural gaps:**
- B2G participant shape — government buyer identity fields: SIRUP code (procurement reference), DIPA reference (budget code), Satker ID (spending unit).
- PPN treatment varies — government entities may be exempt in certain categories.
- e-Katalog product identity — LKPP product codes as an additional identifier alongside ION product code.
- Payment terms: government typically pays post-delivery within 30 days through KPPN (treasury) — different from commercial payment.

---

## 4. Provider Benefits

Provider benefits are declared in the catalog by the seller. The seller absorbs the cost.

| Benefit type | Description | Example |
|---|---|---|
| Price benefit | Item below reference price | Baju batik Rp 89k (was 99k) |
| Bundle benefit | Items at combined price | Pizza + drink = Rp 120k |
| Threshold benefit | Reward when cart hits a value | Spend Rp 200k → free delivery |
| Gift-with-purchase | Free item with qualifying purchase | Buy fridge → free water filter |
| Trade-in benefit | Old item value applied against new purchase | Trade old HP → Rp 500k off |
| Instalment benefit | Payment restructured, 0% offered | Cicilan 12 bulan 0% |
| Exchange benefit | Swap for different variant post-delivery | Wrong size? Tukar dalam 7 hari |
| Loyalty earn | Points earned on this purchase | Earn 89 poin |

## 5. Buyer App Benefits

Buyer app benefits are created by the BAP from its own budget. The seller always receives the full quoted price.

| Benefit type | Description |
|---|---|
| Voucher | Promo code applied by consumer |
| Membership | Free delivery or member price for premium users |
| Occasion | First order, birthday, re-engagement |
| Payment method | Bank card / e-wallet promotion |
| Loyalty redeem | Points from previous orders applied |

Buyer app benefits are hidden from the seller-facing Consideration unless `collectedBy: SELLER` (COD case).

---

## 6. Price Breakup — Consideration Line Types

| Line type | Description | Who absorbs |
|---|---|---|
| ITEM | Base price of product ordered | Seller receives |
| DELIVERY | Delivery charge | Logistics partner |
| HANDLING | Packaging fee | Seller receives |
| TAX | PPN (11%) or PPNBM — computed at select time | Government |
| PROVIDER_BENEFIT | Seller's own benefit applied | Reduces seller receivable |
| BUYER_BENEFIT | Buyer app's benefit — hidden from seller unless COD | Buyer app absorbs |
| TRADE_IN | Old item value applied | Seller absorbs |
| LOYALTY_REDEEM | Points redeemed | Buyer app absorbs from points ledger |
| FINANCE_CHARGE | Instalment fee or interest | Finance partner or buyer |
| GIFT | Free item included — declared for settlement record | Seller absorbs |

---

## 7. Performance Lifecycle

Standard domestic delivery:
```
PLANNED → PACKED → DISPATCHED → DELIVERED
```

Post-delivery events (each creates a new Performance record on the same Contract):
```
Return:       RETURN_INITIATED → RETURN_APPROVED → RETURN_PICKED → RETURN_DELIVERED
Replacement:  REPLACEMENT_DISPATCHED → REPLACEMENT_DELIVERED
RTO:          RTO_INITIATED → RTO_DELIVERED (back to seller)
```

Export:
```
PLANNED → PACKED → EXPORT_CUSTOMS_SUBMITTED → EXPORT_CUSTOMS_CLEARED
→ SHIPPED → IN_TRANSIT → IMPORT_CUSTOMS_CLEARED → DELIVERED
```

---

## 8. Settlement

> **Version note:** The settlement model below describes the full ION design. The settlement declaration fields (`settlementBasis`, `settlementWindow`, payment rails) are part of the current v0.1 spec and go into your `/confirm` payload. The `/reconcile` and `/on_reconcile` APIs that trigger the actual money movement are in active development and will be available in v0.2. You declare the terms now — the reconciliation flow will wire up to them when it lands.



Settlement in Trade follows the standard ION settlement model:

- `settlementBasis` declared at confirm: AFTER_DELIVERY, AFTER_SHIPMENT, or AFTER_RETURN_WINDOW_EXPIRY
- `settlementWindow` in ISO 8601 duration (e.g., P1D = within 1 day of basis event)
- Payment rail: BI-FAST, QRIS, or VA — declared at confirm using SNAP-standard account identifiers
- Reconciliation via `/reconcile` and `/on_reconcile` before money moves *(v0.2 — in development)*

For B2B credit: `paymentDueDate` replaces `settlementWindow`. Payment due Net 30/60 from delivery.

For COD: logistics partner collects cash from consumer and remits to seller. Seller then remits platform fee to buyer app. Reverse money flow — logistics partner owes seller, seller owes buyer app.

For export: SNAP does not apply. International wire or Letter of Credit. Settlement terms governed by Incoterms agreed at confirm.

---

## 9. Indonesian Regulatory Fields Summary

| Field | Layer | Applies to |
|---|---|---|
| halalCertNumber (MUI) | ION Core | Food, cosmetics, pharmaceuticals |
| bpomRegNumber | ION Core | Packaged food, personal care |
| NIB | ION Core | All sellers |
| NPWP | ION Core | All sellers and B2B buyers |
| provinsiCode, kabupatenCode | ION Core | Serviceability and tax zone |
| APE (Angka Pengenal Ekspor) | Trade — Export flow | Export sellers |
| hsCode | Trade — Export flow | All export products |
| SKA (Certificate of Origin) | Trade — Export flow | Export products |
| SIRUP, DIPA, Satker | Trade — B2G flow | Government procurement |
| PPN 11% | Trade sector | All taxable products |
| PPNBM | Trade sector | Luxury goods |

---

## 10. Open Questions

**OQ-A-01: MOQ enforcement**
When a buyer's cart falls below the declared `minimumOrderQuantity`, should the BPP NACK the `/select` or return a modified quote with a warning? The ION preference is to return a warning on `/on_select` with the minimum quantity, allowing the BAP to prompt the buyer to add more. Decision needed from ION Council.

**OQ-A-02: Multi-seller cart**
In B2C marketplace, a consumer often adds items from multiple sellers to a single cart. On confirmation, these split into multiple Contracts (one per BPP). How does the ION model handle the consumer-facing unified cart view vs the protocol-level split? The BAP manages this at the application layer — but ION needs to define a `cartSessionId` or similar linking field so ION Central can trace multi-contract sessions for support purposes.

**OQ-A-03: productCode for inventory-less**
Should `productCode` (GTIN/barcode) be an ION Core field (available across all sectors) or a Trade sector field? If a logistics provider or a finance provider ever needs to reference a specific product by barcode, ION Core placement is cleaner. Trade-only placement keeps ION Core lean. Decision needed.

**OQ-A-04: Auction — multiple BAPs per offer**
Beckn v2.0's current model assumes one BAP per transaction against a BPP offer. In a forward auction, multiple BAPs are simultaneously bidding on the same offer. Does this require a gateway-level change, or can it be handled by the BPP maintaining a bid ledger and responding to each BAP independently? Needs Beckn Foundation input.

**OQ-A-05: Export — international BAP participation**
Can a buyer app registered on a foreign Beckn network (e.g., a future cross-border open network) transact with an Indonesian BPP on ION? This is a cross-network question that requires bilateral agreement between network operators. ION should define the interface requirements — what does ION need from a foreign BAP to allow it to transact? This is out of scope for v1.0 but should be flagged for the ION cross-border working group.

**OQ-A-06: B2G — is this in scope for ION launch?**
Government procurement in Indonesia operates under specific legal frameworks (Perpres 12/2021 and its amendments). Integrating with LKPP e-Katalog requires formal agreement with LKPP. This may be better handled as a Phase 2 item with dedicated government working group participation, rather than a launch-day spec.

**OQ-A-07: Incoterms and PPN zero-rating for export**
Indonesian tax law allows PPN zero-rating on exported goods. However, the point at which goods are considered "exported" for tax purposes varies by Incoterms. For FOB, PPN zero-rating applies from port of origin. For DDP, the seller may need to remit import duties at the destination. ION needs a tax expert review of how to declare this correctly in the Consideration breakup.

---

*ION Sector A — Trade v1.0 — Working Document*  
*For ION Council review and ratification*
