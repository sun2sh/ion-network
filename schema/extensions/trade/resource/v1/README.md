# trade/resource/v1

Physical product attributes for all Trade sector categories.

## Attaches to
`beckn:Resource.resourceAttributes`

## Availability model
**Stock count is NEVER transmitted over the network.**
Publish availability signal only:
- `IN_STOCK` — adequate quantity
- `LOW_STOCK` — limited, BAP may show urgency
- `OUT_OF_STOCK` — not available
- `PREORDER` — available for pre-order
- `DISCONTINUED` — permanently removed

## Resource types
| Type | Use | Required fields |
|---|---|---|
| PLAIN | Single SKU, no choices | availability, images |
| VARIANT | One of several options of a parent | parentResourceId, variantGroup, isDefaultVariant |
| WITH_EXTRAS | Base + optional add-ons | customisationGroups |
| COMPOSED | Base + mandatory/optional groups | customisationGroups |

## Category-specific sub-objects
| Sub-object | Applicable to |
|---|---|
| food | Food & Beverage, Grocery |
| preparation | F&B, perishables |
| packaged | FMCG, grocery, pharma, cosmetics |
| regulatory | All regulated products |
| fashion | Apparel, accessories |
| electronics | Electronics, appliances |
| beauty | Cosmetics, personal care |
| agritech | Fresh produce, agricultural |
| pharmacy | Medicines, OTC |
| installation | Appliances, furniture |
| warranty | Electronics, durables |

## Regulatory
PerBPOM 31/2018 (packaged goods), UU 8/1999 (consumer protection), 
PerBPOM 23/2019 (cosmetics), PP 36/2023 (electronics warranty)
