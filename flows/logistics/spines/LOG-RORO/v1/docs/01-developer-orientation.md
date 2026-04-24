# LOG-RORO — Developer Orientation

## What this spine is for

You are building a Ro-Ro ferry booking integration — either as a ferry operator (BPP) offering vehicle-on-vessel services, or as a BAP (fleet operator, logistics company, individual vehicle owner) booking ferry crossings.

LOG-RORO covers vehicle-accompanied cargo on Ro-Ro ferries and vessels. The consignor typically drives the vehicle onto the ferry at origin port and off at destination port. Covers ASDP Indonesia Ferry routes (Ketapang-Gilimanuk Java-Bali, Merak-Bakauheni Java-Sumatra) and private Ro-Ro operators. The vehicle IS the resource; port events drive the state machine.

## Key difference from LOG-FREIGHT

In LOG-FREIGHT, cargo is loaded onto the carrier's vessel and the shipper has no presence. In LOG-RORO, the consignor (or their driver) accompanies the vehicle throughout. The consignor, consignee, and driver can all be the same person. There is no pickup or delivery address — the transaction is port-to-port.

## As a BPP (Ro-Ro operator)

**Catalog** declares: ports served, vehicle categories accepted (PASSENGER_CAR, LIGHT_TRUCK, HEAVY_TRUCK, MOTORCYCLE, TRAILER), sailing schedule (departure times per route per day of week), crossing duration, and vessel slot capacity per sailing.

**At /select**: BAP requests a specific sailing. You confirm slot availability and return `boardingWindow` — the time range within which the vehicle must check in.

**At /on_confirm**: Return `ticketReference` and `boardingGate`.

State machine: TICKET_ISSUED → CHECKED_IN → BOARDED → SAILED → ARRIVED_AT_PORT → DISEMBARKED → EXITED_PORT.

## As a BAP (fleet operator, transporter)

Subscribe to catalogs from ASDP and private Ro-Ro operators. Your catalog shows sailing schedules, vehicle categories accepted, and per-category pricing.

Call `/select` with your vehicle details (category, registration, dimensions, weight) and requested sailing time. `/on_select` confirms the slot and boarding window.

After `/on_confirm`, present your `ticketReference` at the port gate. Drive on, sail, drive off.

## Missed sailing

If the vehicle does not board before the vessel's departure (outside `boardingWindow`), the `missed-sailing` branch activates. Error code ION-LOG-6503. BAP may rebook on the next available sailing per the missed-sailing policy.

## Beckn 2.0 endpoints used

```
/catalog/publish → /catalog/on_publish
/select → /on_select           (capacity per sailing; always required)
/init → /on_init               (driver identity, vehicle registration)
/confirm → /on_confirm         (ticket reference, boarding gate)
/on_status (BPP pushes — port events)
/cancel → /on_cancel           (window closes at CHECKED_IN)
/rate → /on_rate
/support → /on_support
/raise → ... (escalation)
```
