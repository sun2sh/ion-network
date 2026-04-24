# RTS Handoff Branch

Ready-to-Ship (RTS) signal — the moment the consignor or warehouse has packed, labelled, and is ready for the rider to pick up the shipment. Covers three operational scenarios.

## Why this branch exists

Before this branch, the RTS transition was buried in the warehouse state machine. For operations teams, this left three real problems unsolved:

1. **B2C sellers** — who signals ready? When does the rider get dispatched?
2. **Integrated warehouse + LSP** (e.g. Pos Indonesia warehouse + Pos parcel) — how does the parent warehouse contract's completion trigger the child transport contract's READY_FOR_PICKUP?
3. **Cross-BPP warehouse + LSP** (e.g. TokoCabang warehouse + JNE transport) — the RTS signal originates at TokoCabang but the transport contract is owned by JNE. How does the signal cross BPP boundaries?

Each scenario has distinct evidence requirements and distinct failure modes. This branch covers all three.

## Three scenarios

### Scenario 1 — B2C / B2B seller direct
Seller packs and signals ready. Single contract, single BPP. Used by most e-commerce sellers shipping from their own warehouse.

### Scenario 2 — Warehouse-dispatched, same BPP
Integrated operator owns both the warehouse and the transport. No cross-BPP routing; BPP internally links parent warehouse state to child transport state.

### Scenario 3 — Warehouse-dispatched, cross-BPP
Warehouse BPP and transport BPP are different entities. RTS signal must route via ION Gateway.

```
TokoCabang BPP               ION Gateway                 JNE BPP (transport)
       │                         │                             │
       │ /on_status              │                             │
       │ [READY_FOR_PICKUP]     │                             │
       │ (on transport contract)│                             │
       ├────────────────────────►│                             │
       │                         │  Routed based on            │
       │                         │  dispatchOriginWarehouseBppId│
       │                         ├────────────────────────────►│
       │                         │                             │
       │                         │       /on_status            │
       │                         │       [READY_FOR_PICKUP]   │
       │                         │       to BAP               │
```

## Cross-BPP accountability

The `handoffEvidence` structure under `rtsNotificationRouting` records the exact moment each BPP confirmed its role in the handoff. When pickup fails because the warehouse said ready but the package wasn't actually out at the dock (or the transport system didn't receive the RTS), this evidence determines liability.

## Authorisation

ION Gateway only accepts cross-BPP RTS signals from warehouse BPPs that are pre-registered as dispatch origins for the transport BPP. This registration happens at FWA signing (for enterprise warehouse-LSP pairs) or via a separate dispatch-relationship registration in the ION Registry.

## Error codes
- `ION-LOG-6108` — RTS handoff timeout (transport BPP didn't acknowledge in PT15M)
- `ION-LOG-6109` — Unauthorised cross-BPP RTS
- `ION-LOG-6110` — Handoff evidence mismatch (transport BPP denies receipt)
