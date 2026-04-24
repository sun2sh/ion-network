# offer/v1 — Logistics Offer Attributes

Attaches to `beckn:Offer.offerAttributes`.

## What it covers

The complete terms-of-service for a logistics offering. Every logistics offer published in the catalog carries this pack. It defines what service is being sold, at what rate logic, under what commercial conditions, and which policies govern disputes and claims.

## Mandatory fields — always required in catalog

| Field | Type | Purpose |
|---|---|---|
| `serviceLevel` | enum | INSTANT \| SAME_DAY \| NEXT_DAY \| STANDARD_2_3D \| ECONOMY \| SCHEDULED |
| `transportMode` | enum | motorcycle \| car \| van \| truck \| rail \| sea \| air \| river \| ferry |
| `rateLogic` | enum | How rates are computed — TIERED_BY_ZONE_AND_WEIGHT, DISTANCE_BASED, PER_CONTAINER, etc. |
| `selectRequired` | boolean | **Most critical field for BAP.** If `true`, BAP must call `/select` before `/init` for a firm quote. If `false`, catalog rate is binding. |
| `quoteValidityWindow` | ISO 8601 duration | How long the `/on_select` quote is binding before expiry. |
| `availableOnCod` | boolean | Whether COD payment is accepted for this offer. |
| `cancellationPolicy` | IRI | `ion://policy/cancel.*` — ratified cancellation terms. |
| `claimPolicy` | IRI | `ion://policy/damage.*` or `loss.*` — ratified claim handling terms. |
| `slaPolicy` | IRI | `ion://policy/sla.*` — performance targets and breach consequences. |
| `evidencePolicy` | IRI | `ion://policy/evidence.*` — evidence requirements for claims. |
| `disputePolicy` | IRI | `ion://policy/dispute-resolution.*` — resolution channel and arbitration. |

## selectRequired — the most important decision

This flag determines the entire transaction entry path for BAPs:

```
selectRequired: false  →  Catalog rate is binding
  BAP flow: catalog lookup → /init → /confirm

selectRequired: true   →  Must get firm quote per shipment
  BAP flow: catalog lookup → /select → /on_select → /init → /confirm
```

**When to set `true`:** dynamic surge pricing, capacity-constrained offerings (air, ferry, ocean), zone-computed rates, any offer where catalog rates are indicative rather than binding.

**When to set `false`:** flat rate cards, pre-negotiated FWA rates where catalog accurately reflects what the BAP will be billed.

**Under an active FWA:** `selectRequired` may still be set to `true` for capacity confirmation even when rates are FWA-locked. BAP checks both the FWA and the offer flag.

## Rate logic types

| Value | Description | Typical use |
|---|---|---|
| `FLAT` | Same price regardless of weight/zone | Simple offerings |
| `TIERED_BY_WEIGHT` | Price per kg changes by weight slab | Most parcel services |
| `TIERED_BY_ZONE` | Price changes by origin-destination zone | Intercity parcel |
| `TIERED_BY_ZONE_AND_WEIGHT` | Both zone and weight tiers | JNE, J&T standard |
| `DISTANCE_BASED` | Price per km from pickup | GoSend, GrabExpress |
| `PER_KG` | Flat per kg with no tiers | Air cargo, LTL freight |
| `PER_CBM` | Per cubic metre | LCL ocean, LTL |
| `PER_CONTAINER` | Per 20ft or 40ft container | FCL ocean |
| `PER_TRUCK` | Per truck regardless of load | FTL |
| `PER_VESSEL_SLOT` | Per slot on a sailing | Ro-Ro, ferry |
| `SURGE_DYNAMIC` | Real-time surge computed at /select | Hyperlocal, on-demand |

## Spine-specific mandatory fields

| Spine | Additional mandatory offer fields |
|---|---|
| LOG-HYPERLOCAL | `agentAssignmentModel`, `maxDeliveryRadiusKm`, `liveTrackingEnabled` |
| LOG-PARCEL | `routingTopology` |
| LOG-FREIGHT | `capacityModel`, `consolidationType`, `scheduleType` |
| LOG-RORO | `vehicleCategoriesAccepted[]`, `sailingSchedule[]`, `crossingDuration` |
| LOG-XB | `incotermsSupported[]`, `dutyAndTaxModel` |
| LOG-WAREHOUSE | `storageBillingUnit`, `minimumStorageTerm`, `valueAddedServices[]` |

## Policy IRI naming convention

All policy IRIs follow the pattern `ion://policy/{category}.{qualifier}`:

```
ion://policy/cancel.logistics.prepickup-free
ion://policy/damage.standard.declared-value-cap
ion://policy/sla.standard-95pct
ion://policy/evidence.standard.photo-24hr
ion://policy/re-attempt.standard-3-free
ion://policy/weight-dispute.standard-10pct-tolerance
ion://policy/insurance.standard-declared-value-cap
ion://policy/payment-terms.cod-weekly-monday
ion://policy/dispute-resolution.commercial-odr
```

See `policies/README.md` for the full ratified policy registry.

## FWA interaction

When a BAP transacts under an active FWA, the FWA's `overrides` and `adds` sections supersede offer-level policies. The offer's `fwaApplicable: true` signals to BAPs that this offer accepts FWA-governed transactions. ION Central validates consistency between the FWA scope and the transaction at API boundaries.

## FWA targeting via `Offer.availableTo[]` (Beckn 2.0 native)

For enterprise-specific offers (FWA-restricted rates visible only to named BAPs), use Beckn 2.0's native `Offer.availableTo[]` field rather than inventing a custom visibility mechanism. Three targeting types are supported:

```yaml
offers:
  # Offer visible to all participants on the network
  - id: jne-reg-economy
    availableTo:
      - type: NETWORK
        id: ion.id/logistics

  # Offer visible only to a specific BAP (enterprise contract)
  - id: jne-tokopedia-fwa-nextday
    availableTo:
      - type: PARTICIPANT
        id: tokopedia.com

  # Offer visible only to participants with a specific role
  - id: jne-b2b-credit-terms
    availableTo:
      - type: ROLE
        id: SHIPPER
```

Visibility targeting is a Beckn-native mechanism independent of ION policy IRIs. The FWA policy IRI governs commercial terms (rates, credit terms, volume rebates); `availableTo[]` governs WHO can see the offer. Both are needed — the policy alone doesn't hide the offer from other BAPs.

### Mapping to FWA registration

When an FWA is registered in the logistics-fwa policy registry, ION Central automatically validates that offers referencing the FWA also carry a matching `availableTo` entry. Offers tied to a Tokopedia-JNE FWA must have `availableTo: [{type: PARTICIPANT, id: "tokopedia.com"}]`.

## Offer validity window (Beckn 2.0 native)

Use Beckn 2.0's native `Offer.validity` field (TimePeriod) for time-bound offer availability:

```yaml
offers:
  - id: jne-ramadan-promo
    validity:
      start: "2026-03-01T00:00:00Z"
      end: "2026-04-15T23:59:59Z"
    offerAttributes:
      serviceLevel: NEXT_DAY
      # PSS rate modifier for Ramadan uplift
      rateModifiers:
        - modifierType: PEAK_SEASON_SURCHARGE
          basis: PERCENT_OF_BASE
          percentOfBase: 0.15
          validFrom: "2026-03-15T00:00:00Z"
          validUntil: "2026-04-15T00:00:00Z"
```

The rate modifier's own validity is independent of the offer's validity — peak-season surcharge may kick in mid-way through an offer's overall availability window.
