# ion-core/reconcile/v1

Inter-NP financial reconciliation between BAP (collector) and BPP (receiver).

## Attaches to
`beckn:Settlement.settlementAttributes`

## APIs
`reconcile` → `on_reconcile`

## Flow
1. BAP initiates `/reconcile` with contract amounts, finder fee, withholding, adjustments
2. BPP responds via `/on_reconcile` with `recon_status`: 01=AGREED, 02=OVERPAID, 03=UNDERPAID
3. If DISPUTED, either party raises a ticket via `raise/on_raise`

## Adjustments
Adjustments cover contract-level changes that must be agreed before settlement:
PRICE_ADJUSTMENT, CANCELLATION_FEE, RETURN_DEDUCTION, DAMAGE_PENALTY, COD_REMITTANCE, REFUND

## Relationship to ONDC RSF
reconcile/on_reconcile maps conceptually to ONDC RSF `recon/on_recon`.
The adjustment object is an ION addition — ONDC RSF does not define adjustment types at the protocol level.
