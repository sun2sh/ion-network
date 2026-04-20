# Cross-Cutting Branch

Available on all spines after `on_confirm`. These sub-flows run concurrently with the main spine and with each other.

## Sub-flows

### track / on_track
```
Window:  on_confirm → on_status[DELIVERED]
Purpose: Real-time GPS position of the delivery agent
Note:    Distinct from /status — track gives position, status gives state transitions
BAP → /track (order_id, fulfillment_id)
BPP → /on_track (realTimeGps: latitude, longitude, accuracy, timestamp)
```

### support / on_support
```
Window:  on_confirm → contract COMPLETE
Purpose: Buyer raises issue about order to seller
Flow:    try=true  → preview channels (get contact options without creating ticket)
         try=false → create formal complaint ticket
SLA:     Tracked by ION Central. Escalates to GRO then ODR if unresolved.
BAP → /support (ref_id, try=true)           → BPP returns contact channels
BAP → /support (issue object, try=false)    → BPP creates ticket, returns issue ID
BPP → /on_support (ticket ID, expected resolution time)
```

### rating / on_rate
```
Window:  on_status[DELIVERED] → ratingWindowDays expiry
Purpose: Post-delivery rating on up to 4 categories
         PROVIDER, ITEM, FULFILLMENT, AGENT
BAP → /rate (ratings[] with category, value 1-5, optional feedback text)
BPP → /on_rate (optional: feedbackUrl for extended feedback form)
```

### reconcile / on_reconcile
```
Window:  on_status[DELIVERED] → settlement window expiry
Purpose: BAP and BPP agree on financial settlement amounts
         Withholding released to BPP after return window closes
BAP → /reconcile (baseContractAmount, finderFee, withholdingAmount, adjustments[])
BPP → /on_reconcile (reconStatus: AGREED/DISPUTED, recon_status: 01/02/03)
If DISPUTED → raise to ION via raise/on_raise channel
```

### raise / on_raise — Network Channel
```
Direction:  participant → ION network  (NOT BAP↔BPP)
Window:     Any point in transaction lifecycle
Purpose:    Formal escalation TO ION about:
            - Network policy breach by counterpart
            - Counterpart misconduct
            - Reconcile dispute that support could not resolve
            - Force-cancel dispute
            - Technical failure unresolved by support
participant → /raise (ticket: type, priority, description, contractId)
ION         → /on_raise (ticketId, acknowledgment)
participant → /raise_status → ION → /on_raise_status
participant → /raise_details → ION → /on_raise_details (full thread)
```
