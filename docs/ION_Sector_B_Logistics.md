# ION Sector B — Logistics

**Read this before writing any logistics code.** This is the single reference for the logistics sector: architecture, catalog model, spines and branches, regulatory requirements, Framework Agreements, dispute model, post-fulfilment flows, and the discovery intent patterns.

If you have not already, read [`ION_Developer_Orientation.md`](ION_Developer_Orientation.md) first — it explains ION's cross-sector concepts (BAP/BPP, two-phase architecture, ONIX, Atlas, policy resolution) that this doc assumes.

---

## 1. What ION Logistics is

An open logistics network for Indonesia built on Beckn Protocol v2.0.0. Any BAP (marketplace, merchant platform, fleet operator, consumer app) and any BPP (LSP, carrier, freight forwarder, warehouse operator) registered on ION can transact without bilateral integration.

A marketplace like Tokopedia can query JNE, J&T, SiCepat, GoSend, and Samudera through a single protocol. An LSP registered once is reachable by every BAP on the network.

### Sector scope

Logistics covers the movement and storage of physical goods:
- **Parcel delivery** — domestic and cross-border, B2C and B2B
- **Hyperlocal / on-demand delivery** — sub-day, single-rider, within-city
- **Freight transport** — road, sea, air, rail, river, and multi-modal
- **Ro-Ro / vessel transport** — self-accompanied cargo on ferries
- **Cross-border logistics** — with customs clearance
- **Warehousing and fulfilment** — storage, FBA-style, value-added services

Out of scope: movement of people (future mobility sector), standalone financial settlements (future finance sector), placement of orders for products (Sector A Trade — though Trade contracts trigger Logistics contracts for physical fulfilment).

### Who participates

**BPP — the LSP side.** Parcel carriers (JNE, J&T, SiCepat, Lion Parcel, Anteraja, Pos Indonesia), hyperlocal couriers (GoSend, GrabExpress, Lalamove), freight carriers (Samudera, SPIL, Puninar, Linfox), ferry operators (ASDP, private Ro-Ro), international carriers and forwarders (DHL, FedEx, Kuehne+Nagel, ALFI members), warehouse operators (TokoCabang, Shopee SLS, 3PL warehouses), and 3PL/4PL aggregators (Shipper.id, GoTo Logistics). A 3PL aggregator registers as a BPP representing multiple underlying LSPs; the aggregator's catalog shows its full service range, and underlying carrier assignment is internal.

**BAP — the shipper side.** Marketplaces (Tokopedia, Shopee, Lazada, Blibli), brand direct-to-consumer platforms, merchant seller platforms, fleet operators, B2B procurement platforms, and individual consumers (via consumer-facing apps that act as BAPs).

---

## 2. Two-phase architecture (logistics specifics)

ION's two-phase architecture (see orientation doc) applies directly. A few logistics specifics below.

### Phase 1 — Catalog

```
BPP publishes catalog → ION Catalogue Service (Beckn Fabric)
                                ↕
                       Discover Service (CDS)
                       (ION-hosted or BAP-hosted)
                                ↕
BAP subscribes → CDS → /on_discover → BAP pipeline
```

BPPs do **not** respond to per-query catalog requests. They publish once (and update when rates or coverage change). BAPs subscribe and receive catalogs asynchronously. The `catalog/pull` endpoint can be used to pull a snapshot on demand. For spot-rate lookups (freight, Ro-Ro, one-off pricing not covered by active subscriptions), BAPs use active `/discover` — see §11 for intent payload patterns.

The catalog is a **document**, not a query engine. It carries rate *logic* (not per-shipment rates), coverage, capabilities, policy IRI references, and operational parameters. Per-shipment rates come from `/select`.

### Phase 2 — Transaction (direct BAP ↔ BPP)

```
BAP → /select  → BPP → /on_select    [optional per offer.selectRequired]
BAP → /init    → BPP → /on_init
BAP → /confirm → BPP → /on_confirm
BPP → /on_status (×N, unsolicited, through all performance states)
BAP ↔ BPP → /update / /on_update     (disputes, weight diff, address change)
BAP ↔ BPP → /cancel / /on_cancel     (if cancellation branch fires)
BAP → /track → BPP → /on_track       (real-time tracking handle)
BAP → /rate → BPP → /on_rate         (post-delivery)
BAP ↔ BPP → /reconcile / /on_reconcile  (ION L3 extension — settlement)
BAP → /raise → ION → /on_raise       (ION L3 extension — escalation)
```

