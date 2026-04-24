# ION Logistics Branches

Branches are conditional sub-flows that attach to a spine's live transaction when a specific condition is met. They are not spine variants. Multiple branches can run concurrently on the same transaction.

## Branch families

| Family | Directory | Covers |
|---|---|---|
| eKYC | `ekyc/v1` | B2B KYC verification at first transaction without active FWA |
| Attempts | `attempts/v1` | NDR, reschedule, address change, self-pickup conversion, auto-RTO |
| Weight dispute | `weight-dispute/v1` | Reweigh at hub, diff negotiation, resolution |
| Customs | `customs/v1` | Export, import, clearance events, hold and rejection for LOG-XB |
| Cold chain | `cold-chain/v1` | Proof-of-condition at pickup and delivery, excursion alerts |
| COD | `cod/v1` | Collection at delivery, refusal, remittance |
| Exception | `exception/v1` | Damage, loss, address-unserviceable, pickup-failed |
| Reverse | `reverse/v1` | Per-spine reverse flavours — simple, with-qc, freight, xb, inventory-release |
| Cross-cutting | `cross-cutting/v1` | Track, status, support, rate, reconcile, raise |
| Value-added | `value-added/v1` | QC, kitting, labelling, packaging, returns-processing for LOG-WAREHOUSE |
| During-transaction | `during-transaction/v1` | Payment options, FWA activation, technical NACK handling |
| Cancellation | `cancellation/v1` | Buyer-prepickup, LSP-initiated, in-transit, TAT-breach |
| Incident | `incident/v1` | Accident, breakdown, robbery, medical, force-majeure, rider-refused |
| RTS handoff | `rts-handoff/v1` | Ready-to-Ship signal — seller-direct, warehouse-same-BPP, warehouse-cross-BPP |

## Branch structure
Each branch is defined with the same file structure as Trade branches:
```
branch-name/v1/
├── README.md          — description, applicable spines, windows, sub-branches
├── branch.yaml        — structured definition with sub-branches and API steps
├── docs/
├── examples/
└── profile.json
```

## How branches compose with spines
Each spine declares its `branchWindows` mapping branch name to earliest and latest valid states. Branches are looked up by name; the spine determines if activation is valid at a given moment. Branches can be composed — cold-chain-proof + weight-dispute + COD can all be active on the same transaction.

## How branches reference policies
Dispute-related branches (weight-dispute, damage, loss, exception, reverse) reference ratified policy IRIs for resolution rules. The branch defines the API exchange; the policy defines the outcome. This is consistent with the Trade spec's policy-IRI model.
