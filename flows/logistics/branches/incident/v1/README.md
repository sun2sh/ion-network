# Incident Branch

Driver/rider safety and in-transit incident reporting. Covers accidents, breakdowns, robbery, medical emergencies, force majeure, and rider-refused deliveries.

## Applies to
All spines with asset-operating carriage: LOG-HYPERLOCAL, LOG-PARCEL, LOG-FREIGHT, LOG-RORO, LOG-XB.

## Sub-branches
| Sub-branch | Trigger | Severity |
|---|---|---|
| `incident-accident` | Vehicle collision/rollover/fire/submersion | Minor to Critical |
| `incident-breakdown` | Mechanical/electrical/tire/fuel breakdown | Low |
| `incident-robbery` | Armed/unarmed robbery, theft, hijack | High — always |
| `incident-medical-emergency` | Driver medical event | Varies |
| `incident-force-majeure` | Flood, earthquake, civil unrest, pandemic | Varies |
| `rider-refused-delivery` | Rider refuses due to safety (distinct from NDR) | Low |

## Driver safety first
Every incident notification requires `driverSafetyStatus` populated within PT15M of the event. Cargo status becomes secondary until driver is confirmed safe.

## Insurance distinction
The spec carries two separate insurances:
- **Cargo insurance** — covers goods (insurance branch, liability policies)
- **Driver insurance** — covers driver/vehicle, accessible via incident branch. Referenced via `incidentDetail.insuranceClaimReference` separate from cargo claims.

## Automatic downstream branches
- `incident-robbery` → loss-claim branch fires for affected shipments
- `incident-accident` (SEVERE/CRITICAL) → may trigger loss-claim if cargo affected
- `incident-force-majeure` → SLA penalties waived per force majeure clause

## Error codes
- ION-LOG-7001 — Incident reported, resolution pending
- ION-LOG-7002 — Driver safety status not reported within policy window
- ION-LOG-7003 — Police report reference required but not provided
- ION-LOG-7004 — Force majeure declared, SLA waived
