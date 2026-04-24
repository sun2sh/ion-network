# LOG-WAREHOUSE — Developer Orientation

## What this spine is for

You are building a warehousing or fulfilment integration — either as a warehouse operator (BPP) offering storage, pick-pack, and value-added services, or as a BAP (merchant, marketplace) storing inventory and requesting fulfilment.

LOG-WAREHOUSE is fundamentally different from transport spines. **The resource is inventory (SKUs with quantities), not a shipment in transit. The state machine is an inventory lifecycle. The commercial model is per-SKU-per-day or per-cbm-per-month, not per-shipment.** Dispatching inventory triggers a new transport contract on LOG-PARCEL, LOG-HYPERLOCAL, or LOG-FREIGHT — it does not happen within this spine.

## Common use cases covered

- **FBA-style fulfilment** (TokoCabang, Shopee SLS, Lazada LEX): marketplace operates warehouses; merchants store inventory; orders trigger pick-pack-dispatch cycles
- **3PL storage and distribution**: third-party warehouse stores merchant inventory; merchant requests batch dispatches
- **Dark stores for quick commerce**: small urban warehouse pre-positioned for hyperlocal instant delivery
- **Cold storage**: pharma, fresh food, frozen goods with temperature-controlled storage
- **Bonded warehousing**: goods stored before customs clearance (cross-border use case)

## As a BPP (warehouse operator)

**Catalog** declares: warehouse locations with type (BONDED, NON_BONDED, COLD_STORAGE, FULFILMENT_CENTRE, DARK_STORE), total capacity, cold chain capability, bonded status, value-added services offered (QC, KITTING, LABELLING, PACKAGING), and billing unit (PER_SKU_PER_DAY, PER_CBM_PER_MONTH, PER_PALLET_PER_MONTH).

**At /on_confirm**: Return storage contract reference, allocated warehouse location and capacity, and inbound instructions.

**Inventory lifecycle**: When merchant sends inventory, push INBOUND_RECEIVED with actual received quantities. When merchant requests fulfilment (via `/update`), run PICKING → PACKED → DISPATCHED. At DISPATCHED, create a new transport contract (LOG-PARCEL or LOG-HYPERLOCAL) and return `transportContractReference`.

## As a BAP (merchant or marketplace)

Subscribe to warehouse catalogs. FWA-governed for most enterprise relationships (Tokopedia, Shopee, Amazon Indonesia).

At `/init`, declare your SKU manifest, select value-added services, and provide expected receipt date.

After `/on_confirm`, send inventory to the warehouse per `inboundInstructions`. Watch for INBOUND_RECEIVED `on_status` with actual received quantities vs expected — discrepancies are flagged.

To dispatch inventory to a buyer, send `/update` with `inventoryReleaseRequest` specifying which SKUs, quantities, and destination. The warehouse creates a transport contract and returns `transportContractReference`. Track the delivery on the transport spine, not here.

## Value-added services

Select via `valueAddedServicesSelected` at `/init`. Each service is a branch:
- **QC** (`vas-qc`): inspects inbound goods; your instructions define pass/fail criteria
- **Kitting** (`vas-kitting`): assembles kits from multiple SKUs per a bill-of-materials you provide
- **Labelling** (`vas-labelling`): applies product labels, price tags, compliance labels (BPOM, Halal)
- **Packaging** (`vas-packaging`): custom packaging, branded boxes, gift wrap

## FIFO inventory management

If you need FIFO rotation (oldest stock ships first), declare this in the `/init` manifest. Warehouse operator enforces FIFO in the pick sequence. Not a protocol-level feature — it's an instruction carried in `specialInstructions` on the commitment.

## Beckn 2.0 endpoints used

```
/catalog/publish → /catalog/on_publish
/select → /on_select           (storage capacity quote)
/init → /on_init               (SKU manifest, VAS selection, expected receipt date)
/confirm → /on_confirm         (storage contract, warehouse location, inbound instructions)
/on_status (inventory lifecycle — INBOUND_RECEIVED, STORED, DISPATCHED, etc.)
/update → /on_update           (fulfilment requests, inventory release)
/reconcile → /on_reconcile     (monthly storage fee settlement)
/raise → ...                   (inventory discrepancy escalation)
/support → /on_support
```

## Transport contract relationship

When inventory is dispatched (DISPATCHED state), a new contract is created on LOG-PARCEL, LOG-HYPERLOCAL, or LOG-FREIGHT. The transport contract carries `parentContractReference` pointing to this warehouse contract. Settlement for pick/pack and VAS fees runs through the warehouse contract; freight charges run through the transport contract.

```
LOG-WAREHOUSE contract (long-lived: weeks to months)
  └─ Transport contract (short-lived: 1-3 days)
  └─ Transport contract (short-lived: 1-3 days)
  └─ Transport contract (short-lived: 1-3 days)
```
