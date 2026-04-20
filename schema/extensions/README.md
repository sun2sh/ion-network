# ION Schema Extensions

Extensions are organised by scope. Core packs apply across every ION sector. Sector packs apply within a specific sector.

```
extensions/
  core/         ← Cross-sector — every ION sector uses these
  trade/        ← Trade sector (physical goods commerce) — Sector A
  mobility/     ← Mobility sector (transport, ride-hailing) — planned
  tourism/      ← Tourism sector (hospitality, experiences) — planned
  finance/      ← Finance sector (lending, insurance) — planned
  healthcare/   ← Healthcare sector (consultations, pharmacy) — planned
  logistics/    ← Logistics sector (B2B shipment, warehousing) — planned
```

## What an extension pack contains

Each pack is a folder with six files and two subdirectories:

```
{pack}/v1/
  attributes.yaml   ← OAS 3.1 schema — the source of truth for field definitions
  context.jsonld    ← JSON-LD context mapping fields to ion:, schema.org, beckn: namespaces
  vocab.jsonld      ← URI mappings for enum values
  profile.json      ← Attachment point declaration (which Beckn object this extends)
  renderer.json     ← Display hints for BAP rendering (label, accent colour)
  README.md         ← Summary — mandatory fields, attachment point, regulatory basis
  docs/             ← Narrative — design rationale, field-level guidance
  examples/         ← Concrete JSON payload examples
```

## How packs attach to Beckn objects

Beckn v2.0 defines an `{object}Attributes` extension point on every core object. ION packs populate these extension points. Multiple packs can attach to the same extension point simultaneously — they compose at the field level.

```
Provider.providerAttributes:
  ← core/identity/v1      NPWP, NIB, PKP status
  ← trade/provider/v1     storeStatus, operatingHours, providerCategory

Resource.resourceAttributes:
  ← core/localization/v1  name.id, shortDesc.id (language objects)
  ← core/product/v1       halalStatus, bpomRegNumber
  ← trade/resource/v1     resourceStructure, resourceTangibility, availability, category-specific fields

Consideration.considerationAttributes:
  ← core/tax/v1           ppnRate, taxCategory, eFakturRef
  ← trade/consideration/v1 breakupLineType, discountType

Settlement.settlementAttributes:
  ← core/payment/v1       PaymentDeclaration, QRIS, VirtualAccount, EWallet...
  ← core/reconcile/v1     reconId, amounts, adjustments, reconStatus
```

## OAS compliance

All `attributes.yaml` files are valid **OpenAPI 3.1** schemas. The `x-ion-*` vendor extensions (`x-ion-mandatory`, `x-ion-condition`, `x-ion-regulatory`) are explicitly permitted by the OAS specification and are used for ION-specific metadata only — they do not affect OAS validation.

## Adding a new sector

1. Create `extensions/{sector}/` with a `README.md` following the same pattern as `trade/README.md`
2. Identify which core packs apply (all sectors use at minimum: `localization`, `identity`, `address`, `payment`, `tax`)
3. Define sector-specific packs for entities unique to that sector
4. Add the sector to `schema/core/v2/api/v2.0.0/ion.yaml` under `x-ion-conformance.schemaPackMatrix`

## Pack versioning

Packs version independently. When a breaking change is needed, a new `v2/` directory is created alongside `v1/`. Old versions are retained for backwards compatibility. The `profile.json` in each version declares its own identifier.

## Searching schemas with Atlas

Before adding a field, search the Atlas registry to check if it already exists:

```bash
ion search "halal certification"     # finds core/product/v1 halalStatus
ion search "delivery agent phone"    # finds trade/performance/v1 agentPhone
ion validate myNewField              # clash detection before proposing
```

Atlas searches all ION and Beckn core schemas semantically — by meaning, not keyword. A new field that already exists under a different name will surface as a near-match.

Web Explorer: `devlabs.ion.id/atlas (coming soon)`
