# ION Layer Model

ION composes with Beckn Protocol in five distinct layers. Knowing which layer a given rule, endpoint, or field belongs to is the single most useful piece of orientation for anyone building on ION. This document is the authoritative explanation.

If you are a trade BPP looking up a cancellation policy field, you care about Layer 4 and Layer 5. If you are implementing the `/raise` endpoint, you care about Layer 3. If you are reconciling your overall conformance with the spec, you care about all five.

---

## The five layers

| Layer | What it is | Where it lives | Example content |
|---|---|---|---|
| **L1 — Beckn core** | Upstream Beckn Protocol v2.0.0. Transport, object model, and the native `*Attributes` extension slots. Never forked. | External: <https://github.com/beckn/protocol-specifications-v2> | `Provider`, `Offer`, `Offer.offerAttributes` slot, `/select` endpoint, ACK/callback pattern |
| **L2 — ION network policy profile** | Policy overlay on Beckn. Rules that apply to every ION participant regardless of sector. Not a schema — a rulebook. | `schema/core/v2/api/v2.0.0/ion.yaml` | Ed25519 signing required, NPWP mandatory, data-residency Indonesia, allowed payment rails, mandatory action sets |
| **L3 — ION protocol endpoint extensions** | New endpoints ION adds to Beckn. Same Context, same signing, same ACK pattern — just extra endpoints. | `schema/core/v2/api/v2.0.0/ion-endpoints.yaml` | `/raise`, `/on_raise`, `/raise_status`, `/on_raise_status`, `/raise_details`, `/on_raise_details`, `/reconcile`, `/on_reconcile` |
| **L4 — ION core attribute packs** | Cross-sector field packs that mount onto Beckn's `*Attributes` slots. Same in every sector. | `schema/extensions/core/*/v1/` | `address/v1` (provinsiCode, RT/RW), `identity/v1` (NPWP, NIB), `payment/v1` (QRIS, BI-FAST, COD, credit terms), `tax/v1` (PPN/PPnBM/PPh), `participant/v1` (roles) |
| **L5 — ION sector attribute packs** | Sector-specific field packs that mount onto Beckn's `*Attributes` slots. Apply only within one sector. | `schema/extensions/{trade,logistics,…}/*/v1/` | Trade: `cancellationPolicy`, `returnPolicy`. Logistics: `serviceLevel`, `transportMode`, `routingTopology` |

---

## The extension contract (one rule)

Every ION attribute pack (L4 and L5) carries this annotation on its top-level schema:

```yaml
x-beckn-attaches-to: Offer.offerAttributes
```

That is the extension contract. It names exactly which Beckn object and which slot the pack mounts onto. ION does not invent new top-level objects. It does not fork Beckn. Every field ION adds lives under a Beckn-native `*Attributes` slot that Beckn's own schema already declared as an extension point.

Examples:

```yaml
# core/address/v1/attributes.yaml
x-beckn-attaches-to: Address (as ionAddressAttributes)

# core/payment/v1/attributes.yaml
x-beckn-attaches-to: Settlement.settlementAttributes

# trade/offer/v1/attributes.yaml
x-beckn-attaches-to: Offer.offerAttributes

# logistics/performance/v1/attributes.yaml
x-beckn-attaches-to: Performance.performanceAttributes
```

If you see a field and wonder "is this Beckn or ION?", open the pack it came from and read the `x-beckn-attaches-to` line. If it's in `schema/extensions/core/*`, it's L4. If it's in `schema/extensions/{trade,logistics,…}/*`, it's L5.

---

## Composition rule

For a given sector transaction, a valid payload conforms to:

- **L1** — the Beckn 2.0.0 core transport & schema
- **L2** — the ION network profile (`ion.yaml`)
- **L3** — the ION endpoint extensions (`ion-endpoints.yaml`) where applicable
- **L4** — all ION core attribute packs that apply to the Beckn objects in this payload
- **L5** — the sector-specific packs for whichever sector this transaction belongs to

In practice: if you are a trade BPP sending `on_select`, your `quote.breakup[i].considerationAttributes` contains the **union** of `core/tax/v1` fields (L4) and `trade/consideration/v1` fields (L5). Both attach to the same Beckn `considerationAttributes` slot; they coexist because they define disjoint field sets.

---

## Why this layering matters

A concrete example clarifies the point. Consider a logistics BPP publishing a catalog.

The `Offer.offerAttributes` for a logistics offer carries:

- `cancellationPolicy: ion://policy/cancel.standard.until-dispatched` — an **L4** field, actually defined in `trade/offer/v1` but (cross-sector) reused wherever cancellation applies
- `serviceLevel: NEXT_DAY` — an **L5** field, only meaningful for logistics, defined in `logistics/offer/v1`
- `rateLogic: TIERED_BY_ZONE_AND_WEIGHT` — **L5**, logistics-only
- `codVerifiedReceiptOtp: REQUIRED` — **L5**, logistics-only (COD fraud control is a logistics offer-time concern, not a cross-sector one)
- An offer in IDR — the **L2** default currency (network-wide ION policy)
- Published to an ION subscriber ID signed with Ed25519 — **L1 + L2** (Beckn signing, ION-specified algorithm)

One payload, five layers cooperating. Knowing which layer a field comes from tells you where to change it, who ratifies changes to it, and whether a change is sector-local or network-wide.

---

## A common source of confusion: endpoint extension vs attribute extension

Both L3 and L4/L5 are "extensions to Beckn." They are **not** the same thing.

- **L3 — endpoint extension** adds a whole new API endpoint. `/raise` is a new URL on the wire that Beckn-only implementations do not serve. Adding a new L3 endpoint is a significant network-level change.
- **L4 / L5 — attribute extension** adds fields under a Beckn-native `*Attributes` slot. `ionAddressAttributes.provinsiCode` is not a new endpoint — it is additional data carried inside an existing Beckn request body. Beckn-conformant implementations that do not know about it will simply ignore it (per Beckn's `*Attributes` design); ION-conformant implementations enforce it.

When someone asks "is this Beckn or ION?", half the time they are actually asking "is this a new endpoint or a new field?" The two questions have the same answer space but different implications. L3 requires a new route in your HTTP handler. L4/L5 requires a new field in your request validator.

---

## Where each layer is ratified

| Layer | Ratified by | Change cadence |
|---|---|---|
| L1 | Beckn Council (upstream) | External — ION tracks Beckn releases |
| L2 | ION Council | 90-day notice for profile changes |
| L3 | ION Council | Rare — adding endpoints is a major event |
| L4 | ION Council | 90-day notice; version pack if breaking |
| L5 | ION sector working group → ION Council | Per-sector cadence; 90-day notice |

ION uses a single-version running model: the Council ratifies new versions with 90 days of notice; no per-seller version pinning.

---

## Where to look next

- For the conformance checklist that implementations must pass, see `ION_Beckn_Conformance.md`.
- For onboarding, signing, and auth, see `ION_Onboarding_and_Auth.md`.
- For the Trade sector, see `ION_Sector_A_Trade.md` and `ION_Developer_Orientation.md`.
- For the Logistics sector, see `ION_Sector_B_Logistics.md` and `ION_Sector_B_Logistics.md`.

---

*ION Layer Model — v0.5.2-draft*

---

## See also

- **New to ION?** [`ION_Start_Here.md`](ION_Start_Here.md)
- **Glossary?** [`ION_Glossary.md`](ION_Glossary.md)
- **Conformance checklist?** [`ION_Beckn_Conformance.md`](ION_Beckn_Conformance.md)
- **Cross-sector concepts?** [`ION_Developer_Orientation.md`](ION_Developer_Orientation.md)