Every call returns an immediate ACK. Actual responses arrive via callbacks to the caller's endpoint. Beckn is async throughout Phase 2. There is no `/search` in Beckn 2.0.0 — discovery is via catalog subscription or `/discover`.

---

## 3. The logistics catalog — the intelligence layer for BAP allocation

The catalog is how sophisticated BAPs (Tokopedia, Shopee) decide which LSPs to `/select` against. Allocation algorithms subscribe to catalogs from all relevant LSPs, build an eligibility engine, and at order time narrow to the top-K candidates before calling `/select`.

### What BAPs use from the catalog to filter

1. **Coverage** — does this LSP serve my pickup and delivery pincodes?
2. **Service level** — INSTANT, SAME_DAY, NEXT_DAY, STANDARD_2_3D, ECONOMY, SCHEDULED
3. **Transport mode** — motorcycle, car, van, truck, rail, sea, air, river, ferry
4. **Capabilities** — cold chain? Hazmat? High-value insurance? COD?
5. **Rate logic** — how rates are computed (`TIERED_BY_ZONE_AND_WEIGHT`, `DISTANCE_BASED`, `PER_CONTAINER`, etc.)
6. **`selectRequired`** — will I need to call `/select`, or can I skip to `/init`?
7. **Operating hours** — is the LSP accepting bookings right now?

Key fields in `offer.offerAttributes`: `serviceLevel`, `transportMode`, `routingTopology` (P2P/P2H2P/P2H2H2P for parcel), `rateLogic`, `selectRequired`, `quoteValidityWindow`, and policy IRIs (`cancellationPolicy`, `claimPolicy`, `slaPolicy`, `evidencePolicy`, `disputePolicy`, `reAttemptPolicy`).

### What comes from `/select`

Binding rate for this specific shipment (pickup pincode × drop pincode × actual weight × service level), capacity confirmation, quote validity window. Per-shipment rates are never in the catalog.

### The `selectRequired` flag — the single most important field

| `selectRequired` | Meaning | When to set `true` |
|---|---|---|
| `true` | BAP MUST call `/select` before `/init` for a firm quote | Zone-computed rates, capacity-constrained, dynamic/surge pricing |
| `false` | Catalog rate is binding; `/select` MAY be skipped | Fixed rate cards with pre-validated coverage |

Under an active Framework Agreement (see §6), `/select` can typically be skipped entirely — the FWA rate card is binding. The BAP checks `contractAttributes.fwaReference` and the FWA's scope before skipping.

---

## 4. Indonesian regulatory requirements

| Field | Regulation | Where it lives | Applies to |
|---|---|---|---|
| `nibNumber` | UU 11/2020 (Cipta Kerja) | `providerAttributes` | All LSPs |
| `siupNumber` | PP 5/2021 | `providerAttributes` | Freight and warehouse |
| `npwp` | UU 36/2008; PMK 112/2022 (16-digit format) | `contractAttributes`, `participantAttributes` | B2B transactions |
| `beaCukaiLicenceNumber` | PMK 229/2017 | `providerAttributes` | LOG-XB providers |
| `hsCodes[]` | Bea Cukai nomenclature | `resourceAttributes` | LOG-XB |
| `provinsiCode` | BPS provincial coding | `participant.addressDetail`, `performance.stops[].location` | All spines |
| Faktur Pajak reference | UU 42/2009 | `contractAttributes.invoicePreferences` | B2B with VAT |
| `ppnRate` | UU 7/2021 HPP; current applicable PMK (e.g. PMK 131/2024) | `considerationAttributes.breakup[]` | All taxable transactions |
| `alfiMembership` | SK DJPLN | `providerAttributes` | Freight forwarders |
| `ppjkLicenceNumber` | PMK 219/PMK.04/2019 | `participantAttributes` (logistics addendum) | Customs brokers |
| `driverLicenceNumber`, `driverLicenceCategory` | UU 22/2009 LLAJ; Perpol 5/2021 | `participantAttributes` (logistics addendum) | Drivers (LOG-RORO, LOG-FREIGHT, LOG-HYPERLOCAL) |

Tax rates are **not hardcoded** anywhere in the spec. Implementations source the applicable rate from current DJP/PMK regulation.

