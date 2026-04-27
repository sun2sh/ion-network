# Conditional review worksheet

**Total: 230 fields awaiting review.**

Instructions for reviewers:

- For each field, decide whether the rule is `IN-SCHEMA` (trigger field is on the same schema) or `CROSS-SCHEMA` (trigger lives elsewhere).
- Write the rule as `field_name=VALUE` (e.g. `businessType=PERORANGAN`).
- For cross-schema, also fill in `proposed_target_schema` (the schema that owns the trigger field).
- If the field should actually be unconditionally required, write `ALWAYS`.
- If the field is fully optional and the marker should be removed, write `NEVER`.
- Edit the CSV (`conditional_review_worksheet.csv`); after edits, re-run `tools/fix_residuals.py` and the script will convert IN-SCHEMA rules to standard `if/then/else` automatically.


## `core/address` — 2 field(s)

| Schema | Field | Current text |
|---|---|---|
| `IONAddressSubdivisions` | `kecamatan` | Required for delivery addresses |
| `IONAddressSubdivisions` | `kelurahan` | Required for delivery addresses |

## `core/participant` — 9 field(s)

| Schema | Field | Current text |
|---|---|---|
| `IONParticipantAttributes` | `addressDetail` | *(empty — TODO)* |
| `IONParticipantAttributes` | `authorisedSignatory` | Required for B2B contracts over materiality threshold |
| `IONParticipantAttributes` | `ktpNumber` | Required for DRIVER role; optional for consignee verification |
| `IONParticipantAttributes` | `nib` | Required for all seller/provider/merchant participants |
| `IONParticipantAttributes` | `nik` | Required for cross-border trade (Nomor Identitas Kepabeanan — customs registr... |
| `IONParticipantAttributes` | `npwp` | Required when participant is a business (PKP or non-PKP) and NPWP is available |
| `IONParticipantAttributes` | `passportNumber` | Required for foreign consignees/shippers in cross-border patterns |
| `IONParticipantAttributes` | `pkpStatus` | *(empty — TODO)* |
| `IONParticipantAttributes` | `subscriberId` | Required when the participant is itself an ION-registered subscriber |

## `core/payment` — 8 field(s)

| Schema | Field | Current text |
|---|---|---|
| `CashOnDelivery` | `collectionAmountCollected` | Required after handover — actual amount collected |
| `CashOnDelivery` | `collectionTimestamp` | Required after handover |
| `CashOnDelivery` | `partialCollectionReason` | Required when collectionAmountCollected < collectionAmount |
| `PaymentDeclaration` | `amount` | Required when payment is confirmed |
| `PaymentDeclaration` | `gatewayRef` | Required when payment gateway is used |
| `PaymentDeclaration` | `methodDetail` | Required when method requires instrument-specific fields |
| `PaymentDeclaration` | `paidAt` | Required after payment is confirmed |
| `QRIS` | `qrisString` | Required for DYNAMIC QRIS returned at on_init |

## `core/product` — 1 field(s)

| Schema | Field | Current text |
|---|---|---|
| `IONProductCertifications` | `minAge` | Required when ageRestricted is true |

## `core/raise` — 2 field(s)

| Schema | Field | Current text |
|---|---|---|
| `IONTicket` | `assignedTo` | Required when ticket is assigned to counterparty or ION |
| `IONTicket` | `contractId` | Required for transaction-specific tickets |

## `core/reconcile` — 8 field(s)

| Schema | Field | Current text |
|---|---|---|
| `IONReconcileAttributes` | `adjustmentReason` | Required when adjustmentType is present |
| `IONReconcileAttributes` | `adjustmentType` | Required when parentReconId is present |
| `IONReconcileAttributes` | `affiliateCommissionAmount` | Required when contract.liveCommerceContext.sourceChannel=AFFILIATE_LINK |
| `IONReconcileAttributes` | `codRemittance` | Required when one or more settlements in this reconcile carry method=COD |
| `IONReconcileAttributes` | `parentReconId` | Required when adjustmentType is present |
| `IONReconcileAttributes` | `recon_status` | Set by on_reconcile from BPP/receiver |
| `IONReconcileAttributes` | `streamerCommissionAmount` | Required when contract was placed via live/social commerce |
| `IONReconcileAttributes` | `taxWithholdings` | Required when seller is Mall-tier or above, or when PPN PMSE applies |

## `core/support` — 1 field(s)

| Schema | Field | Current text |
|---|---|---|
| `IONSupportTicket` | `escalationTimestamp` | Required when escalationLevel changes |

## `core/tax` — 3 field(s)

| Schema | Field | Current text |
|---|---|---|
| `IONTaxDetail` | `taxAmount` | Required when taxRegime is not EXEMPT |
| `IONTaxDetail` | `taxBaseAmount` | Required for proper tax computation trail |
| `IONTaxDetail` | `taxRate` | Required when taxRegime is not EXEMPT |

## `logistics/consideration` — 2 field(s)

| Schema | Field | Current text |
|---|---|---|
| `LogisticsConsiderationAttributes` | `ppnAmount` | *(empty — TODO)* |
| `LogisticsConsiderationAttributes` | `ppnRate` | *(empty — TODO)* |

## `logistics/contract` — 11 field(s)

| Schema | Field | Current text |
|---|---|---|
| `LogisticsContractAttributes` | `aseanSingleWindowReference` | *(empty — TODO)* |
| `LogisticsContractAttributes` | `beaCukaiDeclaration` | *(empty — TODO)* |
| `LogisticsContractAttributes` | `cargoInsurance` | *(empty — TODO)* |
| `LogisticsContractAttributes` | `fumigationCertificate` | *(empty — TODO)* |
| `LogisticsContractAttributes` | `inatradePermits` | *(empty — TODO)* |
| `LogisticsContractAttributes` | `incotermsNamedPlace` | *(empty — TODO)* |
| `LogisticsContractAttributes` | `lartasClassification` | *(empty — TODO)* |
| `LogisticsContractAttributes` | `phytosanitaryCertificate` | *(empty — TODO)* |
| `LogisticsContractAttributes` | `ppnExemption` | *(empty — TODO)* |
| `LogisticsContractAttributes` | `stampDuty` | *(empty — TODO)* |
| `LogisticsContractAttributes` | `withholdingTax` | *(empty — TODO)* |

## `logistics/offer` — 38 field(s)

| Schema | Field | Current text |
|---|---|---|
| `LogisticsOfferAttributes` | `agentAssignmentModel` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `awbAllocationModel` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `bulkPickupMaxShipments` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `capacityModel` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `chargeableWeightRule` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `codBuyerDailyLimit` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `codDenominationsAccepted` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `codHoldPeriodDays` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `codPolicy` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `codReconciliationVariance` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `codShipmentLimit` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `consolidationType` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `crossingDuration` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `cutoffs` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `dropOffLocationsUrl` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `dutyAndTaxModel` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `equipmentType` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `incotermsSupported` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `labelFormatsSupported` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `liveTrackingEnabled` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `maxBulkBatchSize` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `maxCodAmount` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `maxDeliveryRadiusKm` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `minimumChargeableAmount` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `minimumStorageTerm` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `overallTatCommitment` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `pickupModels` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `pickupWindowGranularityMinutes` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `rateModifiers` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `routingTopology` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `sailingSchedule` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `sameDayPickupCutoffTime` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `scheduleType` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `slotGranularityMinutes` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `slotWindowsOffered` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `stateTimingCommitments` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `storageBillingUnit` | *(empty — TODO)* |
| `LogisticsOfferAttributes` | `vehicleCategoriesAccepted` | *(empty — TODO)* |

## `logistics/participant-logistics` — 3 field(s)

| Schema | Field | Current text |
|---|---|---|
| `LogisticsParticipantAddendum` | `driverLicenceCategory` | Required when role=DRIVER |
| `LogisticsParticipantAddendum` | `driverLicenceNumber` | Required when role=DRIVER (LOG-RORO, LOG-FREIGHT, LOG-HYPERLOCAL) |
| `LogisticsParticipantAddendum` | `ppjkLicenceNumber` | Required when role=CUSTOMS_BROKER |

## `logistics/performance` — 34 field(s)

| Schema | Field | Current text |
|---|---|---|
| `LogisticsPerformanceAttributes` | `appliedCutoffs` | *(empty — TODO)* |
| `LogisticsPerformanceAttributes` | `awbAllocationMode` | *(empty — TODO)* |
| `LogisticsPerformanceAttributes` | `awbNumber` | *(empty — TODO)* |
| `LogisticsPerformanceAttributes` | `billOfLadingReference` | *(empty — TODO)* |
| `LogisticsPerformanceAttributes` | `bookingReference` | *(empty — TODO)* |
| `LogisticsPerformanceAttributes` | `confirmedPickupDate` | *(empty — TODO)* |
| `LogisticsPerformanceAttributes` | `confirmedPickupWindow` | *(empty — TODO)* |
| `LogisticsPerformanceAttributes` | `currentStateTimingStatus` | *(empty — TODO)* |
| `LogisticsPerformanceAttributes` | `deliveryOtp` | *(empty — TODO)* |
| `LogisticsPerformanceAttributes` | `dispatchOriginWarehouseBppId` | *(empty — TODO)* |
| `LogisticsPerformanceAttributes` | `legs` | *(empty — TODO)* |
| `LogisticsPerformanceAttributes` | `parentWarehouseCommitmentRefs` | *(empty — TODO)* |
| `LogisticsPerformanceAttributes` | `parentWarehouseContractRef` | *(empty — TODO)* |
| `LogisticsPerformanceAttributes` | `pickupAgentPointId` | *(empty — TODO)* |
| `LogisticsPerformanceAttributes` | `pickupBatchId` | *(empty — TODO)* |
| `LogisticsPerformanceAttributes` | `pickupBatchShipmentCount` | *(empty — TODO)* |
| `LogisticsPerformanceAttributes` | `pickupLodgementTimestamp` | *(empty — TODO)* |
| `LogisticsPerformanceAttributes` | `pickupModel` | *(empty — TODO)* |
| `LogisticsPerformanceAttributes` | `preAllocatedAwbBlockRef` | *(empty — TODO)* |
| `LogisticsPerformanceAttributes` | `readyToShip` | *(empty — TODO)* |
| `LogisticsPerformanceAttributes` | `readyToShipBy` | *(empty — TODO)* |
| `LogisticsPerformanceAttributes` | `readyToShipTimestamp` | *(empty — TODO)* |
| `LogisticsPerformanceAttributes` | `requestedPickupDate` | *(empty — TODO)* |
| `LogisticsPerformanceAttributes` | `requestedPickupWindow` | *(empty — TODO)* |
| `LogisticsPerformanceAttributes` | `rtsNotificationRouting` | *(empty — TODO)* |
| `LogisticsPerformanceAttributes` | `rtsPickupToken` | *(empty — TODO)* |
| `LogisticsPerformanceAttributes` | `scheduledDeparture` | *(empty — TODO)* |
| `LogisticsPerformanceAttributes` | `shippingLabelBytes` | *(empty — TODO)* |
| `LogisticsPerformanceAttributes` | `shippingLabelFormat` | *(empty — TODO)* |
| `LogisticsPerformanceAttributes` | `shippingLabelUrl` | *(empty — TODO)* |
| `LogisticsPerformanceAttributes` | `spawnedTransportContractRefs` | *(empty — TODO)* |
| `LogisticsPerformanceAttributes` | `storageContractReference` | *(empty — TODO)* |
| `LogisticsPerformanceAttributes` | `sustainabilityReport` | *(empty — TODO)* |
| `LogisticsPerformanceAttributes` | `ticketReference` | *(empty — TODO)* |

## `logistics/provider` — 4 field(s)

| Schema | Field | Current text |
|---|---|---|
| `LogisticsProviderAttributes` | `coldChainTemperatureZones` | *(empty — TODO)* |
| `LogisticsProviderAttributes` | `hazmatClasses` | *(empty — TODO)* |
| `LogisticsProviderAttributes` | `nibNumber` | *(empty — TODO)* |
| `LogisticsProviderAttributes` | `siupNumber` | *(empty — TODO)* |

## `logistics/resource` — 26 field(s)

| Schema | Field | Current text |
|---|---|---|
| `LogisticsResourceAttributes` | `certificateOfOrigin` | *(empty — TODO)* |
| `LogisticsResourceAttributes` | `dimensions` | *(empty — TODO)* |
| `LogisticsResourceAttributes` | `hazmatAirTransportCode` | *(empty — TODO)* |
| `LogisticsResourceAttributes` | `hazmatClass` | *(empty — TODO)* |
| `LogisticsResourceAttributes` | `hazmatErgCode` | *(empty — TODO)* |
| `LogisticsResourceAttributes` | `hazmatNetExplosiveMass` | *(empty — TODO)* |
| `LogisticsResourceAttributes` | `hazmatNetQuantityPerPackage` | *(empty — TODO)* |
| `LogisticsResourceAttributes` | `hazmatOceanStowageCategory` | *(empty — TODO)* |
| `LogisticsResourceAttributes` | `hazmatPackagingCertification` | *(empty — TODO)* |
| `LogisticsResourceAttributes` | `hazmatPackagingInstruction` | *(empty — TODO)* |
| `LogisticsResourceAttributes` | `hazmatPackingGroup` | *(empty — TODO)* |
| `LogisticsResourceAttributes` | `hazmatProperShippingName` | *(empty — TODO)* |
| `LogisticsResourceAttributes` | `hazmatSegregationGroup` | *(empty — TODO)* |
| `LogisticsResourceAttributes` | `hazmatShippersDeclaration` | *(empty — TODO)* |
| `LogisticsResourceAttributes` | `hazmatUnNumber` | *(empty — TODO)* |
| `LogisticsResourceAttributes` | `hsCodes` | *(empty — TODO)* |
| `LogisticsResourceAttributes` | `importLicence` | *(empty — TODO)* |
| `LogisticsResourceAttributes` | `lithiumBattery` | *(empty — TODO)* |
| `LogisticsResourceAttributes` | `maxDimensions` | *(empty — TODO)* |
| `LogisticsResourceAttributes` | `packingList` | *(empty — TODO)* |
| `LogisticsResourceAttributes` | `skuCount` | *(empty — TODO)* |
| `LogisticsResourceAttributes` | `storageCategory` | *(empty — TODO)* |
| `LogisticsResourceAttributes` | `temperatureRequirement` | *(empty — TODO)* |
| `LogisticsResourceAttributes` | `vehicleDetails` | *(empty — TODO)* |
| `LogisticsResourceAttributes` | `vehicleRegistration` | *(empty — TODO)* |
| `LogisticsResourceAttributes` | `weight` | *(empty — TODO)* |

## `logistics/tracking` — 6 field(s)

| Schema | Field | Current text |
|---|---|---|
| `LogisticsTrackingAttributes` | `agentDetails` | *(empty — TODO)* |
| `LogisticsTrackingAttributes` | `credentials` | *(empty — TODO)* |
| `LogisticsTrackingAttributes` | `currentLocation` | *(empty — TODO)* |
| `LogisticsTrackingAttributes` | `etaMinutes` | *(empty — TODO)* |
| `LogisticsTrackingAttributes` | `refreshIntervalSeconds` | *(empty — TODO)* |
| `LogisticsTrackingAttributes` | `webhookEvents` | *(empty — TODO)* |

## `trade/commitment` — 2 field(s)

| Schema | Field | Current text |
|---|---|---|
| `TradeCommitmentAttributes` | `customisationSelections` | Required for COMPOSED and WITH_EXTRAS resources |
| `TradeCommitmentAttributes` | `price` | Set by BPP at on_select |

## `trade/consideration` — 4 field(s)

| Schema | Field | Current text |
|---|---|---|
| `TradeConsiderationAttributes` | `discountType` | Required on discount consideration lines |
| `TradeConsiderationAttributes` | `discountValue` | Required when discountType is declared |
| `TradeConsiderationAttributes` | `ppnRate` | Required on TAX consideration lines |
| `TradeConsiderationAttributes` | `ppnbmRate` | Required on PPNBM consideration lines for luxury goods |

## `trade/contract` — 13 field(s)

| Schema | Field | Current text |
|---|---|---|
| `TradeContractAttributes` | `beaCukaiReference` | Required for INTERNATIONAL_AIR and INTERNATIONAL_OCEAN logistics |
| `TradeContractAttributes` | `cancellationReasonCode` | Required when contract status is CANCELLED |
| `TradeContractAttributes` | `codAmount` | Required when paymentRail=COD |
| `TradeContractAttributes` | `creditTermsDays` | Required for B2B-CR commerce pattern |
| `TradeContractAttributes` | `fakturPajakReference` | Required for PKP sellers (identity.pkpStatus=PKP) when invoiceType=TAX_INVOICE |
| `TradeContractAttributes` | `fulfillingLocationId` | Present when provider has multiple fulfilment centres |
| `TradeContractAttributes` | `linkedContractId` | Required on all Logistics Contracts linked to a Trade fulfilment |
| `TradeContractAttributes` | `liveCommerceContext` | Required for B2C-LIVE spine; optional otherwise |
| `TradeContractAttributes` | `paymentDueDate` | Required when creditTermsDays > 0 |
| `TradeContractAttributes` | `paymentSchedule` | Required when paymentTermsPolicy is schedule-based |
| `TradeContractAttributes` | `purchaseOrderReference` | Required for B2B wholesale commerce patterns |
| `TradeContractAttributes` | `subscriptionBillingCycle` | Required for B2C-SUB commerce pattern |
| `TradeContractAttributes` | `subscriptionNextBillingDate` | Required for B2C-SUB commerce pattern |

## `trade/offer` — 8 field(s)

| Schema | Field | Current text |
|---|---|---|
| `TradeOfferAttributes` | `cancellationAllowedReasons` | Required when cancellationPolicy is not cancel.none |
| `TradeOfferAttributes` | `codEligibilityReason` | Required when codEligibilityForBuyer is declared |
| `TradeOfferAttributes` | `estimatedWaitSeconds` | Returned in on_select when queuePosition is present |
| `TradeOfferAttributes` | `minimumOrderQuantity` | Required for B2B wholesale commerce pattern |
| `TradeOfferAttributes` | `penaltyPolicy` | Auto-derived from tier + other policies; declare only for explicit override |
| `TradeOfferAttributes` | `returnEvidenceMinPhotos` | Required when returnEvidenceRequirement includes PHOTO |
| `TradeOfferAttributes` | `sellerPickupReturn` | Required when returnable is true |
| `TradeOfferAttributes` | `weightSlabs` | Required for catalogued domestic logistics patterns |

## `trade/performance` — 21 field(s)

| Schema | Field | Current text |
|---|---|---|
| `TradePerformanceAttributes` | `ageVerificationFailedReason` | Required when delivery fails due to age verification |
| `TradePerformanceAttributes` | `ageVerificationRequired` | Required when any item in order has resource.ageRestricted=true |
| `TradePerformanceAttributes` | `agentId` | Present when agent is assigned |
| `TradePerformanceAttributes` | `agentName` | Present when agent is assigned |
| `TradePerformanceAttributes` | `agentPhone` | Present when agent is assigned |
| `TradePerformanceAttributes` | `agentPhoto` | Present when agent is assigned |
| `TradePerformanceAttributes` | `awbNumber` | Added after order is picked up by logistics provider |
| `TradePerformanceAttributes` | `deliveryOtp` | Present when offer.selfPickupOtp=true or high-value item |
| `TradePerformanceAttributes` | `deliveryProofUrl` | Present after DELIVERED state |
| `TradePerformanceAttributes` | `estimatedDeliveryTime` | Present from DISPATCHED state onwards |
| `TradePerformanceAttributes` | `installationScheduling` | Present for products with installation.required=true |
| `TradePerformanceAttributes` | `lspSubscriberId` | Present when fulfilment is handled by on-network LSP |
| `TradePerformanceAttributes` | `qcNotes` | Required when qcResult is not QC_PASSED |
| `TradePerformanceAttributes` | `qcResult` | Required on Performance record for return-delivered state |
| `TradePerformanceAttributes` | `readyToShip` | Required in /update when seller is ready for pickup |
| `TradePerformanceAttributes` | `realTimeGps` | Present only in /on_track responses |
| `TradePerformanceAttributes` | `returnAgentName` | Present on return Performance records when agent assigned |
| `TradePerformanceAttributes` | `returnTrackingUrl` | Present on return Performance after RETURN_PICKED state |
| `TradePerformanceAttributes` | `selfPickupCode` | Present for SELF_PICKUP performance mode |
| `TradePerformanceAttributes` | `shippingInsurance` | Required when offer.price > IDR 5,000,000 or category-mandated |
| `TradePerformanceAttributes` | `trackingUrl` | Present after DISPATCHED state |

## `trade/provider` — 2 field(s)

| Schema | Field | Current text |
|---|---|---|
| `TradeProviderAttributes` | `averagePreparationTime` | Required for food-qsr and quick-commerce providers |
| `TradeProviderAttributes` | `categoryLicenses` | Required for regulated categories (pharmacy, alcohol, tobacco, meat) |

## `trade/resource` — 22 field(s)

| Schema | Field | Current text |
|---|---|---|
| `TradeResourceAttributes` | `agritech` | Required for agritech and fresh produce |
| `TradeResourceAttributes` | `beauty` | Required for beauty and personal care products |
| `TradeResourceAttributes` | `bundleComposition` | Required when offer.offerType=BUNDLE |
| `TradeResourceAttributes` | `canonicalId` | Required for marketplace-eligible products (MP-IH, MP-IL) |
| `TradeResourceAttributes` | `customisationGroups` | Required when resourceStructure IN [COMPOSED, WITH_EXTRAS] |
| `TradeResourceAttributes` | `dataResidency` | Required for pharmacy, health-data, financial-services categories |
| `TradeResourceAttributes` | `digital` | Required when resourceTangibility IN [DIGITAL_VOUCHER, DIGITAL_TOP_UP, DIGITA... |
| `TradeResourceAttributes` | `electronics` | Required for electronics and appliance products |
| `TradeResourceAttributes` | `fashion` | Required for fashion and apparel products |
| `TradeResourceAttributes` | `food` | Required for food and beverage resources |
| `TradeResourceAttributes` | `geographicIndicationCert` | Required when regionOfOrigin is declared for GI products |
| `TradeResourceAttributes` | `installation` | Required for appliances and furniture needing installation |
| `TradeResourceAttributes` | `menuCategory` | Required for F&B providers |
| `TradeResourceAttributes` | `minAge` | Required when ageRestricted is true |
| `TradeResourceAttributes` | `packaged` | Required for packaged goods |
| `TradeResourceAttributes` | `parentResourceId` | Required when resourceStructure IN [VARIANT, WITH_EXTRAS] |
| `TradeResourceAttributes` | `pharmacy` | Required for pharmaceutical and OTC medicine |
| `TradeResourceAttributes` | `preparation` | Required for F&B and perishable products |
| `TradeResourceAttributes` | `preparationTime` | Required for F&B and made-to-order items |
| `TradeResourceAttributes` | `productCode` | Required for FMCG, electronics, cross-border products |
| `TradeResourceAttributes` | `regionOfOrigin` | Required when product claims Geographic Indication status |
| `TradeResourceAttributes` | `warranty` | Required for electronics, appliances, consumer durables |
