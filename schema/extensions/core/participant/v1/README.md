# ion-core/participant/v1

Cross-sector participant role taxonomy and identity fields.

## Attaches to
`beckn:Participant.participantAttributes`

## What it covers
- **Role taxonomy** — 20 roles spanning trade (BUYER, SELLER, MERCHANT), logistics (CONSIGNOR, CONSIGNEE, SHIPPER, FORWARDER, CARRIER, DRIVER), financial (BANK, UNDERWRITER, INSURANCE_BROKER), customs (CUSTOMS_BROKER, CUSTOMS_AUTHORITY), and government (GOVERNMENT_BUYER). Sector working groups may narrow this enum at publish time.
- **Indonesian business identity** — NPWP (16-digit 2024 format), NIB, NIK (customs), PKP status
- **Individual identity** — KTP, passport (for foreign participants)
- **Role-specific IDs** — bankCode, insurerLicenceNumber
- **Authorised signatory** — for B2B contracts
- **Address hierarchy** — provinsi → kabupaten → kecamatan → kelurahan → RT/RW, with patokan landmarks, areaType, 3T remote classification, and accessibility metadata (motorcycle/truck/boat reachability, road condition)

## Why this lives in core, not a sector pack
Every ION sector has participants with roles, tax IDs, and physical addresses. Trade (B2C, B2B, XB, B2G), logistics, future mobility and finance all need the same taxonomy. Keeping it cross-sector prevents each sector from re-defining the same fields with slightly different shapes.

## Sector-specific addenda
Logistics has its own thin addendum for licence fields that only apply to logistics roles (PPJK customs broker licence, driver SIM category): `schema/extensions/logistics/participant-logistics/v1/`.

## History
New in v0.5.2. Consolidated from `schema/extensions/logistics/participant/v1/` in `ion-logistics` (logistics-specific licence fields split out into the addendum pack above).

## Why address-detail lives here, not in `core/address/v1`
Beckn 2.0's `Address` schema is closed (`additionalProperties: false`) and has no `addressAttributes` slot. ION-extended address fields therefore attach via participant attributes. `core/address/v1` exists and defines subdivision fields, but they mount on `Address` via `ionAddressAttributes`, which Beckn 2.0.0 supports as an out-of-band extension; `participant.addressDetail` is the full-fidelity alternative where you need per-participant address context (delivery preferences, accessibility, operating hours).
