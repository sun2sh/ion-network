# Cancellation Branch

Covers all cancellation scenarios for an active (confirmed) order.

## Sub-branches

| Branch | Window | Initiator | Key rules |
|---|---|---|---|
| cancel-full-buyer | on_confirm → on_status[DELIVERED] | BAP | Reason must be in `cancellationAllowedReasons`. Fee applies if state ≥ `cancellationFeeApplicableStates`. |
| cancel-full-seller | on_confirm → on_status[DISPATCHED] | BPP (unsolicited) | Seller-initiated — no fee to buyer. Full refund mandatory for prepaid. Reason code required. |
| cancel-partial-fulfillment | on_confirm → on_status[DISPATCHED] | Either | Only valid if `partialCancellationAllowed = true`. Quote trail updated for cancelled lines. |
| technical-cancellation-force | on_confirm → on_status[DELIVERED] | BAP | BAP sends cancel with `force = yes` after BPP fails to respond within TAT. Code = 999. Triggers raise to ION. |

## Refund rules
- Refund is always a **sub-step** inside a cancellation — never standalone
- Prepaid orders: full refund on seller-initiated cancel; partial refund if fee applies on buyer-initiated
- COD orders: no refund needed (payment not collected)
- Refund timeline: declared in `payment.refundTimeline` at on_cancel

## API sequence
```
cancel-full-buyer:
  BAP → /cancel (reason_code, optional: force=yes)
  BPP → /on_cancel (status=CANCELLED, refundAmount, cancellationFee if applicable)

cancel-full-seller (unsolicited):
  BPP → /on_cancel (status=CANCELLED, reason_code, full refund declared)
```
