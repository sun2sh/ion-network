# performance/v1 — Logistics Performance Attributes

Attaches to `beckn:Performance.performanceAttributes`.

## What it covers

The execution record of the logistics contract. Every state transition adds fields to the performance object. The BAP reads this to track the shipment; the contract's performance history is the primary evidence trail for disputes.

## Shipment identity by spine

| Spine | Identity field | Issued at |
|---|---|---|
| LOG-PARCEL | `awbNumber` | `/on_confirm` |
| LOG-HYPERLOCAL | `bookingReference` | `/on_confirm` |
| LOG-FREIGHT | `billOfLadingReference` | `/on_confirm` |
| LOG-RORO | `ticketReference` | `/on_confirm` |
| LOG-WAREHOUSE | `storageContractReference` | `/on_confirm` |

## Tracking model — status vs track

**`/on_status` (pushed by BPP)** — point-in-time state transitions. Every state change pushes an unsolicited `on_status`. BAPs receive these without polling.

**`/track` → `/on_track`** — real-time streaming handle. BAP requests a tracking URL or WebSocket endpoint. For LOG-HYPERLOCAL, this streams live GPS coordinates. For LOG-PARCEL, it returns the AWB tracking URL that the carrier's website serves.

These are complementary: `on_status` for state machine events, `track/on_track` for continuous real-time position.

## Routing topology

For LOG-PARCEL, `routingTopology` is set in `/on_select` and confirmed in `/on_confirm`:
- `P2P` — direct pickup to delivery; no hub states in the state machine
- `P2H2P` — single hub; AT_ORIGIN_HUB and AT_DESTINATION_HUB states fire
- `P2H2H2P` — both hubs with inter-hub transit; SORTED_AT_ORIGIN, IN_TRANSIT_INTERHUB, SORTED_AT_DESTINATION states fire

## Proof of pickup and delivery

Both types (pickup and delivery) must be declared at `/on_confirm` via `proofOfPickupType` and `proofOfDeliveryType`:

| Type | What it means |
|---|---|
| `OTP` | One-time password generated at booking; buyer shares with rider at delivery |
| `PHOTO` | Photo captured at pickup/delivery location with timestamp and GPS |
| `SIGNATURE` | Digital or physical signature captured |
| `BIOMETRIC` | Fingerprint or face recognition (uncommon, enterprise) |
| `NONE` | No proof required (documents, some B2B) |

For cold chain, temperature reading is required alongside the proof at both pickup and delivery.

## Agent/rider details

For LOG-HYPERLOCAL, `agentDetails` carries: rider name, phone via proxy (never the real number), vehicle type, vehicle plate, and photo URL. When this is exposed depends on `offer.agentAssignmentModel`:

| Model | agentDetails exposed at |
|---|---|
| PRE_ASSIGNED | `on_status[RIDER_ASSIGNED]` |
| DEDICATED_FLEET | `on_status[BOOKING_CONFIRMED]` |
| POOL_ASSIGNED | `on_status[RIDER_EN_ROUTE_TO_PICKUP]` |
| FIFO_AT_PICKUP | `on_status[PICKED_UP]` — only when rider takes the order |

## Cold chain fields

```yaml
temperatureReading:
  value: 4.2
  unit: celsius
  timestamp: "2026-04-22T10:15:00Z"
  location: "Pickup — Jl. Sudirman 45"
  deviceId: "DEVICE-COLDCHAIN-001"
  excursionDetected: false
coldChainIntegrityVerified: true
```

These fire in `on_status[PICKED_UP]` and `on_status[DELIVERED]` when cold chain is declared on the resource. If `coldChainIntegrityVerified = false` at delivery, the damage-claim branch is immediately eligible.

## Weight discrepancy fields

```yaml
actualWeight:
  value: 3.2              # declared was 2.5kg — 28% over
  unit: kilogram
  measuredAt: ORIGIN_HUB  # PICKUP | ORIGIN_HUB | DESTINATION_HUB
  measurementTimestamp: "2026-04-22T14:30:00Z"
```

If actual weight exceeds declared by more than the `offer.weightDisputePolicy` tolerance, BPP raises the weight-dispute branch via `/on_update`.

## Attempt management

```yaml
attemptNumber: 2
ndrReasonCode: "NDR-001"           # Consignee not available
ndrTimestamp: "2026-04-23T11:00Z"
attemptsRemaining: 1
buyerResolutionDeadline: "2026-04-23T23:59Z"
```

After DELIVERY_ATTEMPT_FAILED, the attempts branch opens. BAP has until `buyerResolutionDeadline` to reschedule, change address, or switch to self-pickup.

## Capacity reservation (LOG-FREIGHT)

```yaml
reservedCapacity:
  quantity: 1
  unit: container_20ft
  reservationToken: "CAP-RES-20260422-001"
reservationHoldUntil: "2026-04-22T10:45:00Z"
proposedDeparture: "2026-04-25T08:00:00Z"
capacityConfirmed: true
```

Returned in `/on_select` for freight. If BAP does not reach `/confirm` before `reservationHoldUntil`, capacity is released.

## SLA status

```yaml
slaStatus: ON_TIME    # ON_TIME | AT_RISK | BREACHED
```

BPP optionally includes this in `on_status` updates when monitoring against `offer.slaPolicy`. If `BREACHED`, reconcile step will carry `slaRebateAmount` per the policy formula.
