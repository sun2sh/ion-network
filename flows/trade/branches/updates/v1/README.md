# Updates Branch

Post-confirm order updates. Covers seller-pushed delay notifications, buyer-requested changes, and invoice amendments.

## Sub-branches

| Branch | Window | Initiator | Description |
|---|---|---|---|
| fulfillment-delay | on_confirm → on_status[DELIVERED] | BPP (unsolicited) | BPP pushes delay notification via on_update. New estimated delivery time declared. |
| update-delivery-address | on_confirm → on_status[DISPATCHED] | BAP | Buyer requests address change. BPP may accept or reject. Logistics re-routing cost may apply. |
| update-delivery-authorization | on_confirm → on_status[DELIVERED] | BAP | Buyer delegates collection to another person. Name + ID of authorized recipient declared. |
| buyer-instructions | on_confirm → on_status[DISPATCHED] | BAP | Buyer adds delivery instructions (gate code, leave at door, call before arriving). |
| update-sale-invoice | on_confirm → on_status[DELIVERED] | BAP | Buyer requests invoice amendment — different tax ID, entity name, invoice type. |
| price-adjustment | on_confirm → contract COMPLETE | BPP (unsolicited) | BPP adjusts quote post-confirm. Quote trail updated. BAP must re-confirm if delta > threshold. |
| ready-to-ship | on_confirm → on_status[DISPATCHED] | BPP | BPP signals package physically ready for LSP pickup. Triggers LSP agent dispatch. |

## API sequence
```
Buyer address change:
  BAP → /update (target.fulfillment.stops[].location = new address)
  BPP → /on_update (accepted) or /on_update (rejected, reason)

Delay notification:
  BPP → /on_update (fulfillment.tags.delay_reason, new estimatedDeliveryTime)

Price adjustment:
  BPP → /on_update (quote.breakup[] with changes, contractAttributes.quoteTrail[])
```
