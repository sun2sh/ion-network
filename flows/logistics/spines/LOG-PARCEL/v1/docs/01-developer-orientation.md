# LOG-PARCEL — Developer Orientation

## What this spine is for

You are building a logistics integration for parcel delivery — either as an LSP (BPP) offering parcel services, or as a BAP (marketplace, seller platform) booking parcel deliveries.

LOG-PARCEL is the reference spine for all hub-routed parcel shipments in Indonesia. JNE, J&T, SiCepat, Lion Parcel, Anteraja, and Pos Indonesia all operate on this model. B2C (consumer) and B2B (business) parcels use the same spine — what changes is the participant identity fields and whether the eKYC branch fires.

## The two phases you need to implement

**Phase 1 — Catalog** (BPP only)

You publish your service catalog once (and update it when rates or coverage change). You do not respond to per-query catalog requests. The catalog is pushed to the ION Catalogue Service; BAPs subscribe and receive it.

```
Your API → /catalog/publish → ION Catalogue Service → on_discover → BAPs
```

What your catalog must declare: your coverage (province/pincode level), service levels (NEXT_DAY, SAME_DAY, ECONOMY), rate logic (zone definitions, weight tiers), `selectRequired` flag, policy IRIs for cancellation/claim/SLA/evidence/dispute, and whether you accept FWA-governed transactions.

**Phase 2 — Transaction** (both BAP and BPP)

```
BAP → /select  → BPP → /on_select    [optional — see selectRequired]
BAP → /init    → BPP → /on_init
BAP → /confirm → BPP → /on_confirm   ← AWB issued here
BPP → /on_status (unsolicited, through all states)
BAP ↔ BPP → /update / /on_update    [if branches activate]
BAP → /cancel  → BPP → /on_cancel   [if cancellation branch activates]
BAP → /track   → BPP → /on_track    [real-time tracking handle]
BAP → /support → BPP → /on_support  [support tickets]
BAP → /rate    → BPP → /on_rate     [post-delivery rating]
```

## The selectRequired decision

This is the most important decision in your catalog. Ask yourself: does my rate for a specific shipment depend on the actual pickup and drop pincodes, the actual weight, or current capacity?

- If yes → set `selectRequired: true`. BAP must call `/select` before `/init`.
- If no (fixed published rates, pre-validated coverage) → set `selectRequired: false`. BAP can skip straight to `/init`.

Most parcel LSPs should set `selectRequired: true` because zone computation depends on actual pincodes.

## The routing topology

Declare `routingTopology` on your offer. This determines which state machine runs:

| Topology | Hubs involved | State machine |
|---|---|---|
| P2P | None — direct pickup to delivery | `parcel-p2p` |
| P2H2P | Single consolidation hub | `parcel-p2h2p` |
| P2H2H2P | Origin hub + destination hub + inter-hub transit | `parcel-p2h2h2p` |

The state machine variant is what determines which `on_status` states you push. See `schema/extensions/logistics/performance-states/v1/states.yaml`.

## What happens at /on_confirm

At `on_confirm` you return the AWB number, the shipping label URL, the proof-of-pickup type, and the proof-of-delivery type. The `deliveryOtp` is also returned here if `proofOfDeliveryType: OTP`.

The buyer's app shows this OTP to the delivery rider at the door. The rider enters it into their app. This is the delivery confirmation mechanism.

## The eKYC branch (B2B only)

If the consignor or consignee carries a NPWP and there is no active FWA between you and the BAP, the eKYC branch fires at `/init`. You verify NIB and NPWP against government registries and return `ekycStatus` in `on_init`. If REJECTED, the transaction terminates here.

Once a party is verified, you cache the result. Future transactions with the same party skip eKYC until the verification expires.

## Disputes go through /update

If a package is reweighed at your hub and the weight differs from declared, you send an unsolicited `/on_update` with `context.try: false`, referencing `ion://policy/dispute.weight-discrepancy` and carrying the diff. The BAP can preview the proposed amount using `context.try: true` before accepting.

Never use a separate channel for disputes. The contract's update history is the evidence trail.

## Track vs Status

- `/on_status` — you push state changes (PICKED_UP, IN_TRANSIT, DELIVERED). State machine events.
- `/track` / `/on_track` — BAP requests a tracking handle (URL or WebSocket). You return a URL they can poll for live location. For parcel, this is typically a `trackingUrl` pointing to your tracking page.

Both are needed. Don't conflate them.

## Reconcile

After delivery, the financial settlement is reconciled using the ION Core `reconcile/v1` schema. This covers the final agreed amount (after any weight-dispute adjustments), COD remittance amounts, SLA rebates, and PPN. See `schema/extensions/core/reconcile/v1/`.
