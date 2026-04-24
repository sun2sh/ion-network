# Value-Added Services Branch

Warehouse value-added services — QC, kitting, labelling, packaging.

## Applies to
LOG-WAREHOUSE exclusively.

## Activation
Services selected in `performance.valueAddedServicesSelected[]` at `/init`. Branch fires at the appropriate warehouse state machine trigger.

## Sub-branches
| Branch | Window | Output |
|---|---|---|
| `vas-qc` | INBOUND_RECEIVED → STORED | QC report per SKU; disposition for failed units |
| `vas-kitting` | STORED → DISPATCHED | Kitting completion report; new virtual SKU created |
| `vas-labelling` | STORED → DISPATCHED | Labelling completion with label type |
| `vas-packaging` | PICKING → PACKED | Packaging completion report |
