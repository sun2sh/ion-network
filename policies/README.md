# ION Policy Terms Registry

Machine-enforceable policy terms referenced by offer IRIs across the ION network.

## How it works

Sellers do not author policy prose. They declare policy IRIs on their offers; ION resolves each IRI to a structured terms document that defines exactly what the policy means and how it is enforced.

```
Seller's catalog entry:
  offerAttributes:
    returnPolicy:       ion://policy/return/standard/7d-sellerpays
    cancellationPolicy: ion://policy/cancel/prepacked/free
    warrantyPolicy:     ion://policy/warranty/standard/none
    disputePolicy:      ion://policy/dispute/consumer/bpsk
    grievanceSlaPolicy: ion://policy/grievance-sla/consumer/standard
    paymentTermsPolicy: ion://policy/payment-terms/upfront/full
```

Each IRI resolves to a terms document in this directory. BAP renders display text to the consumer; ION Central enforces the structured terms at each API boundary; reconcile applies penalty deductions per the linked penalty policy.

## Registry structure

```
policies/
  return/v1/                15 return policies
  cancellation/v1/          10 cancellation policies
  warranty/v1/              8 warranty policies
  dispute/v1/               5 dispute resolution policies
  grievance-sla/v1/         4 grievance SLA policies
  payment-terms/v1/         8 payment terms policies
  penalty/v1/               17 penalty policies (referenced by others)
  registry.json             generated aggregate index
  generate_registry.py      builds registry.json from per-file YAML
```

Total: **67 ratified policy documents**.

## Versioning

One version of the registry is canonical at any time. Council ratifies a new version with **90 days notice**. On the cutover date, every catalog auto-upgrades. Sellers receive notification at ratification time and may re-declare if they want different terms before the cutover.

We do not support per-seller version pinning. It does not scale to 100,000+ sellers.

## Validating an IRI

At catalog publish time, ION Central validates every policy IRI declared in the catalog:

- Unknown IRI → `ION-2010 INVALID_POLICY_IRI_AT_CATALOG_PUBLISH`
- Deprecated IRI → `ION-2011 POLICY_IRI_DEPRECATED` (with supersededBy guidance)

At runtime, actions that would violate the declared policy are rejected:

- Cancel outside `cancellationWindowCloses` → `ION-5001`
- Reason not in `returnReasonsAllowed` → `ION-5002`
- Return past `returnWindowDays` → `ION-5004`
- Action not permitted by declared policy → `ION-5008 POLICY_VIOLATION_ACTION_NOT_PERMITTED`

## Referenced penalty policies

Return / cancellation / grievance-SLA policies reference penalty IRIs. When a policy is violated, the linked penalty fires automatically at reconcile time. Sellers are onboarded into a **tier** (Standard / Mall / Premium) and cannot opt out of the tier's minimum penalty terms.

Penalty policies are the only category where sellers do not have free choice. Consumer protection compliance is non-negotiable.

## Seller custom addendum

Edge cases exist where a seller legitimately needs unique terms (e.g., watchmaker offering lifetime service). The `offerAttributes.customTermsAddendum` field (max 1000 chars) supplements the declared policy IRI. It may add terms but cannot contradict them. If the addendum contradicts the base policy, the base policy wins and the addendum is informational only.

## Searching the registry

```bash
ion search "return policy for fashion"
ion search "grievance SLA for flash sale"
ion search "penalty for seller late dispatch"
```

Atlas surfaces matching IRIs with their display text and applicability.

Web Explorer: `devlabs.ion.id/atlas/policies` (coming soon)
