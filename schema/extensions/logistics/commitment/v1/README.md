# commitment/v1 — Logistics Commitment Attributes

Attaches to `beckn:Commitment.commitmentAttributes`.

## What it covers

Line-level details within a logistics transaction. Each commitment line represents one discrete unit being committed — a package, a cargo line, a container, a SKU stock unit, or a vehicle slot. The commitment is the "what" of the contract; performance is the "how it went."

## Spine-specific usage

### LOG-PARCEL and LOG-HYPERLOCAL (package-level)

```yaml
commitmentAttributes:
  lineId: "L1"
  resourceId: "jne-parcel-service"
  offerId: "jne-yes-nextday"
  packageCount: 1
  totalWeight:
    value: 2.5
    unit: kilogram
  specialInstructions: "Do not stack. Fragile — handle with care."
```

Most parcel transactions have a single commitment line. Multi-box orders have multiple lines with separate package counts.

### LOG-FREIGHT (cargo manifest level)

```yaml
commitmentAttributes:
  lineId: "L1"
  resourceId: "samudera-fcl-service"
  offerId: "samudera-fcl-java-sulawesi"
  totalWeight:
    value: 18500
    unit: kilogram
  totalVolume:
    value: 24.5
    unit: cbm
  containerReference: "SAMU1234567"   # FCL — specific container
  sealNumber: "SL987654"
  capacityUnits: 1
  capacityUnitType: container
  requestedDepartureDate: "2026-04-25"
```

Freight commitments carry cargo-level manifest detail. For FCL, the container reference is the booking unit. For LTL, multiple commitment lines share the same carrier's space.

### LOG-RORO (vehicle slot)

```yaml
commitmentAttributes:
  lineId: "L1"
  resourceId: "asdp-roro-service"
  offerId: "asdp-ketapang-gilimanuk-heavy-truck"
  vehicleRegistration: "B 1234 ABC"
  capacityUnits: 1
  capacityUnitType: vessel_slot
  requestedDepartureDate: "2026-04-22"
```

One vehicle = one commitment line. Vehicle registration cross-references the `resource.vehicleRegistration` field.

### LOG-WAREHOUSE (SKU level)

```yaml
commitmentAttributes:
  lineId: "L1"
  skuId: "GMI-SKU-IPHONE-15-BLK-128"
  quantity: 500
  lotNumber: "LOT-2026-Q2-001"
  expiryDate: null
```

Each distinct SKU is a separate commitment line. Lot numbers and expiry dates are mandatory for pharma and food items.

### Child transactions referencing parent

```yaml
commitmentAttributes:
  lineId: "L1"
  parentCommitmentId: "wh-cmt-001"    # Reference to warehouse contract commitment
```

When LOG-WAREHOUSE spawns a LOG-PARCEL dispatch, the transport commitment references the parent warehouse commitment via `parentCommitmentId`.

## specialInstructions

Free-text handling instructions carried at the commitment line level. These appear on the shipping label and are visible to the rider/driver:

- "Do not stack — fragile item below"
- "Keep upright at all times"
- "Refrigerate immediately on receipt"
- "Signature required — do not leave unattended"
- "Government procurement — requires official receipt"

## Multiple commitment lines

A single contract may carry multiple commitment lines when:
- An order has boxes going to different zones (different rates per line)
- A freight booking covers multiple cargo types
- A warehouse inbound covers multiple SKUs
- A dispatch request covers partial inventory (specific SKUs from stored pool)
