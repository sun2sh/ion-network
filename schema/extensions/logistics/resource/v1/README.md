# resource/v1 — Logistics Resource Attributes

Attaches to `beckn:Resource.resourceAttributes`.

## What it covers

The thing being moved or stored. In logistics, this is the shipment object — its physical characteristics, regulatory declarations, special handling requirements, and spine-specific extensions for vehicles (Ro-Ro) and inventory (Warehouse).

## Service types

The `serviceType` field (always mandatory) determines which other fields apply:

| Value | Spine | What it is |
|---|---|---|
| `PARCEL` | LOG-PARCEL, LOG-HYPERLOCAL | Standard packaged shipment |
| `DOCUMENT` | LOG-PARCEL | Documents only — lighter regulatory requirements |
| `FREIGHT` | LOG-FREIGHT, LOG-XB | Bulk cargo requiring capacity booking |
| `VEHICLE` | LOG-RORO | Self-driven vehicle on ferry — vehicle IS the cargo |
| `INVENTORY` | LOG-WAREHOUSE | SKU inventory for storage and fulfilment |

## Physical characteristics (PARCEL and FREIGHT)

```yaml
weight:
  value: 2.5
  unit: kilogram         # gram | kilogram | tonne

dimensions:
  length: 30
  width: 20
  height: 15
  unit: centimeter       # centimeter | meter

declaredValue:
  amount: 500000
  currency: IDR          # For insurance and liability cap purposes
```

`weight` and `dimensions` are mandatory for LOG-PARCEL and LOG-FREIGHT. The BPP may reweigh at pickup or hub — if actual weight differs beyond the policy tolerance, the `weight-dispute` branch activates.

## Handling requirements

| Field | Type | Meaning |
|---|---|---|
| `fragile` | boolean | Requires careful handling; stacking restricted |
| `stackable` | boolean | Stacking allowed (default) |
| `hazmatClass` | string | IATA/IMO dangerous goods class (e.g. "Class 3") |
| `hazmatUnNumber` | string | UN number for DG identification |
| `temperatureRequirement.controlled` | boolean | Triggers cold-chain-proof branch when true |
| `temperatureRequirement.minTempC` | number | Minimum temperature (e.g. 2) |
| `temperatureRequirement.maxTempC` | number | Maximum temperature (e.g. 8) |
| `temperatureRequirement.category` | enum | FROZEN \| CHILLED \| AMBIENT \| CONTROLLED_ROOM |

When `temperatureRequirement.controlled = true`, the `cold-chain-proof` branch fires automatically at PICKED_UP and DELIVERED state events.

## Cross-border documents (LOG-XB — mandatory)

```yaml
hsCodes: ["8517.12.00", "8517.69.90"]   # HS codes per line item
commercialInvoice:
  invoiceNumber: "INV-2026-001"
  invoiceDate: "2026-04-22"
  invoiceValue: 15000000
  currency: IDR
certificateOfOrigin:
  certificateNumber: "COO-2026-001"
  issuingAuthority: "KADIN"
packingList:
  documentUrl: "https://..."
```

All four are mandatory for LOG-XB. Import/export licences are conditional based on product category (pharma, electronics with import restrictions, CITES-listed species).

## Vehicle details (LOG-RORO only)

```yaml
vehicleDetails:
  category: HEAVY_TRUCK    # PASSENGER_CAR | LIGHT_TRUCK | HEAVY_TRUCK | MOTORCYCLE | TRAILER | BUS
  make: Isuzu
  model: Giga FVZ
  lengthM: 12.5
  widthM: 2.5
  heightM: 4.0
  weightKg: 24000
vehicleRegistration: "B 1234 ABC"
```

The vehicle itself is the resource. Dimensions determine which vessel slot type is allocated. `vehicleRegistration` is mandatory for LOG-RORO.

## Inventory details (LOG-WAREHOUSE)

```yaml
skuCount: 3
storageCategory: HIGH_VALUE    # AMBIENT | CHILLED | FROZEN | HIGH_VALUE | HAZMAT | OVERSIZED
skuManifest:
  - skuId: "SKU-IPHONE-15-BLK-128"
    description: "iPhone 15 128GB Black"
    quantity: 500
    unitWeightKg: 0.17
    unitVolumeCbm: 0.001
    expiryDate: null
  - skuId: "SKU-SAMSUNG-S24-WHT-256"
    quantity: 250
```

`skuManifest` is mandatory at `/init` for LOG-WAREHOUSE. It governs what the warehouse operator receives, counts, and stores. Discrepancies between the manifest and actual received quantities trigger the `inbound-discrepancy` state.

## Cargo manifest (LOG-FREIGHT)

```yaml
cargoManifest:
  - lineId: "L1"
    description: "Consumer electronics — smartphones"
    quantity: 500
    unitWeight: 0.17
    hsCode: "8517.12.00"
cargoDescription: "500 units consumer electronics, fragile"
packagingType: CARTON    # CARTON | PALLET | CRATE | DRUM | BULK | ROLL
```

Required for all LOG-FREIGHT transactions. HS codes per line are mandatory for LOG-XB.

## Product category enum

Used for customs classification and compliance checks. Values: `GROCERY`, `FOOD_AND_BEVERAGE`, `FASHION`, `ELECTRONICS`, `BEAUTY`, `PHARMA`, `AGRITECH`, `INDUSTRIAL`, `AUTOMOTIVE`, `CHEMICALS`, `HAZMAT`, `HIGH_VALUE`, `DOCUMENTS`, `OTHER`.
