# ION Payment Extension — Overview

All Indonesian payment method objects plus the `PaymentDeclaration` wrapper.

## PaymentDeclaration
The wrapper object binds a payment method to a transaction. It carries `method`, `collectedBy`, `timing`, `status`, `amount`, and `methodDetail` (the specific instrument object).

## Payment method objects
Each instrument type (QRIS, VirtualAccount, EWallet, etc.) is a separate schema object referenced via `methodDetail.oneOf`. This allows BAPs to render the correct payment UI and BPPs to route to the correct gateway.

## QRIS
Two types: STATIC (same QR for all transactions) and DYNAMIC (per-transaction QR with amount embedded). Dynamic QRIS has `expiresAt`. QRIS string is returned in on_init for BAP to render.

## BI settlement rails
BI_FAST: real-time, max IDR 250 million per transaction. RTGS: high-value same-day, unlimited. SKN: batch clearing for lower values. These are used for NP-to-NP settlement, not consumer-to-seller.
