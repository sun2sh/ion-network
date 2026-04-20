# ION Error Registry

Errors are organised by category. Each category owns a numeric range. The `registry.json` file is machine-generated from the category YAML files — never edit it directly.

## Numbering scheme

| Range | Category | File |
|---|---|---|
| ION-1xxx | Transport | transport.yaml |
| ION-2xxx | Catalog | catalog.yaml |
| ION-3xxx | Transaction | transaction.yaml |
| ION-4xxx | Fulfillment | fulfillment.yaml |
| ION-5xxx | Post-order | post-order.yaml |
| ION-6xxx | Settlement | settlement.yaml |
| ION-7xxx | Network | network.yaml |
| ION-8xxx | Schema | schema.yaml |
| ION-9xxx | System | system.yaml |

A developer receiving error `ION-5xxx` knows immediately it is a post-order error without looking it up.

## Error entry structure

Each entry in a category YAML file:

```yaml
- code: ION-3001
  http_status: 400
  category: transaction
  title:
    id: "Judul error dalam Bahasa Indonesia"
    en: "Error title in English"
  description:
    en: "Full description of what went wrong and why."
  affected_field: message.contract.commitments[]
  affected_apis:
    - select
  schema_ref: schema/extensions/trade/resource/v1
  flow_ref: flows/trade/spines/B2C-SF/v1
  resolution:
    en: "What the implementer should do to fix this."
```

## Adding a new error

1. Identify the correct category file for the error
2. Assign the next available code in that category's range
3. Add the entry to the category YAML file
4. Run `python errors/generate_registry.py` to regenerate `registry.json`
5. Submit a PR with both the YAML change and the regenerated registry

Do not hand-edit `registry.json`.

## Generating the registry

```bash
python errors/generate_registry.py
```

This reads all category YAML files and writes `errors/registry.json`.
