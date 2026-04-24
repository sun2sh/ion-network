# ION Logistics Sector Flows — Sector B

Movement and storage of physical goods on ION. Every transaction starts with a spine — the happy path from catalog through to contract complete. Branches attach to the spine at defined windows and handle everything that isn't the happy path.

---

## How to read the flow map

### Phase 1 — Catalog (Beckn 2.0 catalog endpoints)

Beckn 2.0 supports BOTH active query and subscription-based discovery:

```
Discovery model A — Active query (pull):
BAP → /discover              → BPP / CDS        (BAP carries DiscoverAction.intent)
BAP ← /on_discover           ← BPP / CDS        (catalogs returned as callback)

Discovery model B — Subscription (push):
BPP → /catalog/publish        → ION CDS          (BPP publishes; updated on change)
      /catalog/on_publish     ← ION CDS          (per-catalog processing result)
BAP → /catalog/subscription                      (BAP subscribes to slice)
BAP ← /on_discover           ← CDS               (catalogs pushed on change)

Supplementary endpoints:
BAP → /catalog/pull                               (BAP pulls snapshot on demand)
BAP → /catalog/master/search                      (searches the master catalog index)
BAP → /catalog/master/{masterItemId}              (fetches a specific master item)
BAP → /catalog/master/schemaTypes                 (lists available schema types)
```

ION Logistics BPPs MUST support `/catalog/publish` for subscription-based delivery. BPPs SHOULD additionally support `/discover` to serve BAPs that prefer active query — particularly useful for spot-rate lookups in LOG-FREIGHT and LOG-RORO where catalog-based rates are indicative rather than binding.

### Phase 2 — Transaction (Beckn 2.0 transaction endpoints, direct BAP↔BPP)

```
BAP → /select   → BPP → /on_select   [OPTIONAL per offer.selectRequired; REQUIRED when:
                                        - rateLogic requires zone/weight computation
                                        - capacity-constrained (freight, ferry, air)
                                        - surge pricing active
                                        - FWA not covering this shipment]
BAP → /init     → BPP → /on_init     [ALWAYS — commitment with party details and payment method]
BAP → /confirm  → BPP → /on_confirm  [ALWAYS — binding; AWB/BL/ticket issued]
BPP → /on_status (×N, unsolicited)   [BPP pushes at every state transition]
BAP → /status   → BPP → /on_status  [solicited status check, any time]
BAP → /track    → BPP → /on_track   [real-time tracking handle — URL or WebSocket]
BAP → /update   → BPP → /on_update  [branch-triggered mutations — disputes, address change, etc.]
BPP → /on_update (unsolicited)       [BPP-initiated updates — weight dispute, excursion, RTS ack]
BAP → /cancel   → BPP → /on_cancel  [cancellation branches]
```

### Phase 3 — Post-fulfilment (after contract COMPLETE)

```
# Beckn 2.0 native
BAP → /rate      → BPP → /on_rate           [ratings — context.try=true preview]
BAP → /support   → BPP → /on_support        [customer care — context.try=true]

# ION protocol extensions (not in Beckn 2.0 core — see docs/04)
BAP → /reconcile → BPP → /on_reconcile      [settlement recon — context.try=true]
BAP or BPP → /raise → ION Gateway → /on_raise   [network dispute adjudication]
                    → /raise_status → /on_raise_status
                    → /raise_details → /on_raise_details
```

Branches can activate at any point within their declared window. Multiple branches can run concurrently. The `/raise` channel goes participant → ION network, not BAP↔BPP. Disputes flow through `/update` with policy IRIs before escalating to `/raise`.

---

## Spines

One spine per logistics transaction archetype. Each spine defines the full API sequence, required and conditional fields per step, applicable branches, and the performance state machine in use.

| Code | Archetype | Status | State machine |
|---|---|---|---|
| LOG-HYPERLOCAL | Sub-day rider-based delivery (GoSend, GrabExpress, Paxel instant) | ready | hyperlocal |
| LOG-PARCEL | Hub-routed parcel, domestic and cross-border-by-parcel, B2C and B2B | ready | parcel (P2P, P2H2P, P2H2H2P variants) |
| LOG-FREIGHT | Capacity-based freight — FTL/LTL, FCL/LCL, air cargo, rail, river, bulk | ready | freight-capacity |
| LOG-RORO | Self-accompanied cargo on ferries and Ro-Ro vessels (Java-Bali, Java-Sumatra strait crossings) | ready | roro |
| LOG-XB | Cross-border freight with customs clearance | ready | parcel or freight + customs |
| LOG-WAREHOUSE | Storage, fulfilment-by-marketplace, inventory-as-a-service, value-added logistics (QC, kitting, labelling) | ready | warehouse-inventory |

Each spine supports a reverse branch where relevant.

---

## Branches

