# ION Trade Sector Flows — Sector A

Physical goods commerce on ION. Every transaction starts with a spine — the happy path from catalog through to contract complete. Branches attach to the spine at defined windows and handle everything that isn't the happy path.

---

## How to read the flow map

```
SPINE
  publish → subscribe → on_discover
  → select → on_select
  → init → on_init
  [on_init may also arrive unsolicited from BPP — payment status update]
  → confirm → on_confirm
  → status → on_status [solicited]
  → on_status [unsolicited — BPP pushes proactively]
  (×N through all performance states)
  → rating → on_rate
  → reconcile → on_reconcile
  [Contract: COMPLETE]
```

The spine runs in order. Branches can activate at any point within their declared window. Multiple branches can run concurrently. Cross-cutting branches (track, support, rating, reconcile) are available on all spines. The `raise` channel is separate — it goes participant → ION network, not BAP↔BPP.

---

## Spines

One spine per commerce pattern. Each spine defines the full API sequence, required and conditional fields per step, applicable branches, and the performance state machine in use.

| Code | Pattern | Status | State machine |
|---|---|---|---|
| B2C-SF | B2C Single Fulfilment | ready | standard |
| B2C-MTO | B2C Make-to-Order | ready | mto |
| B2C-SUB | B2C Subscription | ready | standard (per cycle) |
| B2C-LIVE | B2C Live / OTT / Social Commerce | ready | standard |
| B2C-DIG | B2C Digital Goods (pulsa, vouchers, top-ups) | ready | digital |
| B2B-PP | B2B Wholesale Prepaid | ready | standard |
| B2B-CR | B2B Wholesale Credit | ready | standard |
| MP-IH | Marketplace Inventory Held | ready | standard |
| MP-IL | Marketplace Inventory Less | ready | standard |
| AUC-F | Forward Auction | ready | standard |
| AUC-R | Procurement Reverse Auction | ready | standard |
| XB | Cross-Border Export | ready | standard + XB additions |
| B2G | B2G Government Procurement | ready | standard |

---

## Branches

Branches are conditional sub-flows. They are not spine variants — they activate against an existing spine transaction when a specific condition is met. A transaction can have multiple branches active simultaneously.

### During-Transaction Branches

These attach between `select` and `on_confirm`. They handle decisions that shape the transaction before it is committed.

| Branch | Window | What it handles |
|---|---|---|
| fulfillment-type | select → on_confirm | Consumer choosing delivery vs self-pickup |
| payment-prepaid-BAP-collected | init → on_confirm | BAP collects payment upfront; QRIS, EWallet, VA |
| payment-prepaid-BPP-collected | init → confirm | BPP collects upfront; includes unsolicited on_init for payment status |
| payment-COD-BAP-collected | init → on_status[DELIVERED] | COD where marketplace collects |
| payment-COD-BPP-collected | init → on_status[DELIVERED] | COD where seller collects at door |
| multi-fulfillment | select → init | Order split across multiple fulfilment centres |
| cancellation-terms | on_init → on_confirm | Buyer reviews and accepts cancellation fee terms |
| on-network-LSP | on_confirm | BPP triggers a separate Logistics contract on ION |
| technical-cancellation-confirm-failure-BAP | confirm | BAP NACKs on_confirm → cancels with code 999 |
| technical-cancellation-confirm-failure-BPP | on_confirm | BPP NACKs on_confirm → cancels with code 998 |

### Post-Confirm Branches

These attach after `on_confirm` when the contract is live. They handle post-order events.

| Branch | Window | What it handles |
|---|---|---|
| cancel-full-buyer | on_confirm → on_status[DELIVERED] | Buyer-initiated full cancellation |
| cancel-full-seller | on_confirm → on_status[DISPATCHED] | Seller-initiated full cancellation |
| cancel-partial-fulfillment | on_confirm → on_status[DISPATCHED] | Partial cancellation of a multi-item order |
| technical-cancellation-force | on_confirm → on_status[DELIVERED] | BAP force-cancels after BPP TAT breach |
| fulfillment-delay | on_confirm → on_status[DELIVERED] | Unsolicited on_update from BPP declaring delay |
| update-delivery-address | on_confirm → on_status[DISPATCHED] | Buyer requests address change |
| update-delivery-authorization | on_confirm → on_status[DELIVERED] | Buyer delegates collection authority to another person |
| buyer-instructions | on_confirm → on_status[DISPATCHED] | Buyer adds or updates delivery instructions |
| update-sale-invoice | on_confirm → on_status[DELIVERED] | Buyer requests invoice amendment (tax ID, entity name) |
| price-adjustment | on_confirm → contract COMPLETE | Unsolicited on_update from BPP adjusting quote |
| RTO-initiated | on_status[DISPATCHED] → on_status[DELIVERED] | Delivery failed, package returning to origin |
| RTO-disposed | after RTO-initiated | Seller disposes package rather than returning |
| RTO-delivered | after RTO-initiated | Package delivered back to seller; triggers refund |
| return-initiated | on_status[DELIVERED] → return window expiry | Buyer raises return request |
| return-picked-up | after return-initiated | Logistics collects return from buyer |
| return-delivered | after return-picked-up | Return received by seller; triggers refund |
| replacement | after return-initiated | Seller sends replacement instead of refund |
| exchange | after return-initiated | Return with pickup + new forward delivery |
| cancel-return-request | after return-initiated → before return-picked-up | Buyer cancels their own return request |
| refund | inside cancel, RTO-delivered, return-delivered | Always a sub-step, never standalone |

