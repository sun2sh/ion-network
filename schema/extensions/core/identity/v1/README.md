# ion-core/identity/v1

Indonesian business KYC identifiers and licensing.

## Attaches to
`beckn:Provider.providerAttributes` and `beckn:Contract.contractAttributes`

## Fields
| Field | Type | Mandatory | Description |
|---|---|---|---|
| npwp | string(16) | always | Tax ID — Nomor Pokok Wajib Pajak |
| nib | string(13) | always | Business registration — Nomor Induk Berusaha |
| nikNumber | string(16) | conditional | National ID — for individual sellers |
| pkpStatus | enum | always | VAT registration: PKP or NON_PKP |
| legalEntityName | string | always | Registered business name |
| businessType | enum | always | PT/CV/UD/PERORANGAN etc. |
| siupNumber | string | optional | Trade license (legacy, being replaced by NIB) |
| spPIRTNumber | string | optional | Small-scale food production license |

## Regulatory
PMK 136/2023, PP 5/2021, UU 24/2013
