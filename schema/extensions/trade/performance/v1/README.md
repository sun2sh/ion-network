# trade/performance/v1

Fulfilment tracking attributes — agent details, AWB, SLA, handling, installation.

## Attaches to
`beckn:Performance.performanceAttributes`

## Performance modes
| Mode | Description |
|---|---|
| DELIVERY | Logistics delivers to buyer address |
| SELF_PICKUP | Buyer collects from seller location |
| DINE_IN | For restaurant orders consumed on premises |
| CURBSIDE | Buyer drives to pickup, seller brings to car |

## State machine reference
States are defined in `schema/extensions/trade/performance-states/v1/states.yaml`.
Do not redefine state codes in flow files — always reference the canonical states.

## SLA
SLA `unitBasis` options:
- `ORDER_CONFIRMATION` — countdown from when buyer confirms
- `SHIPMENT` — countdown from when package is dispatched
- `PAYMENT_RECEIPT` — countdown from payment confirmation

## Installation scheduling
`resource.installation` declares capability (does it need installation? does seller provide it?).
`performance.installationScheduling` carries the transaction-time appointment (scheduledDate, notes).