---

## 5. The six logistics spines

A spine is a distinct API sequence with distinct message structure. Every logistics transaction runs on exactly one spine.

| Spine | Use when | Example carriers |
|---|---|---|
| **LOG-HYPERLOCAL** | Sub-day, single-rider, within-city | GoSend, GrabExpress, Paxel instant |
| **LOG-PARCEL** | Hub-routed parcel, any distance, B2C or B2B | JNE, J&T, SiCepat, Anteraja — AWB-based |
| **LOG-FREIGHT** | Capacity-based — FTL, FCL, LCL, air cargo, rail, river | Samudera, SPIL, Puninar — bill-of-lading-based |
| **LOG-RORO** | Vehicle-accompanied on ferry — consignor rides with cargo | ASDP, port-to-port, ticket-based |
| **LOG-XB** | Cross-border with Bea Cukai customs clearance | DHL, FedEx, international forwarders |
| **LOG-WAREHOUSE** | Storage, FBA-style fulfilment, value-added services | TokoCabang, 3PL storage, dark stores |

**LOG-PARCEL is the reference spine.** All other spines are defined as deltas from it.

### Things that do NOT create a new spine

- Service level (same-day vs next-day vs economy) → `offer.serviceLevel` enum
- Transport mode (road vs air vs sea) → `offer.transportMode` enum
- Hub routing topology (P2P vs P2H2P vs P2H2H2P) → state machine variant within LOG-PARCEL
- B2B vs B2C → participant identity fields + eKYC branch; same spine
- Cold chain → resource attribute + cold-chain branch
- COD → payment method in settlement + cod branch
- Slotted delivery → `offer.slotsAvailable` + `contract.selectedDeliverySlot`

### Choosing the right spine

| Requirement | Spine |
|---|---|
| Same-city, today, single rider | LOG-HYPERLOCAL |
| Package Jakarta→Surabaya, 2kg, next-day | LOG-PARCEL |
| Container of electronics Jakarta→Makassar by sea | LOG-FREIGHT |
| Truck + driver on ferry Java→Bali | LOG-RORO |
| Electronics export Indonesia→Germany | LOG-XB |
| Merchant wants TokoCabang to store and fulfil orders | LOG-WAREHOUSE |
| Cold-chain vaccines, national | LOG-PARCEL + cold-chain branch |
| Tokopedia reserves 500k parcels/day from JNE, month-ahead | LOG-PARCEL + FWA parent contract |
| Daily milk run — factory to 5 distributors | LOG-FREIGHT + FWA parent contract + `stops[]` |

### State machine selection

Every transaction runs on one of 10 defined state machines. Selection is determined by spine plus `routingTopology` or `agentAssignmentModel`:

| Spine + variant | State machine |
|---|---|
| LOG-HYPERLOCAL (PRE_ASSIGNED or DEDICATED_FLEET) | `hyperlocal-pre-assigned` |
| LOG-HYPERLOCAL (FIFO_AT_PICKUP or POOL_ASSIGNED) | `hyperlocal-fifo` |
| LOG-PARCEL (P2P) | `parcel-p2p` |
| LOG-PARCEL (P2H2P) | `parcel-p2h2p` |
| LOG-PARCEL (P2H2H2P) | `parcel-p2h2h2p` |
| LOG-PARCEL (reverse branch) | `parcel-reverse-qc` |
| LOG-FREIGHT | `freight-capacity` |
| LOG-RORO | `roro` |
| LOG-XB | `xb` |
| LOG-WAREHOUSE | `warehouse-inventory` |

All 10 are defined in `schema/extensions/logistics/performance-states/v1/states.yaml`.

---

## 6. Branches — conditional sub-flows

Branches are not spine variants. They attach to an active spine transaction when a specific condition is met. Multiple branches can be active simultaneously on the same transaction.

