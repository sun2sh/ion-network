# Changelog

All changes to the ION Network Specification are documented here.

Format: `v{major}.{minor}.{patch}` — `{major}` for breaking changes, `{minor}` for new APIs or fields, `{patch}` for fixes and clarifications.

---

## v0.2.0 — In Development

**Target:** Coming weeks — watch this repo for the release tag.

### Adding
- `/reconcile` + `/on_reconcile` — settlement reconciliation flow. ION Central-orchestrated. BPP declares settlement terms at confirm; reconciliation runs after the basis event (delivery, shipment, or return window expiry).
- `/support` + `/on_support` — RaisedMatter (dispute and support ticket) flow. Consumer raises via BAP; routed to BPP with SLA tracking by ION Central.
- `/rate` + `/on_rate` — post-fulfilment rating. Consumer rates seller; seller may rate consumer. Bidirectional in Mobility sector.
- `/track` + `/on_track` — real-time tracking URL handoff. BPP returns tracking URL; BAP embeds or links. Used for live logistics and Mobility GPS.
- YAML specs for: B2C Subscription (Trade), B2B Wholesale (Trade), Logistics domestic surface, Logistics hyperlocal spot booking.

### Spec files added in v0.2.0
- `specs/A_B2C_SUB_Grocery_MealKit.yaml`
- `specs/A_B2B_WHL_FMCG_GudangAda.yaml`
- `specs/B01_CAT_Logistics_JNERegular.yaml`
- `specs/B01_HYPER_Logistics_GoKilat.yaml`

---

## v0.1.0-draft — Current release

**Released:** April 2026  
**Git tag:** `v0.1.0-draft`

### APIs covered
- `/discover` + `/on_discover`
- `/select` + `/on_select`
- `/init` + `/on_init`
- `/confirm` + `/on_confirm`
- `/status` + `/on_status`
- `/update` + `/on_update`
- `/cancel` + `/on_cancel`

### Spec files
- `specs/A01_B2C_MTO_FoodQSR_DominosJakarta.yaml` — Food & QSR, multi-FC brand, composed resource
- `specs/A02_B2C_SF_Grocery_IndomieToko.yaml` — Grocery / FMCG, BPOM MD, halal, allergens
- `specs/A03_B2C_SF_Fashion_BatikKeris.yaml` — Fashion / Apparel, size variants with measurements
- `specs/A04_B2C_SF_Electronics_SamsungA55.yaml` — Electronics, POSTEL, warranty, TKDN
- `specs/A05_B2C_SF_Beauty_WardahLipCream.yaml` — Beauty, BPOM NA, shade variants
- `specs/A07_B2C_SF_Agritech_BerasPandanWangi.yaml` — Agritech, Kementan PD, PPN-exempt

### Reference documents
- `docs/ION_Sector_A_Trade.md` — Trade sector model v1.0
- `docs/ION_Trade_Dictionary.xlsx` — 126 finalised Trade fields
- `docs/ION_Atlas_Developer_Orientation.md` — Atlas concept and governance
- `errors/ion_error_registry.json` — 18 error codes

### Known scope boundaries in v0.1.0
The following are defined conceptually in the Trade Model and Dictionary but not yet specced as API flows. They land in v0.2.0:
- Settlement reconciliation (`/reconcile`)
- Dispute and support (`/support` — RaisedMatter)
- Post-fulfilment rating (`/rate`)
- Real-time tracking (`/track`)

---

## v0.0.1 — Internal working draft

**Released:** April 2026 (internal)

Initial field mapping, sector model, and Dominos catalog proof of concept. Not published.
