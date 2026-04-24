# ion-logistics/participant-logistics/v1

Thin addendum to `core/participant/v1` carrying participant identity fields that apply only to logistics roles.

## Attaches to
`beckn:Participant.participantAttributes`

## Depends on
`core/participant/v1` — this addendum assumes the role taxonomy, identity fields, and addressDetail are already declared by the core participant pack.

## Fields
- `ppjkLicenceNumber` — PPJK customs-broker licence (required when `role=CUSTOMS_BROKER`)
- `driverLicenceNumber` — Indonesian SIM (required when `role=DRIVER`)
- `driverLicenceCategory` — SIM class (A, B_I, B_II, C, D)

## Why this exists as a separate pack

These three fields are strictly logistics-specific — trade, finance, tourism, healthcare have no need for PPJK customs licences or driver SIM categories. Keeping them out of `core/participant/v1` keeps the core pack tight and avoids forcing every sector to carry fields it doesn't use.

## How both blocks coexist on one participant

Beckn 2.0 allows `participantAttributes` to carry multiple JSON-LD typed blocks. Both the core participant block and this addendum attach to the same slot with distinct `@type` values and disjoint field sets. Implementations populating a DRIVER or CUSTOMS_BROKER participant will typically carry both blocks in the same payload.
