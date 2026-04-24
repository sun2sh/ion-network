# LOG-XB — Cross-Border Freight

Cross-border freight with customs clearance as a gating concern. Adds Bea Cukai (Indonesian customs) events as first-class state transitions.

## Applicable service types
International air cargo export/import, international ocean freight, cross-border e-commerce (when duty-paid). Covers DHL, FedEx, Maersk, Kuehne+Nagel, Samudera (international), and licensed freight forwarders with PPJK (Pengusaha Pengurusan Jasa Kepabeanan) capability.

## Delta from LOG-FREIGHT
- Customs clearance states in state machine (EXPORT_SUBMITTED, EXPORT_CLEARED, IMPORT_SUBMITTED, IMPORT_CLEARED, IMPORT_HELD, IMPORT_REJECTED)
- Customs broker (PPJK) as additional participant
- HS codes, commercial invoice, certificate of origin, packing list mandatory
- Import/export licences for regulated goods
- Incoterms (DDP, DAP, FOB, CIF, etc.) declared
- Origin and destination countries mandatory
- Duty and tax estimation at `/on_select`, actuals at customs clearance
- Customs hold and rejection are first-class terminal conditions

## Customs clearance branch states
| State | Meaning |
|---|---|
| EXPORT_CUSTOMS_SUBMITTED | Origin customs declaration filed |
| EXPORT_CUSTOMS_CLEARED | Origin clearance complete, vessel/aircraft can depart |
| IMPORT_CUSTOMS_SUBMITTED | Bea Cukai declaration filed |
| IMPORT_CUSTOMS_CLEARED | Clearance complete, cargo released |
| IMPORT_CUSTOMS_HELD | Flagged for documentation, inspection, or duty recalculation |
| IMPORT_CUSTOMS_REJECTED | Rejected — RTO, destroy-in-place, or re-export required |

## Reverse for cross-border
`reverse-xb` branch handles returns. Unlike domestic returns, reverse cross-border requires **two customs clearances** — export from the original destination country and import back to the original origin country. Practical economics often dictate destroy-in-place outcomes; the branch supports both paths.

## Available branches
- During-transaction: `ekyc`, `fwa-activation`, `capacity-reservation`, `payment-prepaid`, `payment-credit`
- Fulfilment: `customs-clearance`, `customs-hold`, `duty-dispute`, `weight-dispute`, `cold-chain-proof`, `damage-claim`, `loss-claim`
- Cancellation: window closes at export customs submission
- Reverse: `reverse-xb`
- Cross-cutting: `track`, `support`, `rating`, `raise`

## Key fields introduced
`countriesServed[]`, `customsBrokerageCapability`, `beaCukaiLicenceNumber`, `incotermsSupported[]`, `hsCodesServed[]`, `dutyAndTaxModel`, `estimatedClearanceDuration`, `commercialInvoice`, `certificateOfOrigin`, `packingList`, `importLicence`, `exportLicence`, `dutyEstimate`, `taxEstimate`, `actualDuty`, `actualTax`, `customsHoldReason`, `customsResolutionPath`, CUSTOMS_BROKER participant role.