| Family | Activation trigger | Key impact |
|---|---|---|
| **eKYC** | B2B transaction without active FWA | KYC exchange at `/init` |
| **Attempts** | DELIVERY_ATTEMPT_FAILED state | NDR, reschedule, address change, auto-RTO |
| **Weight dispute** | LSP reweighs and finds discrepancy | `/update` dispute flow |
| **Cold chain** | `temperatureRequirement.controlled=true` | Temperature proof at pickup and delivery |
| **COD** | `settlement.method=COD` | Cash collection, remittance |
| **Exception** | Damage, loss, unserviceable address, pickup failure | Claim flow via `/update` |
| **Reverse** | Post-delivery return initiated | Per-spine reverse variant |
| **Customs** | LOG-XB customs events | Clearance states, hold resolution |
| **Incident** | Accident, breakdown, robbery, force majeure, rider refusal | Triage and alternate routing |
| **Value-added** | VAS selected at `/init` in LOG-WAREHOUSE | QC, kitting, labelling, packaging |
| **During-transaction** | Between `/select` and `/on_confirm` | Payment method, FWA activation, eKYC |
| **Cancellation** | After `/on_confirm` | Cancel with attribution |
| **RTS handoff** | Return-to-sender triggered | Seller-direct, same-BPP warehouse, cross-BPP warehouse |
| **Cross-cutting** | Always available | Track, support, rating, reconcile, raise |

---

## 7. Framework Agreements (FWA)

Enterprise logistics relationships don't work on public rate cards. A large marketplace ships millions of parcels per month with a carrier at negotiated rates, defined SLAs, and structured dispute resolution. This relationship is governed by an FWA.

The FWA is a **registered policy document** in the ION policy registry:
```
ion://policy/logistics-fwa/{bap-short}.{bpp-short}.{year}
```

When a transaction references an active FWA via `contractAttributes.fwaReference`:
1. FWA rate card applies (not catalog public rates)
2. `/select` is typically optional (FWA rates are binding, not zone-computed)
3. eKYC is waived (parties verified at FWA registration)
4. SLA, evidence, insurance, COD remittance, and dispute policies from the FWA apply instead of offer-level policies

**FWAs also enable the parent-child transaction pattern:** a long-term FWA governs the commercial envelope; individual shipment transactions execute as children. Milk-run, dedicated fleet, and capacity pre-booking all use this pattern.

FWAs are registered with ION, not negotiated through the protocol. The legal MSA is negotiated offline and the structured YAML is registered to the policy registry.

---

## 8. Policy registry — how commercial terms are enforced

All commercial terms — cancellation conditions, evidence requirements for claims, SLA thresholds and rebates, re-attempt limits, weight dispute tolerances, COD remittance schedules — are expressed as policy IRIs in the ION policy registry.

Policy IRI format: `ion://policy/{category}.{sub-category}.{variant}`

Examples:
```
ion://policy/cancel.standard.until-dispatched
ion://policy/re-attempt.standard-3-free
ion://policy/sla.enterprise-95pct-rebate
ion://policy/evidence.standard.photo-24hr
ion://policy/weight-dispute.enterprise-5pct-tolerance
ion://policy/logistics-fwa/tokopedia-jne-2026q2
```

ION Central enforces these at every API boundary. If a BPP tries to charge a cancellation fee that doesn't match the declared policy, the network rejects it.

Logistics uses Trade's cross-sector policy categories (`cancellation`, `payment-terms`, `penalty`, `dispute`) plus its own: `evidence`, `insurance`, `sla`, `re-attempt`, `weight-dispute`, `liability`, `incident`, `rts-handoff`, `logistics-fwa`.

---

## 9. Dispute model — everything goes through /update, escalate via /raise

**There is no `/issue` endpoint.** ION Logistics does not use the ONDC IGM model. Bilateral disputes are mutations of the contract through `/update`, not a parallel channel. Only network escalation uses `/raise`.

Flow:
1. Commercial dispute arises → open `/update` on the contract with `contractAttributes.disputeReason.policyIri`
2. Counter-party responds via `/on_update`
3. Evidence exchanged via further `/update` calls per the `evidence` policy
4. Resolution: acceptance → contract state resolves; counter → negotiate; no resolution within policy SLA → escalate
5. Escalation: either party calls `/raise` → ION Central adjudicates using the contract's full update history as evidence
6. ION Central issues ruling via `/on_raise`; parties may follow up via `raise_status` and `raise_details`

`/raise` is an ION L3 protocol extension (see [`ION_Beckn_Conformance.md`](ION_Beckn_Conformance.md)). The full raise protocol has 6 endpoints: `raise`, `on_raise`, `raise_status`, `on_raise_status`, `raise_details`, `on_raise_details`.

---

## 10. Post-fulfilment flows

### Rider and agent details

