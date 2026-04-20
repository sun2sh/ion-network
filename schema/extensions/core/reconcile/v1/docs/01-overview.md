# ION Reconcile Extension — Overview

Inter-NP financial reconciliation between BAP (collector) and BPP (receiver).

## When reconciliation happens
After `on_status[DELIVERED]`. The BAP collected payment from the consumer. Now the BAP must settle the net amount to the BPP, minus finder fee and withholding.

## Withholding
A portion (`withholdingAmount`) is held back until the return window closes. This funds potential refunds. After return window expiry with no return, the withheld amount is released to BPP.

## Adjustments
Post-confirm changes that affect the final settlement: cancellation fees, return deductions, damage penalties, COD remittance, loyalty adjustments.

## ONDC RSF compatibility
`recon_status` uses the ONDC RSF numeric codes: `01` (AGREED), `02` (OVERPAID), `03` (UNDERPAID). This enables interoperability with platforms that implement the ONDC reconciliation framework.

## Dispute escalation
If `reconStatus = DISPUTED`, either party raises to ION via the `raise` channel. ION mediates.
