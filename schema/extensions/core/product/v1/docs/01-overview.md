# ION Product Certification Extension — Overview

Indonesian product certifications and regulatory compliance signals for all ION sectors.

## Halal status
`halalStatus` is mandatory for all food and beverage products. Four values:
- `HALAL`: MUI-certified. `halalCertNumber` required.
- `HALAL_PENDING`: in certification process.
- `NON_HALAL`: explicitly non-halal (pork, alcohol).
- `NOT_APPLICABLE`: non-food product.

## BPOM registrations
`bpomRegNumber` uses the BPOM registration format:
- `MD-XXXXXXXXXXXXXX`: domestically produced food/drug
- `ML-XXXXXXXXXXXXXX`: imported product

## Age restriction
`ageRestricted = true` requires `minAge`. Indonesia: 18 for tobacco and alcohol, 21 for certain controlled substances. BAP must verify age before allowing purchase.
