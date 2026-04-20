# ION Raise Extension — Overview

Network-channel ticketing system. Participant (BAP or BPP) raises formal issues to ION network governance.

## Distinct from support
`support` = buyer complains to seller about their order.
`raise` = a network participant escalates to ION about network-level issues.

## When to use raise
- BPP persistently non-responsive to support tickets
- Force-cancel dispute (BAP claims BPP TAT breach; BPP disputes)
- Reconcile disagreement that could not be resolved bilaterally
- Policy violation by counterpart (catalog manipulation, fraudulent listings)
- Technical failure unresolved by bilateral support

## APIs
`raise`, `on_raise`, `raise_status`, `on_raise_status`, `raise_details`, `on_raise_details`

## Direction
Always participant → ION. Never BAP↔BPP. The counterparty NP is not directly involved — ION investigates and responds.
