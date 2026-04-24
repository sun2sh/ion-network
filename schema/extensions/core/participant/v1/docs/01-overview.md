# Participant — Overview

The ION Participant pack extends Beckn 2.0's `Participant` with everything ION implementations need to describe the actors in a transaction — roles, identity, authorised signatories, and physical address detail.

## The role taxonomy

Beckn's own Participant schema is role-agnostic. ION declares an enum of 20 cross-sector roles. Not every role is valid in every sector — sector working groups narrow the enum at publish time via their sector's provider/offer/resource packs. The canonical cross-sector list:

- **Protocol roles**: BAP, BPP, PROVIDER
- **Commercial roles**: BUYER, SELLER, MERCHANT, AGENT
- **Financial roles**: BANK, UNDERWRITER, INSURANCE_BROKER
- **Logistics roles**: CONSIGNOR, CONSIGNEE, SHIPPER, NOTIFY_PARTY, FORWARDER, ACTUAL_CARRIER, DRIVER
- **Customs roles**: CUSTOMS_BROKER, CUSTOMS_AUTHORITY
- **Government roles**: GOVERNMENT_BUYER

## Identity fields — business vs individual

Indonesian compliance requires different identifiers for business participants (NPWP, NIB, PKP status) vs individuals (KTP for domestic, passport for foreign). The pack carries both sets; `x-ion-condition` annotations indicate when each is required.

For cross-border trade, `nik` (Nomor Identitas Kepabeanan — customs registration) is required on the relevant participants.

## Address hierarchy

Indonesian addresses go below the Beckn-native `Address.streetAddress/postalCode`:

```
Provinsi (34 provinces, BPS 2-digit)
  └─ Kabupaten / Kota (514 BPS 4-digit)
       └─ Kecamatan (BPS 7-digit)
            └─ Kelurahan / Desa (BPS 10-digit)
                 └─ RT / RW (neighbourhood detail)
                      └─ Patokan (landmark narrative)
```

For most trade patterns, provinsi + kabupaten + kecamatan + postalCode is enough. For rural delivery, RT/RW/patokan is essential — streets are often unnamed and numbers absent. For logistics, add `accessibility` (can a truck reach the address?) and `operatingHoursForDelivery`.

## Regulatory basis

- **PMK 112/2022** — 16-digit NPWP format (migration from 15-digit deadline June 2024)
- **Permendagri 72/2019** — BPS administrative codes
- **OJK** — UNDERWRITER and INSURANCE_BROKER licensing
- **UU 7/2021 HPP** — tax regime rules that cascade into participant PKP status
