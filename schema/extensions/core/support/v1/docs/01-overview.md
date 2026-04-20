# ION Support Extension — Overview

Consumer complaint ticket system. Buyer raises order issues to seller. Derived from ONDC IGM (Issue and Grievance Management) model.

## Two-phase flow
1. `context.try = true` — preview available support channels (get contact options without creating a ticket)
2. `context.try = false` — create formal complaint ticket with full issue object

## SLA tracking
ION Central tracks support ticket SLAs. Escalation path:
- Level 1: Interfacing NP (auto-resolution attempted)
- Level 2: GRO (Grievance Redressal Officer) of counterparty NP
- Level 3: ODR (Online Dispute Resolution) — external arbitration

## Relationship to raise/on_raise
`support` is buyer↔seller. `raise` is participant→ION network. If a seller fails to respond to support tickets, the BAP may raise to ION via the `raise` channel.
