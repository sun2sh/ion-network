# ION Identity Extension — Overview

Indonesian business KYC identifiers required for all ION network participants.

## Mandatory at onboarding
NPWP (16-digit, post-2024 format) and NIB are validated against DJP and OSS registries at provider onboarding. PKP status determines whether the seller can issue Faktur Pajak.

## Where each field attaches
- `providerAttributes`: identifies the seller entity at catalog publish time
- `contractAttributes`: identifies both buyer (NPWP/NIK) and seller at order confirm

## Individual sellers
`nikNumber` (16-digit e-KTP) required for `businessType = PERORANGAN` sellers. NPWP is still required — individuals registered for tax also hold an NPWP.
