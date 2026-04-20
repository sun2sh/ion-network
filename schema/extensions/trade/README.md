# ION Trade Extension Packs

Trade sector schema extensions. These packs apply to all Trade sector transactions — B2C, B2B, marketplace, subscription, cross-border, auction, and procurement. Trade covers all physical goods commerce on ION.

## Packs

| Pack | Attaches to | What it covers |
|---|---|---|
| `provider/v1` | `beckn:Provider.providerAttributes` | storeStatus, operatingHours, holidayCalendar, serviceabilityByCategory, averagePreparationTime, providerCategory, nibRegistered, invoicingModel |
| `resource/v1` | `beckn:Resource.resourceAttributes` | Full TradeResource — identity, physical, packaged goods, regulatory, food, fashion, electronics, beauty, agritech, installation, usage, warranty, availability, catalog structure (variants, customisation groups) |
| `offer/v1` | `beckn:Offer.offerAttributes` | cancellable, returnable, returnWindow, timeToShip, availableOnCod, return/cancellation policies, cancellation fee, self-pickup, MOQ, weight slabs |
| `consideration/v1` | `beckn:Consideration.considerationAttributes` | ppnRate, ppnbmRate, discountType, discountValue, breakup line types, promotion mechanics |
| `performance/v1` | `beckn:Performance.performanceAttributes` | readyToShip, awbNumber, agent details, trackingUrl, deliveryOtp, deliveryProof, SLA, handling, installationScheduling, performanceMode |
| `contract/v1` | `beckn:Contract.contractAttributes` | fulfillingLocationId, creditTermsDays, paymentDueDate, subscriptionBillingCycle, buyerInstructions, gift, deliveryPreferences, invoicePreferences, Faktur Pajak reference |
| `commitment/v1` | `beckn:Commitment.commitmentAttributes` | lineId, resourceId, offerId, quantity, price, customisationSelections, specialInstructions |
| `performance-states/v1` | (canonical enum, not a pack) | Standard, MTO, self-pickup, return, replacement, RTO state machines |

## Resource availability model

Stock count is NOT transmitted over the network. The BPP manages inventory internally. What the BPP publishes is an availability signal only:

```yaml
availability:
  status: IN_STOCK | LOW_STOCK | OUT_OF_STOCK | PREORDER | DISCONTINUED
  nextAvailableAt: date-time   # for PREORDER or restock
  maxOrderQty: integer          # per-order cap
  backorderAllowed: boolean
  preorderAllowed: boolean
  substitutionAllowed: boolean
```

## Category-specific attributes

Category-specific product attributes (food allergens, electronics specs, fashion sizing, beauty ingredients, agritech harvest details) are conditional fields within `resource/v1`. They are not separate category packs. The `resource/v1` README documents which fields apply to which product categories.
