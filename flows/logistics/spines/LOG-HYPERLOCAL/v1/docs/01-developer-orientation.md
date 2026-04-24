# LOG-HYPERLOCAL — Developer Orientation

## What this spine is for

You are building a sub-day, same-city delivery integration — either as an on-demand courier platform (BPP) offering rider-based delivery, or as a BAP (marketplace, food delivery, quick commerce) booking instant deliveries.

LOG-HYPERLOCAL covers GoSend-style, GrabExpress-style, and Paxel-instant patterns. What distinguishes this from LOG-PARCEL: there are no hubs, the rider is exposed to the buyer, tracking is real-time GPS, and agent assignment has four distinct models (PRE_ASSIGNED, POOL_ASSIGNED, FIFO_AT_PICKUP, DEDICATED_FLEET).

## As a BPP (courier platform)

**Phase 1 — Publish your catalog**

Your catalog must declare `agentAssignmentModel` per offer. This is the single most important field for BAPs — it tells them when to expect rider identity in `on_status` updates and how to communicate ETAs to end users.

```
/catalog/publish → ION Catalogue Service → on_discover → BAP
```

Publish: city-level coverage, service levels (INSTANT, SAME_DAY), max radius, live tracking flag, rate logic (almost always DISTANCE_BASED + surge), `selectRequired: true` for surge-priced offers, and all policy IRIs.

**Phase 2 — Handle transaction calls**

For FIFO_AT_PICKUP: buyer books, you dispatch to merchant location, first available rider takes the first ready order. You only know rider identity at PICKED_UP state — expose `agentDetails` in that `on_status` push.

Real-time GPS updates via `/on_track` endpoint (not `/on_status`). Push GPS to the tracking handle URL you return in `/on_track`.

## As a BAP (marketplace, quick commerce)

**Phase 1 — Subscribe to catalogs**

Subscribe to catalogs from all hyperlocal providers in your operating cities. The catalog tells you each provider's coverage radius, assignment model, and whether they support COD.

**Phase 2 — Transact**

Because `selectRequired: true` for most hyperlocal offers (surge pricing), always call `/select` to get a binding quote before `/init`. Quote validity is typically PT5M — complete the booking quickly.

After `/on_confirm`, your UI must adapt based on `agentAssignmentModel`:
- PRE_ASSIGNED/DEDICATED_FLEET: "Rider Agus is on the way" from booking confirmation
- POOL_ASSIGNED: "Finding you a rider..." until RIDER_EN_ROUTE_TO_PICKUP
- FIFO_AT_PICKUP: "Your order is being prepared. A rider will collect it shortly." until PICKED_UP

## Key differences from LOG-PARCEL

| | LOG-HYPERLOCAL | LOG-PARCEL |
|---|---|---|
| Shipment identity | `bookingReference` | `awbNumber` |
| Hubs | None | 0–2 hubs |
| Tracking | Real-time GPS via /track | Scan events via /status |
| Rider identity | Exposed mid-flow | Opaque |
| State machine | Minutes-scale | Hours-days |
| Select | Almost always required (surge) | Depends on offer |
| Cancellation window | Tight (before pickup) | Wider |

## Beckn 2.0 endpoints used

```
/catalog/publish → /catalog/on_publish
/select → /on_select
/init → /on_init
/confirm → /on_confirm
/on_status (BPP pushes unsolicited)
/track → /on_track (real-time GPS handle)
/update → /on_update (COD, address change, cancellation)
/cancel → /on_cancel
/rate → /on_rate
/support → /on_support
/raise → /on_raise → /raise_status → ... (if escalation needed)
```

Note: There is no `/search` in Beckn 2.0. Discovery is via the catalog subscription model.