For LOG-HYPERLOCAL, rider identity is exposed in `on_status` updates. When it's exposed depends on `offer.agentAssignmentModel`:

| Model | Rider known at |
|---|---|
| PRE_ASSIGNED | RIDER_ASSIGNED `on_status` |
| DEDICATED_FLEET | RIDER_ASSIGNED `on_status` |
| POOL_ASSIGNED | RIDER_EN_ROUTE_TO_PICKUP `on_status` |
| FIFO_AT_PICKUP | PICKED_UP `on_status` |

Phone numbers are **always proxy numbers**. Direct phone numbers are never exposed on the network. Proxy communication is handled by the BPP's infrastructure.

`agentDetails` in `performance.performanceAttributes` carries `name`, `phoneProxy`, `vehicleType`, `vehiclePlate`, `photoUrl`. Real-time GPS is served via `/track` → `/on_track`, not via `on_status`. The tracking handle returned in `/on_track` is a URL or WebSocket endpoint that streams live GPS.

### Rating (`/rate` → `/on_rate`)

Opens at DELIVERED state. Use `context.try=true` to preview the rating form. Dimensions: CONTRACT_OVERALL, FULFILLMENT_TIMELINESS, PACKAGE_CONDITION, AGENT_BEHAVIOUR, PROVIDER_SERVICE. One `/rate` call per dimension.

### Reconcile (`/reconcile` → `/on_reconcile`) — L3 extension

Financial settlement after contract is COMPLETE. Carries: base amount, weight adjustments, SLA rebates, COD amounts, PPN declarations, FWA volume rebates. Use `context.try=true` to preview the settlement statement. If `reconStatus=DISPUTED`, raise a ticket via `/raise`.

### Support (`/support` → `/on_support`)

Customer care queries. Use `context.try=true` to see available channels. Use `context.try=false` to submit a ticket. Categories: SHIPMENT_STATUS, RIDER_CONTACT_REQUEST, DELIVERY_RESCHEDULING, DOCUMENTATION_REQUEST, DAMAGED_ON_ARRIVAL, GENERAL.

---

## 11. Discovery intent patterns — /discover payloads

When a BAP uses active discovery (`/discover` → `/on_discover`) instead of catalog subscription, the `DiscoverAction.intent` carries a structured description of what the BAP is looking for.

**Important — Beckn's `Intent` is a closed schema.** Beckn 2.0.0 defines `Intent` with `additionalProperties: false` and exactly four properties:

| Field | Purpose |
|---|---|
| `textSearch` | Free-text query string |
| `filters` | `{ type: "jsonpath", expression: "<JSONPath>" }` — structured filter against catalog items |
| `spatial` | Array of `SpatialConstraint` objects using OGC CQL2 semantics (`S_WITHIN`, `S_INTERSECTS`, `S_DWITHIN`, etc.) |
| `mediaSearch` | Image/audio/video search |

ION-specific attributes (spine codes, pincodes, shipment profile, container types, HS codes, etc.) **do not** go directly inside `intent.*`. They live on the BPP's **catalog items** (inside the relevant `*Attributes` bags — `offerAttributes`, `resourceAttributes`) and the BAP uses `filters.expression` (JSONPath) to select against them, plus `spatial[*]` to constrain by geography.

BAPs typically use `/discover` for spot-rate lookups (LOG-FREIGHT, LOG-RORO), one-off pricing queries not covered by active subscriptions, and cross-network discovery across multiple BPPs simultaneously.

### How ION attributes reach the catalog item

Before the intent patterns below make sense, remember the shape of a catalog item published by an LSP BPP. Each offer in the catalog carries ION's extension fields inside `offer.offerAttributes`:

```json
{
  "id": "JNE-REG-JKT-SBY",
  "offerAttributes": {
    "@context": "https://schema.ion.id/logistics/v1/context.jsonld",
    "@type": "ion:LogisticsParcelOffer",
    "spineCode": "LOG-PARCEL",
    "serviceLevel": "NEXT_DAY",
    "transportMode": "road",
    "routingTopology": "P2H2P",
    "coverage": {
      "originProvinsiCodes": ["31", "32", "33", "34", "35", "36"],
      "destinationProvinsiCodes": ["35", "73"]
    },
    "rateLogic": "TIERED_BY_ZONE_AND_WEIGHT",
    "availableOnCod": true,
    "insuranceAvailable": true,
    "selectRequired": true,
    "serviceAreaGeometry": {
      "type": "MultiPolygon",
      "coordinates": [[[ [106.7, -6.3], [106.9, -6.3], [106.9, -6.1], [106.7, -6.1], [106.7, -6.3] ]]]
    }
  }
}
```

