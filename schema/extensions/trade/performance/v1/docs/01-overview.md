# Trade Performance Extension — Overview

Fulfilment tracking attributes. What the BAP receives at each state transition.

## What gets added per state
- PACKED: nothing new (just state code)
- DISPATCHED: `awbNumber`, `trackingUrl`, `estimatedDeliveryTime`, agent details
- OUT_FOR_DELIVERY: updated `estimatedDeliveryTime`, realTimeGps via `/track`
- DELIVERED: `deliveryProofUrl` (if PHOTO type), contract status = COMPLETE

## installationScheduling
Declared capability is in `resource.installation` (does it need installation? does seller provide it?). This field carries the transaction-time appointment — `scheduledDate` + `notes`. Populated by BPP after on_confirm.

## GPS vs status
`realTimeGps` is returned only in `/on_track` responses — not in `/on_status`. They serve different purposes: `/on_status` carries state transitions; `/on_track` carries position.
