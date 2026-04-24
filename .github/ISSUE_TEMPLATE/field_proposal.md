---
name: Field Proposal
about: Propose a new field for an existing schema pack
labels: field-proposal
---

**Target pack**
e.g. `schema/extensions/trade/resource/v1`

**Field name** (camelCase)

**Type and format**

**Mandatory?**
always / conditional (state condition) / optional

**Regulatory basis** (if any)

**Use case**
Which commerce pattern or sector requires this field and why.

**Proposed attributes.yaml snippet**
```yaml
fieldName:
  type: string
  description: ...
  x-ion-mandatory: ...
  x-ion-regulatory: ...
```