The `spatial[*]` constraints in an intent match against geometric fields inside the item document — typically `offerAttributes.serviceAreaGeometry` or `providerAttributes.availableAt[*].geo`. The `filters.expression` runs as JSONPath over the entire item document.

### Pattern 1 — Parcel rate lookup (LOG-PARCEL)

Find LSPs offering `LOG-PARCEL` + `NEXT_DAY` service, serving origin pincode in DKI Jakarta (provinsi 31) and destination in East Java (provinsi 35), with insurance available and COD *not* required.

```json
{
  "intent": {
    "filters": {
      "type": "jsonpath",
      "expression": "$[?(@.offerAttributes['@type']=='ion:LogisticsParcelOffer' && @.offerAttributes.spineCode=='LOG-PARCEL' && @.offerAttributes.serviceLevel=='NEXT_DAY' && '31' in @.offerAttributes.coverage.originProvinsiCodes && '35' in @.offerAttributes.coverage.destinationProvinsiCodes && @.offerAttributes.insuranceAvailable==true)]"
    }
  }
}
```

Weight, dimensions, and declared value are not part of discovery — those become binding at `/select` (the BAP submits the actual shipment profile there and gets a firm rate back).

### Pattern 2 — Freight capacity lookup (LOG-FREIGHT)

Find carriers offering sea or air freight from Tanjung Priok port (IDTPP) to Makassar port (IDMAK) with capacity for 40FT dry containers on 2026-05-10.

```json
{
  "intent": {
    "filters": {
      "type": "jsonpath",
      "expression": "$[?(@.offerAttributes['@type']=='ion:LogisticsFreightOffer' && @.offerAttributes.spineCode=='LOG-FREIGHT' && (@.offerAttributes.transportMode=='sea' || @.offerAttributes.transportMode=='air') && 'IDTPP' in @.offerAttributes.originPorts && 'IDMAK' in @.offerAttributes.destinationPorts && 'CONTAINER_40FT_DRY' in @.offerAttributes.containerTypesSupported)]"
    }
  }
}
```

Tonnage, incoterm, and hazard class are finalized at `/select`. If the BAP genuinely needs to pre-filter by capacity window (e.g., book-ahead), the BPP publishes a `capacityCalendar[]` inside `offerAttributes` and the filter JSONPath tests a date range.

### Pattern 3 — Hyperlocal instant (LOG-HYPERLOCAL)

Find hyperlocal BPPs whose service area polygon contains the pickup point in Jakarta (using a spatial constraint), offering hot-food delivery capability.

```json
{
  "intent": {
    "filters": {
      "type": "jsonpath",
      "expression": "$[?(@.offerAttributes.spineCode=='LOG-HYPERLOCAL' && 'HOT' in @.offerAttributes.temperatureRangesSupported)]"
    },
    "spatial": [
      {
        "targets": ["$.offerAttributes.serviceAreaGeometry"],
        "op": "S_CONTAINS",
        "geometry": {
          "type": "Point",
          "coordinates": [106.8456, -6.2088]
        }
      }
    ]
  }
}
```

CQL2 `S_CONTAINS` means "the offer's service-area polygon contains this pickup point." Combine with a second spatial constraint for the drop point if needed.

### Pattern 4 — Warehouse discovery (LOG-WAREHOUSE)

Find warehouses within 50 km of a given location in East Java (provinsi 36) offering ambient storage and QC + kitting value-added services.

```json
{
  "intent": {
    "filters": {
      "type": "jsonpath",
      "expression": "$[?(@.offerAttributes.spineCode=='LOG-WAREHOUSE' && @.offerAttributes.storageType=='AMBIENT' && 'QC' in @.offerAttributes.valueAddedServices && 'KITTING' in @.offerAttributes.valueAddedServices)]"
    },
    "spatial": [
      {
        "targets": ["$.providerAttributes.availableAt[*].geo"],
        "op": "S_DWITHIN",
        "geometry": {
          "type": "Point",
          "coordinates": [112.7521, -7.2575]
        },
        "distanceMeters": 50000
      }
    ]
  }
}
```

