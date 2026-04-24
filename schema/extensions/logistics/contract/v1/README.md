# contract/v1 — Logistics Contract Attributes

Attaches to `beckn:Contract.contractAttributes`.

## What it covers

The confirmed terms of a logistics transaction. Everything that survives the lifecycle of the contract — from the FWA reference through billing identity, through the dispute lifecycle, through resolution — lives here.

## FWA and parent contract references

```yaml
fwaReference: "ion://policy/logistics-fwa/tokopedia-jne-2026q2"
parentContractReference: "tc-wh-20260422-001"
```

`fwaReference` links this transaction to a pre-negotiated Framework Agreement. When present, ION Central applies FWA rates and policies instead of offer-level defaults.

`parentContractReference` links this shipment to a parent contract — a warehouse contract that triggered this dispatch, or a capacity reservation that governs this freight booking.

## Billing identity

```yaml
npwp: "01.234.567.8-900.000"      # Tax ID — mandatory for B2B
nib: "1234567890123"              # Business registration — mandatory for B2B
invoicePreferences:
  fakturaRequired: true
  fakturaReference: "FK-2026-001"
  invoicingModel: INDIVIDUAL_PER_SHIPMENT  # or CONSOLIDATED_MONTHLY or FWA_SETTLEMENT
```

Indonesian tax law requires NPWP on B2B invoices. `fakturaRequired: true` triggers Faktur Pajak generation.

## Credit terms

```yaml
creditTermsDays: 30               # Payment due within 30 days
paymentDueDate: "2026-05-22"
```

Populated from the FWA `rateCard.paymentTerms` or from the offer's payment-terms policy. The `reconcile` step references these when computing the settlement.

## eKYC state

```yaml
ekycFormReference: "EKYC-JNE-2026-001"
ekycStatus: VERIFIED               # VERIFIED | PENDING_MANUAL_REVIEW | REJECTED
ekycVerificationTimestamp: "2026-04-22T09:30:00Z"
```

For B2B transactions without an active FWA. Status returned in `/on_init`. If `REJECTED`, transaction terminates at `/on_init`. If `PENDING_MANUAL_REVIEW`, BPP sends an unsolicited `/on_init` when resolved.

## Dispute state machine

Disputes are mutations on the contract. The `disputeState` field tracks where each dispute is:

```
DISPUTE_WEIGHT_RAISED
  → DISPUTE_EVIDENCE_EXCHANGED
  → DISPUTE_RESOLVED_ACCEPTED | DISPUTE_RESOLVED_NEGOTIATED | DISPUTE_ESCALATED

CLAIM_RAISED
  → CLAIM_UNDER_REVIEW
  → CLAIM_RESOLVED_ACCEPTED | CLAIM_RESOLVED_PARTIAL | CLAIM_REJECTED | CLAIM_ESCALATED
```

The `disputeReason.policyIri` field carries the applicable policy IRI that governs the dispute resolution.

## Claim lifecycle fields

```yaml
claimType: DAMAGE                 # WEIGHT_DISCREPANCY | DAMAGE | LOSS | SLA_BREACH | etc.
claimDetail:
  policyIri: "ion://policy/damage.standard.declared-value-cap"
  description: "Package arrived with cracked screen"
  claimedAmount: 500000
  evidenceUrls: ["https://..."]
  evidenceType: PHOTO
  reportedAt: "2026-04-23T09:00:00Z"
claimAssessment:
  outcome: PARTIAL                 # ACCEPTED | PARTIAL | REJECTED | PENDING_INSPECTION
  offeredSettlement: 400000
claimResolution:
  decision: ACCEPT_SETTLEMENT
```

All claims flow through `/update` carrying these fields. The contract is the evidence chain.

## Cold chain excursion

```yaml
excursionDetail:
  detectedAt: "2026-04-22T15:30:00Z"
  location: "In transit — Km 47 Pantura"
  measuredTemperature: 12.3
  declaredMin: 2
  declaredMax: 8
  excursionDurationMinutes: 47
excursionResolution:
  decision: HOLD_FOR_INSPECTION   # CONTINUE_AT_BUYER_RISK | HOLD_FOR_INSPECTION | CANCEL_AND_RETURN
```

Populated by the cold-chain branch when an in-transit excursion is detected.

## Reverse logistics fields

```yaml
returnReason:
  code: "DEFECTIVE"
  policyIri: "ion://policy/return.standard-7d-sellerpays"
returnItems:
  - resourceId: "SKU-001"
    quantity: 1
reverseContractReference: "jne-reverse-20260430-001"
```

Populated by the reverse branches. `reverseContractReference` links to the new reverse shipment contract.

## Cross-border fields

```yaml
incoterms: DDP                    # EXW | FCA | FOB | CIF | DAP | DDP
xbReturnDecision: RETURN_TO_ORIGIN  # RETURN_TO_ORIGIN | DESTROY_IN_PLACE | RE_EXPORT
```

Incoterms determine duty payment responsibility. XB return decision is made after customs rejection.
