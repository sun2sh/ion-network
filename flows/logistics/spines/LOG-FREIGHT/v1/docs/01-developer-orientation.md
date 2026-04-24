# LOG-FREIGHT — Developer Orientation

## What this spine is for

You are building a freight logistics integration — either as a carrier or freight forwarder (BPP) offering FTL, LTL, FCL, LCL, air cargo, rail, river, or bulk services, or as a BAP (shipper, 3PL, marketplace) booking freight capacity.

The defining characteristic of LOG-FREIGHT is **capacity-based booking**. Unlike LOG-PARCEL where a rate card produces a per-package price, freight booking is against capacity on a specific departure — a container slot on a vessel, aircraft payload, truck load, rail car. This means `/select` is always required — the catalog declares rate logic and capacity availability intent, but only `/select` confirms whether capacity exists on your requested date.

## As a BPP (carrier or freight forwarder)

**Phase 1 — Publish your catalog**

Your catalog declares capacity model, consolidation types, schedule type (regular sailing/flight vs ad-hoc), and route/corridor coverage. Rate logic declares pricing per capacity unit — per container, per cbm, per kg, per truck.

```
/catalog/publish → ION Catalogue Service → on_discover → BAPs
```

Key fields: `capacityModel`, `consolidationType`, `scheduleType`, `departurePattern`, `fleetType`, `incotermsSupported` (for LOG-XB).

**Phase 2 — Handle capacity reservation at /select**

Unlike parcel, `/select` is not optional — you must check and reserve capacity. Return a `reservationToken` with a `reservationHoldUntil` timestamp. BAP has until then to call `/init`.

At `/on_confirm`, return `billOfLadingReference` and confirmed departure/arrival times.

## As a BAP (shipper or 3PL)

**Phase 1 — Subscribe and build your rate understanding**

The freight catalog tells you rate logic — not binding per-shipment rates. You understand zone structures, consolidation types, incoterms. At booking time you always call `/select`.

**Phase 2 — Booking sequence**

```
/select → /on_select   (capacity reserved; hold window PT15M-PT4H typical)
/init → /on_init       (consignor/consignee details, cargo manifest, HS codes for XB)
/confirm → /on_confirm (bill of lading issued; scheduled departure locked)
```

After `/on_confirm`, the state machine progresses through departure events: BOOKING_CONFIRMED → READY_FOR_LOADING → LOADED → DEPARTED → IN_TRANSIT → ARRIVED → UNLOADED → AVAILABLE_FOR_COLLECTION → DELIVERED.

## Milk-run and multi-stop freight

Milk-run patterns (one vehicle, multiple pickups → one consolidation point) are handled via `performance.stops[]` carrying the stop sequence. Parent FWA governs the commercial envelope; each child shipment is a LOG-FREIGHT transaction referencing the parent.

## Multi-modal freight

Air + trucking, ocean + road: `performance.stops[]` carries each leg with its own carrier attribution. Performance state updates report the current leg's state.

## B2B and eKYC

All LOG-FREIGHT transactions are B2B. eKYC fires at `/init` for first-time relationships without an active FWA. NPWP, NIB, SIUP number, and authorised signatory are required. Subsequent transactions reuse verified credentials.

## Beckn 2.0 endpoints used

```
/catalog/publish → /catalog/on_publish
/select → /on_select           (ALWAYS required)
/init → /on_init               (eKYC sub-flow fires if no FWA)
/confirm → /on_confirm         (bill of lading issued)
/on_status (BPP pushes — departure events)
/track → /on_track             (vessel/flight tracking handle)
/update → /on_update           (weight discrepancy, address, disputes)
/cancel → /on_cancel           (window closes at DEPARTED)
/rate → /on_rate
/reconcile → /on_reconcile
/raise → ... (escalation)
/support → /on_support
```
