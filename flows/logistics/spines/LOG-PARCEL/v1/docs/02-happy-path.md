# LOG-PARCEL — Happy Path

## Narrative walkthrough

A seller on Tokopedia receives an order for an electronics item. Tokopedia (BAP) needs to book a parcel shipment with JNE (BPP).

**Step 1 — Catalog already subscribed**

Tokopedia has already subscribed to JNE's catalog from the ION Catalogue Service. They know JNE covers Jakarta → Surabaya, offers NEXT_DAY air service at Rp 18,000/kg, requires `/select` for firm quotes (`selectRequired: true`), and accepts COD.

**Step 2 — /select (firm quote)**

Tokopedia calls `/select` with the actual pickup pincode (10110, Jakarta Pusat), actual drop pincode (60111, Surabaya), actual weight (2.5 kg), and service level (NEXT_DAY).

JNE responds via `/on_select` with: total amount Rp 56,721 (including fuel surcharge, insurance premium, PPN), routing topology P2H2H2P, estimated TAT 1 day, quote valid for 15 minutes.

**Step 3 — /init (commitment with delivery details)**

Tokopedia calls `/init` with full consignor details (seller name, phone, pickup address), consignee details (buyer name, phone, delivery address including provinsiCode "35" for Jawa Timur), and payment method (QRIS, collected by BAP).

JNE responds via `/on_init` with QRIS string for payment and confirms the final amount.

**Step 4 — /confirm (binding commit)**

Tokopedia calls `/confirm` after the buyer pays via QRIS. Payment status is PAID.

JNE responds via `/on_confirm` with:
- `awbNumber: JNE2026042200001`
- `proofOfDeliveryType: OTP`
- `deliveryOtp: 482916` (sent to buyer's phone separately)
- `shippingLabelUrl: https://...`
- State: READY_FOR_PICKUP

**Step 5 — Seller prints label, packages**

Seller prints shipping label and hands over to JNE pickup agent.

**Step 6 — on_status updates (JNE pushes)**

JNE pushes state updates to Tokopedia's `/on_status` endpoint:

```
READY_FOR_PICKUP → OUT_FOR_PICKUP → PICKED_UP (with photo proof)
→ AT_ORIGIN_HUB (Cengkareng) → IN_TRANSIT → AT_DESTINATION_HUB (Surabaya)
→ OUT_FOR_DELIVERY → DELIVERED (buyer showed OTP)
```

At DELIVERED, JNE carries `deliveryTimestamp` and `proofOfDelivery: {type: OTP, value: "482916 verified"}`.

**Step 7 — Rating**

Tokopedia calls `/rate` after delivery with buyer's rating of the delivery experience (FULFILLMENT category) and the agent (AGENT category).

**Step 8 — Reconcile**

JNE and Tokopedia reconcile the financial settlement. If this was a COD order, the COD remittance would follow per the agreed payment-terms policy.

## What can go wrong (branches that activate)

- **Weight discrepancy**: JNE weighs at hub — 3.2 kg not 2.5 kg. Triggers `weight-dispute` branch.
- **Buyer not home**: First delivery attempt fails. Triggers `attempts` branch — NDR-001 sent, buyer reschedules.
- **Damage**: Buyer reports damage on receipt. Triggers `exception/damage-claim` branch within evidence window.
- **Buyer cancels before pickup**: Triggers `cancellation` branch — `cancel-buyer-prepickup`.

All these are documented in `flows/logistics/branches/`.
