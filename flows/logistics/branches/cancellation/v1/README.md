# Cancellation Branch

Covers all logistics contract cancellation scenarios with explicit attribution model.

## Sub-branches
| Sub-branch | Window | Who triggers | Cost attribution |
|---|---|---|---|
| `cancel-buyer-prepickup` | on_confirm → PICKED_UP | BAP | Buyer if changed mind; no fault if payment issue |
| `cancel-lsp-initiated` | on_confirm → PICKED_UP | BPP | LSP if coverage failure; Consignor if not ready |
| `cancel-intransit` | PICKED_UP → OUT_FOR_DELIVERY | BAP | Buyer bears return freight |
| `cancel-tat-breach` | on_confirm + SLA breach | BAP | LSP bears cost + penalty |

## Attribution model
Every cancellation declares a reason code that determines: who bears the cost, whether a cancellation fee applies, whether RTO is triggered, and whether a refund is due and of what amount.

## API endpoints
Uses Beckn 2.0 `/cancel` (BAP → BPP) and `/on_cancel` (BPP → BAP). LSP-initiated cancellation uses unsolicited `/on_cancel`.

## Applies to
LOG-PARCEL, LOG-HYPERLOCAL (sub-branch: cancel-buyer-prepickup only — window is very tight), LOG-FREIGHT (all sub-branches), LOG-XB (note: window closes at export customs submission).
