# Weight Dispute Branch

Handles discrepancies between declared and measured weight/dimensions.

## Applies to
LOG-PARCEL, LOG-FREIGHT.

## Trigger
BPP measures actual weight at pickup or hub and finds it exceeds declared weight by more than the policy tolerance.

## Sub-branches
`weight-discrepancy-raised`, `weight-discrepancy-accepted`, `weight-discrepancy-countered`, `weight-discrepancy-escalated`.

## Resolution flow
BPP raises via `/on_update` → BAP accepts or counters → if unresolved within policy SLA, either party escalates via `/raise` → ION Central adjudicates.

## Policy references
`ion://policy/weight-dispute.standard-10pct-tolerance` (public), `ion://policy/weight-dispute.enterprise-5pct-tolerance` (FWA-governed).
