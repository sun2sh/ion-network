# B2B Wholesale Credit / BNPL (B2B-CR)

B2B wholesale with deferred payment. Buyer receives goods first; pays within agreed credit terms.


## Performance state machine
`performance-states/v1/states.yaml#standard`
Delivery follows standard states. Credit collection (Phase 4) runs post-DELIVERED.

## Extends
B2B-PP — all B2B-PP fields apply. Credit adds:

## Key additions
- `creditTermsDays`: NET 7, NET 14, NET 30, NET 45, NET 60, NET 90
- `paymentDueDate`: computed as delivery date + creditTermsDays; locked at confirm
- `settlementBasis: AFTER_PAYMENT_DUE_DATE`
- Payment timing: POST_FULFILLMENT (not ON_ORDER as in B2B-PP)
- Dunning flow: BPP sends on_update reminders at T-7, T-3, T-1 before due date
- BNPL option: Kredivo Business, Akulaku for Merchant — `FINANCE_CHARGE` in breakup
- PPh23 2% withheld by buyer for service components (if applicable)
- `payment.status = PENDING` at confirm (unlike B2B-PP where status = PAID)
