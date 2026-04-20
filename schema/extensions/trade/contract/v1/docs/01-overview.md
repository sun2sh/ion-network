# Trade Contract Extension — Overview

Order-level fields locked at `on_confirm`. These persist through the full contract lifecycle.

## Fields set at init (buyer-declared)
`invoicePreferences`, `deliveryPreferences`, `gift`, `purchaseOrderReference`, `buyerInstructions`

## Fields set at on_confirm (BPP-assigned)
`fulfillingLocationId`, `fakturPajakReference`

## quoteTrail
Every post-confirm price change adds an entry to `quoteTrail[]`. This provides an auditable trail for reconciliation — the final settlement amount can always be derived from the original quote plus all trail entries.

## Subscription fields
`subscriptionBillingCycle` and `subscriptionNextBillingDate` are only populated for B2C-SUB pattern. `subscriptionNextBillingDate` is updated by BPP after each successful billing event.
