# Return to Origin (RTO) Branch

Delivery failed. Package returns to seller origin. Three possible outcomes.

## Sub-branches

| Branch | Window | Trigger | Outcome |
|---|---|---|---|
| RTO-initiated | on_status[DISPATCHED] → on_status[DELIVERED] | Delivery failed: consumer unavailable, refused delivery, OTP mismatch | Logistics begins return journey |
| RTO-delivered | after RTO-initiated | Package back at seller location | Refund triggered for prepaid orders |
| RTO-disposed | after RTO-initiated | Seller decides to dispose (perishable, damaged, low value) | No return to seller; refund still applies for prepaid |

## Refund rules
- Prepaid orders: full refund on RTO-delivered or RTO-disposed
- COD orders: no money collected; no refund needed
- Seller may reattempt delivery before RTO-initiated if consumer contactable

## API sequence
```
BPP → /on_status (RTO_INITIATED, rtoReason: undeliverable/refused/otp_failed)
BPP → /on_status (RTO_IN_TRANSIT)
BPP → /on_status (RTO_DELIVERED or RTO_DISPOSED)
BPP → /on_update (refundAmount — for prepaid orders)
```

## State machine
`performance-states/v1/states.yaml#rto`
