# Procurement Reverse Auction (AUC-R)

Buyer publishes requirement; sellers bid down. Lowest valid bid wins.

## Applicable categories
Government procurement (LKPP), corporate procurement, hospital supply, agritech bulk buying

## Mechanism
- BAP publishes RFQ via `/discover` with procurement intent (ceiling price, spec, delivery deadline)
- Multiple BPPs respond via `on_discover` with their quotes
- BAP evaluates (price, delivery time, compliance, track record) and sends `/select` to winner
- Winner proceeds: on_select → init → on_init → confirm → on_confirm → standard fulfilment

## Key fields
`rfq_id`, `ceiling_price`, `submission_deadline`, `tkdn_percentage`, `technical_compliance`, `incoterms` (for export procurement)

## Performance state machine
`performance-states/v1/states.yaml#standard`
Standard delivery machine from DISPATCHED onwards (post procurement fulfilment).
