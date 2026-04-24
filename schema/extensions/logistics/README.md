# ION Logistics Extension Packs

Logistics sector (Layer 5) attribute packs. These attach to Beckn-native `*Attributes` slots and apply to all logistics-sector transactions on ION — hyperlocal delivery, parcel, freight, Ro-Ro, cross-border, and warehousing.

## Packs in this directory

| Pack | Attaches to | What it covers |
|---|---|---|
| `provider/v1` | `beckn:Provider.providerAttributes` | LSP identity, licences (ALFI), coverage, modes supported, spines supported, fleet attributes, cold-chain certification, operating hours, aggregator-vs-direct |
| `resource/v1` | `beckn:Resource.resourceAttributes` | Shipment object — weight, dimensions, declared value, fragile/hazmat flags, temperature requirements, product category, packaging, vehicle-as-resource (Ro-Ro) |
| `offer/v1` | `beckn:Offer.offerAttributes` | Service level, transport mode, routing topology, rate logic, selectRequired flag, COD availability, COD fraud-control policy (OTP required, denominations, daily limits, hold periods), agent assignment model, slot availability, value-added services, MOQ |
| `consideration/v1` | `beckn:Consideration.considerationAttributes` | Freight charge, fuel surcharge, COD charge, insurance premium, handling fees, customs duties, PPN tax, breakup line types |
| `performance/v1` | `beckn:Performance.performanceAttributes` | AWB, booking reference, pickup slot, tracking URL, rider/driver identity (licence numbers via addendum pack), delivery proof, POD, temperature readings, SLA adherence, state machine reference |
| `contract/v1` | `beckn:Contract.contractAttributes` | Confirmed shipment terms, FWA reference, billing NPWP/NIB, credit terms, eKYC form reference, Faktur Pajak reference, POD signatory, parent contract reference |
| `commitment/v1` | `beckn:Commitment.commitmentAttributes` | Line identifiers, resource references, special handling instructions, per-line quantities |
| `tracking/v1` | `beckn:Tracking.trackingAttributes` | Live GPS, AWB URL, WebSocket, webhook |
| `performance-states/v1` | (canonical enum, not an attachment) | 10 state machine definitions: hyperlocal, parcel (P2P / P2H2P / P2H2H2P), freight, warehouse, Ro-Ro, cross-border, reverse |
| `participant-logistics/v1` | `beckn:Participant.participantAttributes` (as addendum) | Thin addendum to `core/participant/v1`: PPJK customs-broker licence, Indonesian driver SIM fields |

## Cross-sector packs used by logistics (Layer 4 — in `../core/`)

Logistics does not redeclare these. Core packs apply directly:

| Core pack | Used for |
|---|---|
| `core/address/v1` | Indonesian address subdivisions |
| `core/identity/v1` | Business identity (NPWP, NIB, PKP) |
| `core/localization/v1` | Language / currency / timezone |
| `core/participant/v1` | Role taxonomy (including CONSIGNOR, CONSIGNEE, FORWARDER, CARRIER, DRIVER, CUSTOMS_BROKER), address hierarchy with accessibility, authorised signatory — see `participant-logistics/v1` here for the licence-field addendum |
| `core/payment/v1` | All payment method declarations — rails, COD (including runtime fields), credit terms, refunds, invoices, processing fees. Offer-level COD policy (OTP required, denominations) lives in `logistics/offer/v1` |
| `core/product/v1` | Product metadata (brand, model, country of origin) |
| `core/rating/v1` | Rating input for LSPs |
| `core/raise/v1` | Network dispute escalation payloads |
| `core/reconcile/v1` | Settlement reconciliation — includes COD remittance batch fields |
| `core/support/v1` | Support tickets |
| `core/tax/v1` | PPN, PPnBM, PPh withholding |

## History

- **v0.5.2** — Unified into `ion-network`. The previous standalone `ion-logistics` repo contained its own `payment`, `rating`, `support`, `participant` packs; those have been dropped. Cross-sector primitives from them were promoted into `core/payment`, `core/rating`, `core/support`, `core/participant`. Logistics-only fields (COD fraud controls, PPJK licence, driver SIM) landed in `logistics/offer` and `logistics/participant-logistics` respectively.

## Logistics service availability model

Capacity is not transmitted continuously over the network. The BPP manages capacity internally. What the BPP publishes is a capability-and-availability signal:

```yaml
availability:
  status: AVAILABLE | CONSTRAINED | UNAVAILABLE | SCHEDULED_ONLY
  nextAvailableAt: date-time     # for constrained/scheduled
  operatingWindow: object         # days and hours when bookings are accepted
  selectRequired: boolean         # true if firm quote needs /select
```

For capacity-constrained offerings (air cargo, inter-island ferry, ocean freight), firm capacity confirmation happens at `/select` — the catalog declares availability intent; `/select` confirms for the specific shipment.

## Spine-specific attributes

Spine-specific attributes (cold-chain handling, customs documentation, vehicle-as-resource for Ro-Ro, inventory lifecycle for warehouse) are conditional fields within the relevant pack. They are not separate category packs. Each pack's README documents which fields apply to which spines.

## Rate logic in catalog vs firm quote in `/select`

The catalog carries rate **logic** — zone definitions, weight tiers, rate formulas, surcharge rules. It does not carry per-shipment rates. Firm rates for a specific pickup-drop-weight-mode combination are returned via `/on_select` in response to a BAP `/select` request. This is how BAPs can rank providers (using catalog rate logic) while honouring per-shipment pricing dynamics.