### Cross-Cutting Branches

These are available on every spine after `on_confirm`. They run concurrently with the main flow and with each other.

| Branch | Window | What it handles |
|---|---|---|
| track / on_track | on_confirm → on_status[DELIVERED] | Real-time GPS position of delivery agent. Position updates, not state changes. |
| support / on_support | on_confirm → contract COMPLETE | Buyer raises issue about an order to the seller. try=true previews channels; try=false creates ticket. SLA tracked by ION Central. |
| rating / on_rate | on_status[DELIVERED] → rating window expiry | Post-delivery rating. PROVIDER, ITEM, FULFILLMENT, AGENT categories. |
| reconcile / on_reconcile | on_status[DELIVERED] → settlement window | BAP and BPP agree on financial settlement. ION Central orchestrated. |

### Network Channel — raise / on_raise

`raise` is not a BAP↔BPP branch. It is a participant-to-ION channel.

```
BAP or BPP → raise → ION Network
ION Network → on_raise → BAP or BPP
```

A participant raises a formal issue to ION about network behaviour, policy breach, counterpart misconduct, or an unresolved reconciliation dispute. This escalates beyond what `support` can handle. It can be triggered at any point in the transaction lifecycle.

---

## Branch file reference

```
flows/trade/branches/
  during-transaction/v1/     ← all 10 during-transaction branches
  cancellation/v1/           ← cancel-full-buyer, cancel-full-seller, cancel-partial, force-cancel
  returns/v1/                ← return-initiated through return-delivered, replacement, exchange
  RTO/v1/                    ← RTO-initiated, RTO-disposed, RTO-delivered
  updates/v1/                ← address, authorization, instructions, invoice, price, delay
  cross-cutting/v1/          ← track, support, rating, reconcile, raise
```

---

## Performance state machines

All state codes are canonical — defined once in `schema/extensions/trade/performance-states/v1/states.yaml`. Spines and branches reference the canonical codes; they never redefine them.

| Machine | Used by | States |
|---|---|---|
| standard | B2C-SF, B2B-PP, B2B-CR, MP-IH, MP-IL, AUC-F, AUC-R, XB, B2G | PLANNED → PACKED → DISPATCHED → OUT_FOR_DELIVERY → DELIVERED |
| mto | B2C-MTO, food QSR | PREPARING → READY → DISPATCHED → OUT_FOR_DELIVERY → DELIVERED |
| self_pickup | all patterns, SELF_PICKUP mode | PACKED → READY_FOR_PICKUP → PICKED_UP |
| return | all return branches | RETURN_INITIATED → RETURN_APPROVED → RETURN_AGENT_ASSIGNED → RETURN_PICKED → RETURN_DELIVERED |
| replacement | replacement branch | REPLACEMENT_DISPATCHED → REPLACEMENT_DELIVERED |
| rto | RTO branch | RTO_INITIATED → RTO_IN_TRANSIT → RTO_DELIVERED / RTO_DISPOSED |
| digital | B2C-DIG (digital goods) | PENDING_OPERATOR → DELIVERED / DELIVERY_FAILED |

---

## Finding flows in Atlas

ION Atlas lets you search and browse flow definitions alongside schema fields. Use this when you want to understand a field in context — not just what it is, but where in the transaction lifecycle it appears and which branches set it.

```bash
ion search "when does AWB number get set"
ion search "cancellation fee fields"
ion search "return window"
```

Web Explorer: `devlabs.ion.id/atlas (coming soon)`


---

## Policy Terms Registry

Each spine declares `requiredPolicyCategories` in its `profile.json`. Offers published under that spine must declare policy IRIs for every required category. Unknown IRIs rejected at catalog publish with ION-2010.

Categories and typical bindings:

| Spine | Required policy categories |
|---|---|
| B2C-SF | RETURN, CANCELLATION, WARRANTY, DISPUTE, GRIEVANCE_SLA, PAYMENT_TERMS |
| B2C-MTO | CANCELLATION, DISPUTE, GRIEVANCE_SLA, PAYMENT_TERMS |
| B2C-SUB | CANCELLATION, WARRANTY, DISPUTE, GRIEVANCE_SLA, PAYMENT_TERMS |
| B2C-LIVE | all 6 |
| B2C-DIG | CANCELLATION, DISPUTE, GRIEVANCE_SLA, PAYMENT_TERMS |
| B2B-PP, B2B-CR, MP-IH, MP-IL, AUC-R, XB, B2G | all 6 |
| AUC-F | RETURN, CANCELLATION, DISPUTE, GRIEVANCE_SLA, PAYMENT_TERMS (no warranty in auction model) |

See `policies/README.md` for the registry model.
