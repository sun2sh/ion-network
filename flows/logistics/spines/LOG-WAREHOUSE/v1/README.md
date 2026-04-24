# LOG-WAREHOUSE — Warehousing and Fulfilment

Storage and fulfilment services. Fundamentally different from transport spines — the resource is inventory, the state machine is inventory lifecycle, and the commercial model is per-unit-per-time.

## Applicable service types
Bonded and non-bonded warehousing, fulfilment-by-marketplace (TokoCabang, Shopee SLS, Lazada LEX), local fulfilment centres, dark stores for quick commerce, cold storage, value-added logistics (QC, kitting, labelling, packaging).

## What makes this a distinct spine
- **Resource is inventory** — SKUs with quantities, not shipments in transit
- **No destination at booking** — destinations emerge later with fulfilment requests
- **Commercial model is time-based** — per-SKU-per-day, per-cbm-per-month, per-pallet-per-month
- **State machine is inventory lifecycle** — INBOUND_RECEIVED → STORED → PICKED → PACKED → DISPATCHED → INVENTORY_RELEASED
- **Dispatching spawns transport** — when inventory is dispatched, a new transport contract is created on LOG-HYPERLOCAL, LOG-PARCEL, or LOG-FREIGHT. The transport contract references the warehouse contract via `parentContractReference`

## Warehouse types
Bonded warehouse, non-bonded warehouse, cold storage, fulfilment centre, dark store, cross-dock facility.

## Available branches
- During-transaction: `fwa-activation` (enterprise FBA-style relationships)
- Storage lifecycle: `vas-qc`, `vas-kitting`, `vas-labelling`, `vas-packaging`
- Inventory movement: `inventory-release` (withdrawal spawns transport contract)
- Exception: damage in storage, shrinkage, inventory discrepancy
- Cross-cutting: `support`, `rating`, `raise`

## Value-added services
Covered as branches within this spine:
- `vas-qc` — quality control per inbound receipt or per SKU
- `vas-kitting` — kit assembly from multiple SKUs per instruction
- `vas-labelling` — labelling, tagging, repackaging before dispatch
- `vas-packaging` — custom packaging, gift wrap, branded inserts

## Key fields introduced
`warehouseLocations[]`, `warehouseType`, `bondedStatus`, `storageBillingUnit` (PER_SKU_PER_DAY, PER_CBM_PER_MONTH, PER_PALLET_PER_MONTH), `minimumStorageTerm`, `valueAddedServices[]`, `pickPackFee`, `fbaEquivalentModel`, `skuManifest[]`, `receivedQuantities[]`, `pickedSkus[]`, `inboundDiscrepancy`, `storageContractReference`, `transportContractReference`.

## Relationship to transport spines
When a fulfilment is requested, the warehouse creates a **new contract** on a transport spine. The relationship is:

```
Warehouse contract (LOG-WAREHOUSE) — long-lived parent
  └─ Transport contract #1 (LOG-PARCEL) — short-lived child
  └─ Transport contract #2 (LOG-HYPERLOCAL) — short-lived child
  └─ Transport contract #3 (LOG-FREIGHT) — short-lived child
```

Each transport contract references the warehouse contract via `contractAttributes.parentContractReference`. Settlement for pick/pack fees runs through the warehouse contract; transport settlement runs through the transport contract.
