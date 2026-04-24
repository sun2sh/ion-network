# Attempts Branch

Delivery attempt management for failed deliveries. Five sub-branches covering all resolution paths after a first missed delivery.

## Sub-branches
| Sub-branch | Trigger | Resolution |
|---|---|---|
| `attempt-ndr` | BPP pushes DELIVERY_ATTEMPT_FAILED | Buyer receives NDR notification with resolution deadline |
| `attempt-reschedule` | Buyer picks new window via /update | BPP confirms new date/window |
| `attempt-address-change` | Buyer corrects address via /update | BPP recomputes zone, confirms or re-quotes |
| `attempt-self-pickup-conversion` | Buyer switches to agent-point pickup | BPP issues OTP and hold window |
| `attempt-auto-rto` | Max attempts or buyer window expired | BPP initiates RTO, notifies BAP |

## NDR reason codes
NDR-001 through NDR-008 covering: not available, address not found, refused, requested reschedule, access denied, condition concern, no safe location, COD not available.

## Policy references
Attempt limits, re-attempt charges, and resolution windows are defined in the offer's `re-attempt policy` IRI. The branch enforces the declared policy; it does not hardcode attempt counts.

## Applies to
LOG-PARCEL (full sub-branch set), LOG-HYPERLOCAL (NDR, reschedule, auto-RTO only — tighter windows).