### Pattern 5 — Cross-border (LOG-XB)

Find international forwarders handling ID → DE DDP service supporting HS chapters 85.17 (telephony).

```json
{
  "intent": {
    "filters": {
      "type": "jsonpath",
      "expression": "$[?(@.offerAttributes.spineCode=='LOG-XB' && 'ID' in @.offerAttributes.originCountries && 'DE' in @.offerAttributes.destinationCountries && @.offerAttributes.serviceType=='DDP' && '8517' in @.offerAttributes.hsChaptersSupported)]"
    }
  }
}
```

### Intent vs textSearch

Beckn 2.0.0 also supports `textSearch` on `DiscoverAction` for free-text queries. ION Logistics recommends structured `filters.expression` over `textSearch` wherever possible — JSONPath filters enable deterministic matching at the CDS; textSearch falls back to best-effort natural-language matching. Structured filters are mandatory for spot-rate patterns; textSearch is acceptable for exploratory queries ("LSPs serving Surabaya").

### What about the shipment profile?

The discovery intent **never** carries the actual shipment's weight, dimensions, declared value, pickup time, or special-handling requirements. Those are submitted as part of `/select` when the BAP has chosen candidate BPPs from the `/on_discover` results. The `/select` request body carries the full shipment profile inside `contract.commitments[*].resources[*].resourceAttributes` (an ION `ion:LogisticsShipment` JSON-LD type), and each candidate BPP returns a binding quote via `/on_select`.

This separation is deliberate: discovery is broad and cheap (one filter, many BPPs); select is precise and potentially expensive (binding quote, capacity reservation).

---


## 12. Schema pack composition

Each API step uses a combination of ION core packs (L4) and ION logistics packs (L5). The spine definition's `schemaPacks` field at each step declares which packs apply. See [`ION_Layer_Model.md`](ION_Layer_Model.md) for the full layer explanation and [`ION_Beckn_Conformance.md`](ION_Beckn_Conformance.md) for the complete attachment table.

**ION core packs used by logistics** (in `schema/extensions/core/`):
- `address/v1`, `identity/v1`, `localization/v1`, `participant/v1`, `payment/v1`, `product/v1`, `raise/v1`, `rating/v1`, `reconcile/v1`, `support/v1`, `tax/v1`

**ION logistics packs** (in `schema/extensions/logistics/`):
- `provider/v1` → `Provider.providerAttributes`
- `resource/v1` → `Resource.resourceAttributes`
- `offer/v1` → `Offer.offerAttributes` (includes COD fraud-control policy fields)
- `consideration/v1` → `Consideration.considerationAttributes`
- `performance/v1` → `Performance.performanceAttributes`
- `contract/v1` → `Contract.contractAttributes`
- `commitment/v1` → `Commitment.commitmentAttributes`
- `tracking/v1` → `Tracking.trackingAttributes`
- `performance-states/v1` — state machine definitions (not an attribute bag)
- `participant-logistics/v1` → `Participant.participantAttributes` (thin addendum alongside `core/participant/v1`; carries PPJK, driver SIM)

---

## 13. Getting started

**BPP (LSP, carrier, warehouse):**
1. Pick your spine(s)
2. Read your spine's `README.md` and `spine.yaml`
3. Compose your catalog using `schema/extensions/logistics/` packs (plus the core packs listed above)
4. Publish via `/catalog/publish`
5. Implement Phase 2 callbacks (`/on_select`, `/on_init`, `/on_confirm`, unsolicited `/on_status` pushes)
6. Implement branch handlers for the branches your spine supports

**BAP (marketplace, merchant platform, fleet operator):**
1. Subscribe to catalogs via `/catalog/subscription`
2. Build your allocation algorithm using catalog attributes (coverage, rate logic, `selectRequired`)
3. Implement `/select` → `/on_select` → `/init` → `/on_init` → `/confirm` → `/on_confirm`
4. Handle unsolicited `/on_status` pushes
5. Implement branch-specific `/update` flows for active branches

---

## 14. Directory map