Branches are conditional sub-flows. They are not spine variants — they activate against an existing spine transaction when a specific condition is met. A transaction can have multiple branches active simultaneously.

### During-Transaction Branches

These attach between `select` and `on_confirm`. They handle decisions that shape the transaction before it is committed.

| Branch | Window | What it handles |
|---|---|---|
| ekyc | init → on_init | B2B identity verification at first transaction without an active FWA |
| fwa-activation | select → confirm | Transaction references an active Framework Agreement; rate card and policies inherited |
| payment-prepaid | init → on_confirm | Upfront payment; QRIS, VA, EWallet |
| payment-cod | init → on_status[DELIVERED] | COD collection at delivery |
| payment-credit | init → on_confirm | Credit terms payable post-delivery, per FWA |
| capacity-reservation | select → confirm | Parent contract reserves capacity; children stream in |

### Post-Confirm Branches — Fulfilment

These attach after `on_confirm` when the contract is live. They handle fulfilment-time events.

| Branch | Window | What it handles |
|---|---|---|
| weight-dispute | on_status[PICKED_UP] → on_status[DELIVERED] | LSP reweighs; diff proposed via /on_update |
| cold-chain-proof | on_status[PICKED_UP], on_status[DELIVERED] | Temperature reading captured at handoffs |
| attempt-ndr | on_status[OUT_FOR_DELIVERY] → on_status[DELIVERED] | Delivery attempt failed; buyer chooses action |
| attempt-reschedule | after ndr | Buyer picks new delivery window |
| attempt-address-change | after ndr | Buyer provides corrected address |
| attempt-self-pickup-conversion | after ndr | Buyer switches to agent-point pickup |
| attempt-auto-rto | after max attempts reached | Auto-RTO per re-attempt policy |
| customs-clearance | LOG-XB specific | Export, import, duty calculation, clearance events |
| customs-hold | LOG-XB specific | Customs flags shipment; resolution via /update |

### Exception Branches

| Branch | Window | What it handles |
|---|---|---|
| damage-claim | on_status[PICKED_UP] → contract_COMPLETE | Package damaged; claim filed via /update |
| loss-claim | after SLA breach threshold | Package not located; claim filed via /update |
| address-unserviceable | on_status[IN_TRANSIT] | Destination discovered unserviceable; resolution path |
| pickup-failed | pre-pickup | Seller not ready; policy-driven handling |

### Cancellation Branches

| Branch | Window | What it handles |
|---|---|---|
| cancel-buyer-prepickup | on_confirm → on_status[PICKED_UP] | Buyer cancels before pickup; free or low fee |
| cancel-seller | on_confirm → on_status[DISPATCHED] | Seller cancels; FWA-governed |
| cancel-intransit | on_status[PICKED_UP] → on_status[OUT_FOR_DELIVERY] | In-transit cancel; intercept logic |

### Reverse Branches

Reverse is not a separate spine. Each forward spine supports a reverse flavour via a branch that modifies its state machine.

| Branch | Parent spine | What it handles |
|---|---|---|
| reverse-simple | LOG-HYPERLOCAL | Origin-destination swapped; no QC; fast refund |
| reverse-with-qc | LOG-PARCEL | QC gating step before refund |
| reverse-freight | LOG-FREIGHT | Acceptance states; credit-note commercial |
| reverse-xb | LOG-XB | Dual customs legs (export from buyer country, import back) |
| inventory-release | LOG-WAREHOUSE | Spawns forward transport contract on another spine |

### Value-Added Service Branches (LOG-WAREHOUSE)

| Branch | Window | What it handles |
|---|---|---|
| vas-qc | storage | Quality control inspection per SKU |
| vas-kitting | storage | Kit assembly per instruction |
| vas-labelling | storage | Labelling, tagging, repackaging |
| vas-packaging | storage | Custom packaging |

### Cross-Cutting Branches

Available on all spines.

| Branch | What it handles |
|---|---|
| track | Enhanced real-time tracking beyond standard on_status |
| support | BAP↔BPP customer care channel |
| rating | Post-delivery rating of LSP, agent, and service |
| raise | Escalation to ION network when bilateral via /update fails |

---

## Framework Agreement (FWA)

Enterprise relationships in logistics use the FWA construct (see `policies/logistics-fwa/v1/`). When a transaction references an active FWA, rates, policies, payment terms, and SLAs are inherited from the FWA. `/select` becomes optional. The FWA is composed of pointers to ratified policies in the registry.

Parent-child transaction patterns (capacity reservations, milk runs, dispatch-from-FC, dedicated fleet) also use the FWA construct. The parent is a long-validity FWA; child transactions reference it and inherit scope and commercial terms.

---

## Disputes

Disputes flow through `/update` with the `reason` field referencing a ratified dispute policy IRI. The Contract state machine includes dispute states. Evidence is carried in the update payload. Escalation to `/raise` occurs when bilateral resolution exceeds the policy-defined SLA.
