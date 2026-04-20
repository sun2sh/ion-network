# B2C Make-to-Order (B2C-MTO)

Extends B2C-SF for products prepared after confirm. Once preparation starts, cancellation closes.

## Applicable categories
Food QSR (restaurants, cloud kitchens), custom bakery, tailoring, custom furniture

## Key differences from B2C-SF
- State machine: **mto** — PREPARING → READY → DISPATCHED → OUT_FOR_DELIVERY → DELIVERED
- Cancellation policy: `cancel.mto.nofee.before_prepare` — free before PREPARING, closed after
- `averagePreparationTime` required on provider; `preparationTime` required per item
- On `on_status[PREPARING]` — cancellation window closes

## API sequence
Same as B2C-SF. State code differences only in `on_status`.