```
schema/extensions/logistics/       ← WHAT things ARE
  provider/v1/                     ← Provider capabilities and identity
  resource/v1/                     ← Shipment/inventory/vehicle object
  offer/v1/                        ← Service terms, rate logic, COD policy
  consideration/v1/                ← Financial breakup
  performance/v1/                  ← Execution tracking
  contract/v1/                     ← Confirmed terms and dispute state
  commitment/v1/                   ← Line-item detail
  tracking/v1/                     ← Live tracking handles
  performance-states/v1/           ← All 10 state machine definitions
  participant-logistics/v1/        ← Thin licence-field addendum (PPJK, SIM)

flows/logistics/                   ← WHAT things DO
  spines/                          ← 6 spine definitions
    LOG-PARCEL/                    ← Reference spine (read this first)
    LOG-HYPERLOCAL/  LOG-FREIGHT/  LOG-RORO/  LOG-XB/  LOG-WAREHOUSE/
  branches/                        ← 13 branch families
    ekyc/  attempts/  weight-dispute/  cold-chain/  cod/
    exception/  reverse/  customs/  incident/  value-added/
    during-transaction/  cancellation/  rts-handoff/  cross-cutting/

policies/                          ← WHAT governs (logistics-originated categories)
  logistics-fwa/v1/   evidence/v1/   insurance/v1/   sla/v1/
  re-attempt/v1/   weight-dispute/v1/   liability/v1/
  incident/v1/   rts-handoff/v1/
  (cancellation, payment-terms, penalty, dispute are cross-sector — shared with trade)

errors/
  logistics.yaml                   ← All error codes (ION-LOG-Nxxx)
```

---

## 15. What this spec covers that ONDC Logistics does not

| Concern | ONDC-LOG | ION Logistics |
|---|---|---|
| Hyperlocal / instant delivery | Not covered | LOG-HYPERLOCAL spine |
| FIFO agent assignment | Not covered | `agentAssignmentModel` enum + state variants |
| Slotted delivery | Not covered | `offer.slotsAvailable` + `contract.selectedDeliverySlot` |
| Framework Agreements / enterprise rates | Out-of-band | `logistics-fwa` policy construct |
| Inter-island water transport | Not covered | LOG-FREIGHT with `transportMode: sea/river/ferry` |
| Ro-Ro / vehicle-accompanied | Not covered | LOG-RORO spine |
| Warehousing and fulfilment | Not covered | LOG-WAREHOUSE spine |
| Value-added logistics | Not covered | VAS branches on LOG-WAREHOUSE |
| Cold chain proof-of-condition | Not covered | cold-chain branch |
| Multi-attempt with NDR codes | Basic | Full attempts branch with 5 sub-branches |
| Dispute resolution | IGM channel (separate) | `/update` with policy IRIs; `/raise` for escalation |
| Machine-enforceable policies | Narrative PDFs | Ratified policy IRI registry |
| Reconcile with adjustments | Basic | Full reconcile including weight-dispute adjustments, SLA rebates, FWA rebates |

---

## 16. Open questions for ION Council (Sector B)

| # | Question | Impact |
|---|---|---|
| 1 | Which spines are mandatory for network participation? | Minimum implementation bar |
| 2 | Are all 10 state machines ratified, or are some aspirational? | Implementation priority |
| 3 | What is FWA registration governance? Who approves a submitted FWA? | Governance load |
| 4 | Which policy instances are mandatory vs optional at launch? | What must LSPs implement |
| 5 | How is LOG-RORO licensed vs registered? Is ASDP a BPP or a special participant? | Regulatory clarity |
| 6 | What is the accountability model for 3PL aggregators — aggregator liability or underlying LSP liability? | Dispute attribution |
| 7 | Does inter-island water transport require cabotage compliance checks? Who enforces? | Regulatory burden |

---

*Last updated v0.5.2-draft — April 2026*

## See also

- **First time here?** [`ION_Start_Here.md`](ION_Start_Here.md)
- **Confused by an acronym?** [`ION_Glossary.md`](ION_Glossary.md)
- **End-to-end transaction example?** [`ION_First_Transaction.md`](ION_First_Transaction.md)
- **Cross-sector concepts?** [`ION_Developer_Orientation.md`](ION_Developer_Orientation.md)
- **Layer model (L1-L5)?** [`ION_Layer_Model.md`](ION_Layer_Model.md)
- **Signing and auth?** [`ION_Onboarding_and_Auth.md`](ION_Onboarding_and_Auth.md)
- **Doing trade instead?** [`ION_Sector_A_Trade.md`](ION_Sector_A_Trade.md)
