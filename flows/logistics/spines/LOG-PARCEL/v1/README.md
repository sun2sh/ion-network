# LOG-PARCEL — Parcel Logistics

The reference logistics spine on ION. Hub-routed parcel shipments, covering domestic and cross-border-by-parcel, B2C and B2B. Every other logistics spine is defined as a delta from this one.

## Applicable service types
Standard express, economy, next-day, same-day, scheduled. Covers JNE, J&T, SiCepat, Lion Parcel, Anteraja, Pos Indonesia, and international parcel express operating in Indonesia.

## Covers both B2C and B2B
The spine itself does not split by consignor/consignee type. B2B transactions are identified by the presence of registered-business identifiers (NPWP, NIB) on participants and trigger the `ekyc` branch at `/init` when there is no active FWA between the parties.

## API sequence
```
Phase 1  BPP → publish_catalog → ION Catalogue Service
         ION Catalogue Service → on_discover → BAP (subscription-based)

Phase 2  BAP → select  → BPP → on_select       (optional per offer.selectRequired)
         BAP → init    → BPP → on_init         (ekyc branch attaches for B2B w/o FWA)
         BAP → confirm → BPP → on_confirm      (AWB issued)

Phase 3  BPP → on_status [READY_FOR_PICKUP]
         BPP → on_status [OUT_FOR_PICKUP]
         BPP → on_status [PICKED_UP]           (proof of pickup)
         BPP → on_status [AT_ORIGIN_HUB]       (P2H2P, P2H2H2P only)
         BPP → on_status [IN_TRANSIT]
         BPP → on_status [AT_DESTINATION_HUB]  (P2H2P, P2H2H2P only)
         BPP → on_status [OUT_FOR_DELIVERY]
         BPP → on_status [DELIVERED]           (proof of delivery; Contract COMPLETE)
```

## Performance state machine variants
The state machine in use is determined by `offer.routingTopology`:
- `parcel-p2p` — direct pickup to delivery, no hub states. Short-distance intra-city parcel.
- `parcel-p2h2p` — single origin-or-destination hub consolidation.
- `parcel-p2h2h2p` — both origin and destination hubs with inter-hub transit.

All three are defined in `schema/extensions/logistics/performance-states/v1/states.yaml`.

## Available branches
- During-transaction: `ekyc` (B2B w/o FWA), `fwa-activation`, `payment-prepaid`, `payment-cod`, `payment-credit`
- Fulfilment: `weight-dispute`, `cold-chain-proof`, `attempt-ndr`, `attempt-reschedule`, `attempt-address-change`, `attempt-self-pickup-conversion`, `attempt-auto-rto`
- Exception: `damage-claim`, `loss-claim`, `address-unserviceable`, `pickup-failed`
- Cancellation: `cancel-buyer-prepickup`, `cancel-seller`, `cancel-intransit`
- Reverse: `reverse-with-qc`
- Cross-cutting: `track`, `support`, `rating`, `raise`

## Key fields introduced
`awbNumber`, `routingTopology`, `rateLogic`, `selectRequired`, `quoteValidityWindow`, `proofOfPickup`, `proofOfDelivery`, `deliveryOtp`, `actualWeight`, `declaredValue`, `temperatureRequirement`, `agentAssignmentModel`, `fwaReference`, `ekycFormReference`.

## Distinguishing from other logistics spines
- **LOG-HYPERLOCAL**: sub-day rider-based, real-time GPS, rider identity exposed mid-flow, no hub states. Use LOG-HYPERLOCAL when service level is INSTANT and no hub routing applies.
- **LOG-FREIGHT**: capacity-based booking (FTL/LTL, FCL/LCL, air cargo slots), bill-of-lading, departure-event state machine. Use LOG-FREIGHT when the shipment is booked against capacity, not against a rate card.
- **LOG-XB**: adds customs clearance branch. Use LOG-XB for cross-border freight; for cross-border parcel (small packages), LOG-PARCEL with the customs-clearance branch attached is usually sufficient.
