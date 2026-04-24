# consideration/v1 — Logistics Consideration Attributes

Attaches to `beckn:Consideration.considerationAttributes`.

## What it covers

The financial structure of a logistics transaction — from the initial quote breakup through post-delivery adjustments, COD settlements, and final reconciliation.

## Breakup line types

Every charge in a logistics transaction must be expressed as a breakup line with a declared `titleType`. ION Central validates breakup consistency against offer attributes.

| titleType | When it appears | Notes |
|---|---|---|
| `FREIGHT_BASE` | Always | Core transport charge |
| `FUEL_SURCHARGE` | Always | Computed from `offer.fuelSurchargeFormula` |
| `COD_CHARGE` | When COD | Fee for cash collection service |
| `INSURANCE_PREMIUM` | When insurance requested | Per `offer.insurancePolicy` |
| `HANDLING_FEE` | Fragile, white-glove | Special handling surcharge |
| `COLD_CHAIN_PREMIUM` | Cold chain resources | Temperature-controlled transport premium |
| `HAZMAT_SURCHARGE` | Hazmat resources | DG handling fee |
| `REMOTE_AREA_SURCHARGE` | Outer island delivery | Remote pincode surcharge |
| `OVERSIZE_SURCHARGE` | Oversized cargo | Beyond standard max dimensions |
| `OVERWEIGHT_SURCHARGE` | Overweight cargo | Beyond standard max weight |
| `CUSTOMS_DUTY` | LOG-XB | Actual Bea Cukai duty assessed |
| `CUSTOMS_HANDLING_FEE` | LOG-XB | PPJK broker fee |
| `VALUE_ADDED_SERVICE_FEE` | LOG-WAREHOUSE | Aggregated VAS charges |
| `PICK_PACK_FEE` | LOG-WAREHOUSE | Per-unit pick and pack |
| `STORAGE_FEE` | LOG-WAREHOUSE | Periodic storage charge |
| `RE_ATTEMPT_FEE` | After first attempt | Per `offer.reAttemptPolicy` |
| `FAILED_PICKUP_FEE` | Consignor not ready | Per pickup-failed policy |
| `WEIGHT_DIFF_ADJUSTMENT` | Weight dispute resolved | Positive or negative delta |
| `CREDIT_NOTE` | Adjustment | Negative amount — reduces total |
| `DISCOUNT` | Promotional | Negative amount |
| `PPN_TAX` | All B2B, B2C over threshold | Indonesian VAT at the current applicable rate (e.g. 11% under PMK 131/2024) |
| `PPNBM_TAX` | Luxury goods | Luxury goods tax |

## PPN handling

PPN must be declared as a separate breakup line with `ppnRate` set to the current applicable rate (e.g. `0.11` under PMK 131/2024 — source from DJP, not hardcoded). Every `on_select` and `on_init` response carrying a PPN line must include `ppnRate` on that specific breakup entry.

```yaml
breakup:
  - titleType: FREIGHT_BASE
    amount: 45000
    currency: IDR
  - titleType: FUEL_SURCHARGE
    amount: 3600
    currency: IDR
  - titleType: PPN_TAX
    amount: 5346
    currency: IDR
    ppnRate: 0.11      # 11% applied to base + surcharge = 48600 * 0.11 = 5346
totalAmount: 53946
```

## COD settlement flow

```yaml
codAmountCollected: 500000        # Collected at delivery by rider
codCharge: 10000                  # Fee deducted by LSP
codRemittanceAmount: 490000       # Net remitted to BAP
codRemittanceBatchRef: "BATCH-20260428-001"
codRemittanceTimestamp: "2026-04-28T10:00:00Z"
codRemittanceMethod: BANK_TRANSFER
```

COD collected amounts appear in `on_status[DELIVERED]`. Remittance amounts appear in a separate `on_update` push from BPP when the remittance batch runs (per `offer.codPolicy` schedule — typically weekly).

## Cross-border duties

```yaml
dutyEstimate: 1500000             # Returned in /on_select — indicative
taxEstimate: 750000               # Returned in /on_select — indicative
actualDuty: 1620000               # Returned at IMPORT_CUSTOMS_CLEARED state — final
actualTax: 810000
```

Estimates are provided at `/on_select` for DDP incoterms. Actual amounts are declared when `IMPORT_CUSTOMS_CLEARED` state fires and flow into the final reconcile.

## Weight dispute adjustments

```yaml
revisedAmount: 68066              # BPP's proposed total after reweigh
revisionBreakup:
  - titleType: FREIGHT_BASE
    originalAmount: 45000
    revisedAmount: 57600          # 3.2kg actual vs 2.5kg declared
    diff: 12600
weightDiffAdjustment: 12600
```

When a weight discrepancy is raised, BPP sends `revisedAmount` and `revisionBreakup` in `/on_update`. If BAP accepts, the contract amount is updated and flows into reconcile. The `WEIGHT_DIFF_ADJUSTMENT` line appears in the final reconcile breakup.

## Reconciliation structure

At reconcile time, the full settlement history is consolidated:

```yaml
settlements:
  - settlementAttributes:
    reconId: "RECON-JNE-20260424-001"
    contractId: "jne-ord-20260422-001"
    settlementBasis: NET_AMOUNT
    settlementWindow: "2026-04-24T23:59:59Z"
    collectedBy: BAP
    amounts:
      baseContractAmount: 56721
      weightAdjustmentAmount: 12600   # Weight dispute resolved
      slaRebateAmount: 0              # On-time — no rebate
      codCollectedAmount: 0           # Prepaid order
      fwaVolumeRebate: 0              # Not yet at rebate threshold
    netSettlementAmount: 69321
    reconStatus: AGREED
```
