# LOG-HYPERLOCAL — Hyperlocal Delivery

Sub-day single-rider delivery within a city or metropolitan area. Real-time GPS, rider exposed mid-flow, no hub states.

## Applicable service types
INSTANT and sub-3-hour delivery patterns. Covers GoSend, GrabExpress, Paxel instant, Lalamove, and on-demand courier services.

## Delta from LOG-PARCEL
- State machine: `hyperlocal-fifo` or `hyperlocal-pre-assigned` — no hub events
- Service level restricted to INSTANT or sub-3h
- `agentAssignmentModel` is mandatory on offer (PRE_ASSIGNED, POOL_ASSIGNED, FIFO_AT_PICKUP, DEDICATED_FLEET)
- Rider identity exposed via `agentDetails` — timing depends on assignment model
- `liveTrackingEnabled` true throughout
- `selectRequired` typically true (surge pricing)
- Cold chain rarely supported; hazmat not supported
- No AWB — `bookingReference` used
- Tighter cancellation and return windows

## Agent assignment models
| Model | Rider known at |
|---|---|
| PRE_ASSIGNED | Booking confirmation |
| DEDICATED_FLEET | Booking confirmation (from committed pool) |
| POOL_ASSIGNED | Rider dispatched to merchant |
| FIFO_AT_PICKUP | Rider pickup event — first rider takes first ready order |

## Available branches
- `payment-prepaid`, `payment-cod`
- `attempt-ndr` (1–2 attempts typical), `attempt-reschedule`
- Reverse: `reverse-simple`
- Cross-cutting: `track`, `support`, `rating`, `raise`

## Key fields introduced
`agentAssignmentModel`, `maxDeliveryRadiusKm`, `liveTrackingEnabled`, `bookingReference`, `agentDetails` (name, phone via proxy, vehicle, photo).
