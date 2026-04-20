# B2C Subscription (B2C-SUB)

Recurring purchases on a defined billing cycle. Mandate setup at first confirm; subsequent cycles auto-trigger.

## Applicable categories
Grocery subscriptions, meal kit delivery, supplements, dairy, water delivery, pet food, FMCG auto-reorder

## Key additions to B2C-SF
- `subscriptionBillingCycle`: WEEKLY / FORTNIGHTLY / MONTHLY / QUARTERLY / ANNUAL
- `subscriptionNextBillingDate`: updated after each successful billing
- Mandate setup at on_init (UPI Autopay or e-mandate deep link)
- Lifecycle management via /update: PAUSE, SKIP, MODIFY_QUANTITY, RESUME
- Cancellation applies to future cycles; in-progress delivery completes normally

## API sequence
```
Phase 2  select (with billing_cycle tag) → on_select (confirms billing terms)
         init → on_init (mandate setup instructions)
         confirm → on_confirm (subscription created, first cycle scheduled)

Phase 3  Per-cycle: PACKED → DISPATCHED → DELIVERED (as B2C-SF)

Phase 4  update[PAUSE/SKIP/RESUME/MODIFY] — lifecycle management
         cancel[SUBSCRIPTION] — terminate recurring
```

## Performance state machine
`performance-states/v1/states.yaml#standard`
Applies per delivery cycle. Each recurring delivery is a fresh standard run.
