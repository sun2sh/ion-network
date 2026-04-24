# Cross-Cutting Branches

Branches available on all logistics spines. All use exact Beckn 2.0 endpoints.

## Sub-branches and their Beckn 2.0 endpoints

| Sub-branch | Beckn 2.0 endpoints | Purpose |
|---|---|---|
| `track` | `/track` + `/on_track` | Real-time tracking handle (URL/WebSocket) |
| `support` | `/support` + `/on_support` | Customer care queries and support tickets |
| `rating` | `/rate` + `/on_rate` | Post-delivery ratings per dimension |
| `reconcile` | `/reconcile` + `/on_reconcile` | Financial settlement reconciliation |
| `raise` | `/raise` + `/on_raise` + `/raise_status` + `/on_raise_status` + `/raise_details` + `/on_raise_details` | Network escalation |

## context.try support (Beckn 2.0)

`context.try=true` sandbox flag is supported on:
- `support` — previews available channels without creating ticket
- `rate` — previews rating form without recording
- `reconcile` — previews settlement statement without committing

## track vs status

`/status` and `/on_status` report point-in-time state. `/track` and `/on_track` return a real-time streaming handle (URL or WebSocket) for continuous live tracking. For LOG-HYPERLOCAL this includes live GPS. For LOG-PARCEL it returns the AWB tracking URL.

## support vs dispute

`/support` is for customer queries — rider contact, delivery rescheduling, documentation. Financial disputes use `/update` with policy IRI references. Unresolved disputes escalate to `/raise`.

## Full raise protocol

6 Beckn 2.0 steps: raise → on_raise (acknowledgement) → raise_status → on_raise_status (polling) → raise_details → on_raise_details (full thread). ION Central adjudicates using the contract's /update history as the evidence trail.

## reconcile timing

After contract COMPLETE. Covers net settlement: freight base, weight adjustments, SLA rebates, COD amounts, PPN, FWA volume rebates. If reconStatus=DISPUTED, raise ticket is next step.
