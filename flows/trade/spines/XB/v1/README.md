# Cross-Border Export (XB)

Indonesian seller exports to international buyer. Requires bilingual catalog, HS codes, and customs documentation.

## Applicable categories
Agritech (coffee, cocoa, palm oil, spices), Fashion (batik, garments), Handicraft, Electronics re-export


## Performance state machine
`performance-states/v1/states.yaml#standard`
Plus additional XB states: CUSTOMS_CLEARED_EXPORT, IN_TRANSIT_INTERNATIONAL, CUSTOMS_CLEARED_IMPORT.

## Key differences from B2C-SF
- `name.en` and `shortDesc.en` **mandatory** (unlike domestic where en is optional)
- `packaged.hsnCode` required for all items
- `countryOfOrigin` required (already in resource/v1)
- `logisticsServiceType`: INTERNATIONAL_AIR or INTERNATIONAL_OCEAN
- Incoterms declared at on_select: FOB, CIF, EXW, DAP, DDP
- `beaCukaiReference` in contractAttributes at on_confirm
- `peb_reference` (Pemberitahuan Ekspor Barang) — Bea Cukai export declaration
- Payment: SWIFT or Letter of Credit for international; IDR settlement for domestic leg
- Documents: Commercial Invoice, Packing List, PEB, Certificate of Origin, Phytosanitary Cert
