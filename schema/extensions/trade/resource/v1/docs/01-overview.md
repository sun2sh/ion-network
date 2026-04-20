# Trade Resource Extension — Overview

Complete physical product attributes for all Trade sector categories. The most complex pack in ION — covers every product type from nasi goreng to smartphones to fresh mangoes.

## Availability signal (never stock count)
BPP manages actual inventory internally. What ION transmits is a signal only: `IN_STOCK`, `LOW_STOCK`, `OUT_OF_STOCK`, `PREORDER`, `DISCONTINUED`. BAPs must never request or display actual stock numbers.

## Resource types
Four structural types control how the product is presented and ordered:
- `PLAIN`: single SKU — just buy it
- `VARIANT`: one of a family (size M/L/XL pizza is a VARIANT of the base pizza)
- `WITH_EXTRAS`: base + optional add-ons (garlic bread + optional extra cheese)
- `COMPOSED`: base + mandatory/optional customisation groups (build-your-own pizza)

## Category sub-objects
Each product category uses a specific sub-object: `food`, `preparation`, `packaged`, `regulatory`, `fashion`, `electronics`, `beauty`, `agritech`, `pharmacy`, `installation`, `warranty`. These are conditional — only include the sub-object relevant to the product category.

## Regulatory declarations
Food: nutritionalInfo, allergens, BPOM registration. Electronics: energy rating, warranty minimum P1Y. Fashion: fabric composition per SNI 0055. All products: countryOfOrigin ISO alpha-3.
