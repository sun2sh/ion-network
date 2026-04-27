# ION Schema Style Guide

**Status: v0.5.2-draft**

This document specifies the conventions every ION schema pack MUST follow.
It is the contract between pack authors and ION's verifiers/tooling.

---

## 1. OAS compliance is non-negotiable

Every ION pack file is a standalone OpenAPI 3.1.1 document. It must:

- Start with `openapi: 3.1.1`
- Have an `info` block with `title` and `version`
- Define schemas under `components.schemas`
- Use only standard JSON Schema 2020-12 / OAS 3.1.1 keywords for validation logic
- Use `x-` prefixed extensions ONLY for documentation/tooling, never for required-field semantics

---

## 2. The four legal forms of `x-beckn-attaches-to`

Every ION schema that extends a Beckn type MUST carry an `x-beckn-attaches-to`
annotation. The annotation MUST match one of these four forms:

### Form 1 — Canonical single-level slot
```yaml
x-beckn-attaches-to: Offer.offerAttributes
x-beckn-attaches-to: Resource.resourceAttributes
x-beckn-attaches-to: Provider.providerAttributes
```
Use when the ION pack mounts directly onto a Beckn `*Attributes` slot. The
verifier checks that `Offer.offerAttributes` actually exists in `beckn.yaml`.

### Form 2 — Multi-level slot
```yaml
x-beckn-attaches-to: RatingInput.target.targetAttributes
```
Use when the slot is nested inside a Beckn object (e.g. `RatingInput.target` is
an inner object with its own `targetAttributes`).

### Form 3 — Array-of-Attributes slot
```yaml
x-beckn-attaches-to: Support.channels[*]
```
Use when a Beckn field is `array<Attributes>` and ION provides one of the
permitted entry types. Combine with `x-ion-discriminator` (see §4) so a
validator knows which entries match this pack.

### Form 4 — Off-Beckn or reusable shape (freeform, parenthesised)
```yaml
x-beckn-attaches-to: (off-Beckn — ION-only object, carried in /raise message body)
x-beckn-attaches-to: (reusable shape — embedded inside participantAttributes.addressDetail)
```
Use when the schema is intentionally not attached to a Beckn slot. The
parenthesis is the marker that says "do not try to validate this against
beckn.yaml." Annotation must start with `(`.

---

## 3. Required-field semantics

### 3.1 Unconditional requirements
Use the standard `required: [...]` array on the schema:

```yaml
IONBusinessIdentity:
  type: object
  properties:
    npwp: {type: string}
    nib:  {type: string}
  required: [npwp, nib]
```

DO NOT use `x-ion-mandatory: always` on individual properties. Standard
validators ignore it.

### 3.2 Conditional requirements (in-schema)
When the trigger field is on the same schema, use JSON Schema's `if/then/else`
inside an `allOf`:

```yaml
IONBusinessIdentity:
  properties:
    businessType: {enum: [PT, CV, UD, PERORANGAN]}
    nikNumber: {type: string}
  required: [businessType]
  allOf:
    - if:
        properties:
          businessType: {const: PERORANGAN}
        required: [businessType]
      then:
        required: [nikNumber]
```

### 3.3 Conditional requirements (cross-schema)
When the trigger field lives on a SIBLING pack that ends up in the same
Beckn `*Attributes` bag at runtime, JSON Schema cannot express the rule.
Mark the field with `x-ion-conditional-cross-schema: true` and add an entry
to `schema/core/v2/api/v2.0.0/ion-conditional-rules.yaml`:

```yaml
LogisticsParticipantAddendum:
  properties:
    driverLicenceNumber:
      type: string
      x-ion-conditional-cross-schema: true
      x-ion-condition: Required when role=DRIVER
```

A network-level validator (ONIX) enforces these at Attributes-bag composition
time.

### 3.4 Optional fields
Just declare the property; don't add any marker. Optional is the default.

---

## 4. Open Attributes posture and `x-ion-closed-extensions`

Every ION pack that attaches to a Beckn `*Attributes` slot MUST set:

```yaml
additionalProperties: true
x-ion-closed-extensions: false
```

Reason: Beckn's `Attributes` type is open by design (so participants can add
fields via NPOS). An ION pack that sets `additionalProperties: false` would
forbid additions Beckn's design explicitly permits.

The marker `x-ion-closed-extensions: false` is the explicit signal that NPOS
fields may be added under this schema's bag.

Internal helper types (e.g. `LocalisedText`, `AddressDetail`) that are nested
inside another schema and not directly attached to a Beckn slot keep
`additionalProperties: false`. They are not extension points.

---

## 5. allOf composition with `beckn:Attributes`

Every ION extension pack MUST formally compose with the Beckn `Attributes` base:

```yaml
IONBusinessIdentity:
  type: object
  additionalProperties: true
  x-beckn-attaches-to: Provider.providerAttributes
  properties: { ... }
  required: [...]
  allOf:
    - $ref: '<URL or path>/beckn.yaml#/components/schemas/Attributes'
    - if: ...
      then: ...
```

This makes every ION pack a typed subtype of `beckn:Attributes`, ensuring
`@context` and `@type` are always present (Beckn's `Attributes` requires them).

---

## 6. Discriminator for `@type`-keyed array entries

Where a pack attaches to a `Object.field[*]` array (e.g. `Support.channels[*]`),
declare a discriminator on the `@type` field:

```yaml
IONSupportTicket:
  x-beckn-attaches-to: Support.channels[*]
  x-jsonld:
    "@context": ./context.jsonld
    "@type": ion:SupportTicket
  x-ion-discriminator:
    propertyName: "@type"
    expectedValue: ion:SupportTicket
    doc: An array element matches this schema iff its @type equals expectedValue.
```

This formalises the identification mechanism instead of leaving it as narrative.

---

## 7. Documentation extensions

These `x-` extensions are reserved for documentation and have no validation
semantics. Use them freely:

| Extension | Purpose |
|---|---|
| `x-ion-regulatory` | Reference to Indonesian regulation (PMK, UU, PerBPOM, etc.) |
| `x-jsonld` | JSON-LD `@context` and `@type` for the schema |
| `x-ion-attach-mode` | Notes on non-standard attach patterns |

---

## 8. Forbidden patterns

The following are NOT permitted:

- `x-ion-mandatory: always` (use `required[]` instead)
- `x-ion-mandatory: optional` (just omit; that's the default)
- `x-ion-mandatory: conditional` without an `x-ion-condition` AND a corresponding
  `if/then/else` or rules-file entry
- `additionalProperties: false` on a schema that attaches to a Beckn `*Attributes` slot
- Inventing new top-level Beckn objects (always use `*Attributes` slots)
- `$ref` to a participant-controlled URL (security risk; only refs to `beckn.yaml`,
  `schema.ion.id`, and intra-pack are permitted)

---

## 9. Verifier

Run `python3 tools/verify_ion_yaml.py` to check structural compliance with
this style guide. It enforces:

- OAS envelope correctness
- $ref resolution (internal and to beckn.yaml)
- No `x-ion-mandatory` markers remain
- `required[]` only references declared properties
- `x-beckn-attaches-to` matches one of the four legal forms

Run `python3 tools/verify_ion_yaml_completeness.py` to check that no fields
were lost during a regeneration.

Run `python3 tools/verify_ion_inventory.py` to verify the per-pack files
agree with the composed `ion.yaml`.

---

*Last updated: v0.5.2-draft, 2026-04-27*
