# ION First Transaction — Annotated Walkthrough (Corrected)

**A realistic end-to-end transaction with every message explained field-by-field — every payload validates against `beckn.yaml` v2.0.0 + ION packs.**

If you've read [`ION_Start_Here.md`](ION_Start_Here.md) and [`ION_Glossary.md`](ION_Glossary.md), you have the concepts. This doc shows them in action — and every JSON payload here conforms exactly to Beckn's core object shapes.

> **Companion doc:** [`ION_First_Transaction_Food.md`](ION_First_Transaction_Food.md) walks through a different sector pair (food order + hyperlocal delivery) and explicitly covers the **linkage mechanism** between two ION transactions via `linkedContractId` and `parentContractReference`. Read this doc first for the canonical Beckn flow; read the food doc next to see how multi-BPP coordination works in ION.

---

## The scenario

A consumer uses BuyerApp Indonesia (a BAP) to order a pair of running shoes from SellerApp Indonesia (a BPP — merchant seller) in Jakarta. LogisticsApp Indonesia (another BPP — LSP) handles delivery to the buyer in Surabaya.

Participants:
- **Buyer:** Sari Wijayanti, living in Surabaya.
- **BAP:** BuyerApp Indonesia (app she's using).
- **Seller BPP:** SellerApp Indonesia — a shoe merchant in Jakarta.
- **Logistics BPP:** LogisticsApp Indonesia — Indonesian parcel carrier.

Three transactions actually happen:
1. **Trade transaction** — BuyerApp Indonesia ↔ SellerApp Indonesia for the shoes
2. **Logistics transaction** — BuyerApp Indonesia ↔ LogisticsApp Indonesia for delivery
3. **Child coordination** — the two transactions reference each other by contract ID

We'll walk through the Trade transaction in detail, then summarize the Logistics one.

---

## Two conformance rules you will see enforced throughout

**Rule 1 — Beckn shapes are not negotiable.** Every Beckn core object (`Contract`, `Commitment`, `Resource`, `Offer`, `Consideration`, `Settlement`, `Performance`, `Participant`, `Address`, `Context`) has a fixed shape defined in `beckn.yaml` v2.0.0. ION never adds top-level fields to any of these objects. Where ION needs to extend, it extends through the Beckn-native `*Attributes` slot (`resourceAttributes`, `offerAttributes`, `commitmentAttributes`, `considerationAttributes`, `settlementAttributes`, `performanceAttributes`, `participantAttributes`, `contractAttributes`).

In practical terms that means, for example, **Beckn's `Resource` has exactly three properties: `id`, `descriptor`, `resourceAttributes`.** Anything ION adds for a resource — quantity, availability, country of origin, halal status, dimensions, weight — lives inside `resourceAttributes`, never at the top of `Resource`.

**Rule 2 — One vocabulary per `*Attributes` bag.** Each `*Attributes` bag is a JSON-LD container (`Attributes` schema in Beckn requires `@context` and `@type` and is `additionalProperties: true` for the rest). The `@context` of any single bag is exactly one URL — and it MUST resolve to one of two roots:

- `https://schema.beckn.io/core/v2.0.0/` — Beckn's core transport vocabulary. Owned by Beckn Foundation.
- `https://schema.ion.id/{layer}/{pack}/{version}/` — ION's own vocabulary (all extension attributes, policies, states, error categories). Owned by ION Network.

Different bags in the same message can reference different ION packs (`resourceAttributes` carries `trade/resource/v1`, `considerationAttributes` carries `trade/consideration/v1`, etc.). What you cannot do is split one bag across two contexts — `@context` is a single string per `Attributes` object, not an array. To advertise the full set of vocabularies a message uses, populate `context.schemaContext` (the array on Beckn's `Context` object designed for exactly this purpose).

ION Central rejects messages carrying any other `@context` value at the protocol gate.

You will see both rules in action in every payload below.

---

## Phase 0 — Catalog discovery (happens continuously, not at order time)

Before any of this starts, SellerApp Indonesia and LogisticsApp Indonesia have already published their catalogs to the Catalog Discovery Service (CDS). BuyerApp Indonesia has subscribed.

SellerApp Indonesia's catalog publishes `Provider`, `Resource` (the SKUs it sells), and `Offer` (the terms — price, validity — under which those resources are available) as separate Beckn objects. The `Offer` references the resources via `resourceIds`.

A simplified view of one resource from the catalog:

```json
{
  "id": "SAI-RUN-AIRZOOM-42-BLK",
  "descriptor": { "name": "AirZoom Running Shoes — Size 42 Black" },
  "resourceAttributes": {
    "@context": "https://schema.ion.id/trade/resource/v1/",
    "@type": "ion:TradeResourceAttributes",
    "ion:availability": { "status": "IN_STOCK" },
    "ion:countryOfOrigin": "IDN",
    "ion:images": ["https://sellerapp.id/sku/SAI-RUN-AIRZOOM-42-BLK.jpg"],
    "ion:ageRestricted": false
  }
}
```

And the matching offer:

```json
{
  "id": "OFR-SAI-AIRZOOM-42-BLK-STD",
  "descriptor": { "name": "Standard price — AirZoom Size 42 Black" },
  "resourceIds": ["SAI-RUN-AIRZOOM-42-BLK"],
  "considerations": [
    {
      "id": "cons-tmpl-1",
      "status": { "code": "DRAFT" },
      "considerationAttributes": {
        "@context": "https://schema.ion.id/trade/consideration/v1/",
        "@type": "ion:TradeConsideration",
        "ion:price": { "value": 500000, "currency": "IDR" }
      }
    }
  ],
  "validity": { "start": "2026-04-25T00:00:00+07:00", "end": "2026-04-30T23:59:59+07:00" },
  "offerAttributes": {
    "@context": "https://schema.ion.id/trade/offer/v1/",
    "@type": "ion:TradeOffer",
    "ion:selectRequired": false,
    "ion:cancellationPolicy": "ion://policy/cancel.standard.until-dispatched",
    "ion:returnPolicy": "ion://policy/return.standard.14-days"
  }
}
```

Notice:
- `Resource` has exactly the three Beckn-native properties — `id`, `descriptor`, `resourceAttributes`. Nothing else at the top.
- `Offer.resourceIds` links the offer to its resources (this is the Beckn-mandated way for a commitment to find its offer at `/select` time).
- Domain-specific data lives in the appropriate `*Attributes` bag, each with one `@context` URL.
- ION-defined fields are prefixed `ion:` to distinguish them from Beckn-native terms inside the JSON-LD context.

---

## Phase 1 — Consumer taps "Buy"

Sari has browsed BuyerApp Indonesia's app, found the shoes (surfaced from the catalog), picked size 42 black, tapped **Add to cart** and then **Checkout**. She's entered her delivery address in Surabaya. Payment is via GoPay (e-wallet).

BuyerApp Indonesia (BAP) now needs to:
1. Lock in the seller's price and stock
2. Get a delivery quote
3. Lock in the whole order
4. Collect payment
5. Tell both BPPs to execute

This all happens in the next ~5 seconds.

---

## Phase 2 — BAP → Seller BPP: /select

Because `selectRequired: false` was declared in the catalog, BuyerApp Indonesia could technically skip `/select` and go straight to `/init`. But it still calls `/select` for two reasons:
- To verify the price hasn't changed since the catalog was published
- To verify stock is still available right now

### Request: `POST https://sellerapp.id/api/beckn/select`

```json
{
  "context": {
    "domain": "retail",
    "action": "select",
    "version": "2.0.0",
    "bapId": "buyerapp.id",
    "bapUri": "https://buyerapp.id/api/beckn",
    "bppId": "sellerapp.id",
    "bppUri": "https://sellerapp.id/api/beckn",
    "transactionId": "8743f2a0-4b1c-4d8e-9a23-7f6b8c9d0e1a",
    "messageId": "ab91c0d4-3e7f-4a2b-8c5d-1e9f0a2b3c4d",
    "timestamp": "2026-04-25T10:30:12.445Z",
    "ttl": "PT30S",
    "schemaContext": [
      "https://schema.beckn.io/core/v2.0.0/",
      "https://schema.ion.id/trade/resource/v1/",
      "https://schema.ion.id/trade/offer/v1/"
    ]
  },
  "message": {
    "contract": {
      "commitments": [
        {
          "id": "cmt-1",
          "status": { "code": "DRAFT" },
          "offer": {
            "id": "OFR-SAI-AIRZOOM-42-BLK-STD",
            "resourceIds": ["SAI-RUN-AIRZOOM-42-BLK"]
          },
          "resources": [
            {
              "id": "SAI-RUN-AIRZOOM-42-BLK",
              "descriptor": { "name": "AirZoom Running Shoes — Size 42 Black" },
              "resourceAttributes": {
                "@context": "https://schema.ion.id/trade/resource/v1/",
                "@type": "ion:TradeResourceAttributes",
                "ion:quantity": { "value": 1, "unit": "piece" }
              }
            }
          ]
        }
      ]
    }
  }
}
```

What each field does:

| Field | Purpose |
|---|---|
| `context.domain` | Which sector — `retail` for trade transactions |
| `context.action` | Which endpoint is being invoked (must match URL) |
| `context.version` | MUST be `"2.0.0"` (Beckn's `Context.version` is `const: "2.0.0"`) |
| `context.bapId`/`bppId` | Registered subscriber IDs on the ION Registry |
| `context.transactionId` | Beckn requires UUID format. Same across select/init/confirm. |
| `context.messageId` | Beckn requires UUID format. Unique for THIS specific message. |
| `context.timestamp` | When BAP generated the message (RFC3339) |
| `context.ttl` | How long this message is valid (ISO 8601 duration — 30 seconds here) |
| `context.schemaContext` | Beckn-native field for declaring all JSON-LD vocabularies this message uses. Replaces any `@context` on `context` itself (`Context` has no `@context` property). |
| `message.contract.commitments` | Beckn `Contract.commitments` — array, minItems 1. |
| `commitment.status` | Required by Beckn. `DRAFT` until BPP commits at `/on_confirm`. |
| `commitment.offer` | Required by Beckn (with `id` + `resourceIds`). Links the commitment to the catalog offer. |
| `commitment.resources[*].id` | Required by Beckn — matches a resource ID from the catalog. |
| `resourceAttributes.ion:quantity` | ION trade pack puts `quantity` inside `resourceAttributes` (Beckn's `Resource` schema has no top-level `quantity`). |

Also required but not shown: the `Authorization: Signature ...` HTTP header with Ed25519 signature. See [`ION_Onboarding_and_Auth.md`](ION_Onboarding_and_Auth.md) for the exact signing format.

**Beckn shape check:** the only top-level keys under `Contract` here are `commitments`. Under each commitment, only `id`, `status`, `offer`, `resources`. Under each resource, only `id` and `resourceAttributes`. Everything else lives inside an `*Attributes` bag with its own `@context` and `@type`.

### Synchronous response: Ack

SellerApp Indonesia's server validates the signature, checks the message is well-formed, and immediately returns:

```json
{
  "message": { "ack": { "status": "ACK" } },
  "counterSignature": "Signature keyId=\"sellerapp.id|key-2026-04|ed25519\",algorithm=\"ed25519\",..."
}
```

This is the **Ack response** — SellerApp Indonesia has received the request and queued it for processing. **The actual business response comes via callback**, not in this response.

The `counterSignature` is SellerApp Indonesia signing their Ack, proving they received the request. MANDATORY — ION Central rejects Acks without it.

### Async callback: `POST https://buyerapp.id/api/beckn/on_select`

A few hundred milliseconds later, SellerApp Indonesia calls BuyerApp Indonesia back:

```json
{
  "context": {
    "domain": "retail",
    "action": "on_select",
    "version": "2.0.0",
    "bapId": "buyerapp.id",
    "bapUri": "https://buyerapp.id/api/beckn",
    "bppId": "sellerapp.id",
    "bppUri": "https://sellerapp.id/api/beckn",
    "transactionId": "8743f2a0-4b1c-4d8e-9a23-7f6b8c9d0e1a",
    "messageId": "cd7e1402-9b3a-4c8d-bf5e-2a1c3d4e5f6a",
    "timestamp": "2026-04-25T10:30:12.702Z",
    "ttl": "PT30S",
    "requestDigest": { "digest": "BLAKE-512=hZ8w...kQ==" },
    "schemaContext": [
      "https://schema.beckn.io/core/v2.0.0/",
      "https://schema.ion.id/trade/resource/v1/",
      "https://schema.ion.id/trade/consideration/v1/",
      "https://schema.ion.id/core/tax/v1/"
    ]
  },
  "message": {
    "contract": {
      "status": { "code": "DRAFT" },
      "commitments": [
        {
          "id": "cmt-1",
          "status": { "code": "DRAFT" },
          "offer": {
            "id": "OFR-SAI-AIRZOOM-42-BLK-STD",
            "resourceIds": ["SAI-RUN-AIRZOOM-42-BLK"]
          },
          "resources": [
            {
              "id": "SAI-RUN-AIRZOOM-42-BLK",
              "descriptor": { "name": "AirZoom Running Shoes — Size 42 Black" },
              "resourceAttributes": {
                "@context": "https://schema.ion.id/trade/resource/v1/",
                "@type": "ion:TradeResourceAttributes",
                "ion:quantity": { "value": 1, "unit": "piece" },
                "ion:availability": { "status": "IN_STOCK" },
                "ion:countryOfOrigin": "IDN"
              }
            }
          ]
        }
      ],
      "consideration": [
        {
          "id": "cons-1",
          "status": { "code": "DRAFT" },
          "considerationAttributes": {
            "@context": "https://schema.ion.id/trade/consideration/v1/",
            "@type": "ion:TradeConsideration",
            "ion:price": { "value": 555000, "currency": "IDR" },
            "ion:breakup": [
              { "ion:type": "ITEM", "ion:amount": { "value": 500000, "currency": "IDR" } },
              { "ion:type": "PPN", "ion:amount": { "value": 55000, "currency": "IDR" }, "ion:note": "Applicable rate per current DJP regulation" }
            ]
          }
        }
      ]
    }
  }
}
```

Now BuyerApp Indonesia knows:
- Stock is available (`ion:availability.status: IN_STOCK`)
- Price is confirmed (500,000 IDR + 55,000 PPN = 555,000 IDR)
- Contract is in `DRAFT` status (not committed yet)

Note: Contract status is `DRAFT` (4-value enum: `DRAFT/ACTIVE/CANCELLED/COMPLETE`). Commitment status is `DRAFT` (3-value enum: `DRAFT/ACTIVE/CLOSED` — see [`ION_Beckn_Conformance.md`](ION_Beckn_Conformance.md) §5 for why these differ).

**Beckn shape check on this callback:**
- `Contract.consideration` (singular field, type array) — yes, this is what Beckn calls it. Not `considerations`. (Compare with `Offer.considerations`, plural — different field on a different object.)
- `Contract.settlements` (plural, array) — not present yet, will appear at `/on_init`.
- Each `consideration[*]` has `id`, `status`, `considerationAttributes` only. No top-level `amount` — the price lives inside `considerationAttributes`.

---

## Phase 3 — BAP → Logistics BPP: /select (for delivery)

In parallel with (or right after) the shoe `/select`, BuyerApp Indonesia asks LogisticsApp Indonesia for a delivery quote.

```json
{
  "context": {
    "domain": "logistics",
    "action": "select",
    "version": "2.0.0",
    "bapId": "buyerapp.id",
    "bapUri": "https://buyerapp.id/api/beckn",
    "bppId": "logisticsapp.id",
    "bppUri": "https://logisticsapp.id/api/beckn",
    "transactionId": "4b9c2100-7e3d-4f1a-8c6b-9d5e0a1b2c3d",
    "messageId": "f0a1b2c3-d4e5-4f67-89ab-cdef01234567",
    "timestamp": "2026-04-25T10:30:13.110Z",
    "ttl": "PT30S",
    "schemaContext": [
      "https://schema.beckn.io/core/v2.0.0/",
      "https://schema.ion.id/logistics/resource/v1/",
      "https://schema.ion.id/logistics/performance/v1/",
      "https://schema.ion.id/core/address/v1/"
    ]
  },
  "message": {
    "contract": {
      "commitments": [
        {
          "id": "cmt-logi-1",
          "status": { "code": "DRAFT" },
          "offer": {
            "id": "OFR-LAI-PARCEL-NEXTDAY",
            "resourceIds": ["shipment-sari-2026-04-25"]
          },
          "resources": [
            {
              "id": "shipment-sari-2026-04-25",
              "descriptor": { "name": "Parcel — AirZoom shoes order ORD-SAI-...-1234" },
              "resourceAttributes": {
                "@context": "https://schema.ion.id/logistics/resource/v1/",
                "@type": "ion:LogisticsShipmentAttributes",
                "ion:quantity": { "value": 1, "unit": "package" },
                "ion:serviceType": "PARCEL",
                "ion:weight": { "value": 1.2, "unit": "kilogram" },
                "ion:dimensions": { "length": 35, "width": 25, "height": 15, "unit": "centimeter" },
                "ion:declaredValue": { "value": 555000, "currency": "IDR" }
              }
            }
          ]
        }
      ],
      "performance": [
        {
          "id": "perf-logi-1",
          "status": { "code": "DRAFT" },
          "commitmentIds": ["cmt-logi-1"],
          "performanceAttributes": {
            "@context": "https://schema.ion.id/logistics/performance/v1/",
            "@type": "ion:LogisticsPerformanceAttributes",
            "ion:stops": [
              {
                "ion:type": "PICKUP",
                "ion:address": {
                  "streetAddress": "Jl. Cendrawasih 15",
                  "addressLocality": "Jakarta Pusat",
                  "postalCode": "10710",
                  "addressCountry": "ID"
                },
                "ion:subdivisions": {
                  "@context": "https://schema.ion.id/core/address/v1/",
                  "@type": "ion:AddressSubdivisions",
                  "ion:provinsiCode": "BPS-31",
                  "ion:kabupatenCode": "3173",
                  "ion:kecamatan": "Menteng",
                  "ion:kelurahan": "Cikini",
                  "ion:rt": "02",
                  "ion:rw": "05"
                }
              },
              {
                "ion:type": "DROPOFF",
                "ion:address": {
                  "streetAddress": "Jl. Pemuda 89",
                  "addressLocality": "Surabaya",
                  "postalCode": "60271",
                  "addressCountry": "ID"
                },
                "ion:subdivisions": {
                  "@context": "https://schema.ion.id/core/address/v1/",
                  "@type": "ion:AddressSubdivisions",
                  "ion:provinsiCode": "BPS-35",
                  "ion:kabupatenCode": "3578",
                  "ion:kecamatan": "Genteng",
                  "ion:kelurahan": "Embong Kaliasin",
                  "ion:rt": "04",
                  "ion:rw": "02"
                }
              }
            ]
          }
        }
      ]
    }
  }
}
```

Key things to notice:

- **Different `transactionId`** — Trade and Logistics are separate transactions.
- `Contract.performance` is an array (per Beckn) — not a single object. Each performance has `id`, `status`, `commitmentIds` linking back to which commitments it executes, and a `performanceAttributes` bag.
- The Indonesian address hierarchy lives in a nested `ion:subdivisions` bag with its own `@context` pointing at `core/address/v1`. This is because Beckn's `Address` schema is `additionalProperties: false` — ION cannot add `provinsiCode` directly to it. The `core/address/v1` pack is therefore a reusable shape embedded inside other ION attribute bags (see the pack's own `attributes.yaml` for the full list of mount points).
- RT/RW are included because they're needed for last-mile delivery in Indonesia.

LogisticsApp Indonesia responds via `/on_select` callback with a binding quote:

```json
{
  "context": {
    "domain": "logistics",
    "action": "on_select",
    "version": "2.0.0",
    "bapId": "buyerapp.id",
    "bapUri": "https://buyerapp.id/api/beckn",
    "bppId": "logisticsapp.id",
    "bppUri": "https://logisticsapp.id/api/beckn",
    "transactionId": "4b9c2100-7e3d-4f1a-8c6b-9d5e0a1b2c3d",
    "messageId": "0a1b2c3d-4e5f-4607-8912-3456789abcde",
    "timestamp": "2026-04-25T10:30:13.480Z",
    "ttl": "PT30S",
    "requestDigest": { "digest": "BLAKE-512=mZ4...rA==" },
    "schemaContext": [
      "https://schema.beckn.io/core/v2.0.0/",
      "https://schema.ion.id/logistics/consideration/v1/",
      "https://schema.ion.id/logistics/performance/v1/"
    ]
  },
  "message": {
    "contract": {
      "status": { "code": "DRAFT" },
      "commitments": [
        {
          "id": "cmt-logi-1",
          "status": { "code": "DRAFT" },
          "offer": {
            "id": "OFR-LAI-PARCEL-NEXTDAY",
            "resourceIds": ["shipment-sari-2026-04-25"]
          },
          "resources": [
            {
              "id": "shipment-sari-2026-04-25",
              "descriptor": { "name": "Parcel — AirZoom shoes order ORD-SAI-...-1234" },
              "resourceAttributes": {
                "@context": "https://schema.ion.id/logistics/resource/v1/",
                "@type": "ion:LogisticsShipmentAttributes",
                "ion:quantity": { "value": 1, "unit": "package" }
              }
            }
          ]
        }
      ],
      "consideration": [
        {
          "id": "cons-logi-1",
          "status": { "code": "DRAFT" },
          "considerationAttributes": {
            "@context": "https://schema.ion.id/logistics/consideration/v1/",
            "@type": "ion:LogisticsConsideration",
            "ion:price": { "value": 18000, "currency": "IDR" },
            "ion:breakup": [
              { "ion:type": "FREIGHT_BASE", "ion:amount": { "value": 15000, "currency": "IDR" } },
              { "ion:type": "PPN", "ion:amount": { "value": 1650, "currency": "IDR" } },
              { "ion:type": "FUEL_SURCHARGE", "ion:amount": { "value": 1350, "currency": "IDR" } }
            ]
          }
        }
      ],
      "performance": [
        {
          "id": "perf-logi-1",
          "status": { "code": "DRAFT" },
          "commitmentIds": ["cmt-logi-1"],
          "performanceAttributes": {
            "@context": "https://schema.ion.id/logistics/performance/v1/",
            "@type": "ion:LogisticsPerformanceAttributes",
            "ion:estimatedDeliveryTime": "2026-04-27T18:00:00+07:00",
            "ion:quoteValidityWindow": "PT30M"
          }
        }
      ]
    }
  }
}
```

Delivery cost: 18,000 IDR. Estimated delivery: April 27 by 6pm. Quote valid for 30 minutes.

---

## Phase 4 — BAP → both BPPs: /init

BuyerApp Indonesia now has both prices. Total to collect: 555,000 (shoes) + 18,000 (delivery) = 573,000 IDR.

BuyerApp Indonesia calls `/init` on both BPPs in parallel.

### `/init` to SellerApp Indonesia (seller)

The request echoes back the quote from `/on_select`, adding the buyer and seller `Participant` records (for tax jurisdiction computation, NPWP/NIB checks, and contact details):

```json
{
  "context": {
    "domain": "retail",
    "action": "init",
    "version": "2.0.0",
    "bapId": "buyerapp.id",
    "bapUri": "https://buyerapp.id/api/beckn",
    "bppId": "sellerapp.id",
    "bppUri": "https://sellerapp.id/api/beckn",
    "transactionId": "8743f2a0-4b1c-4d8e-9a23-7f6b8c9d0e1a",
    "messageId": "1f2e3d4c-5b6a-4798-bd0e-fedcba987654",
    "timestamp": "2026-04-25T10:30:14.100Z",
    "ttl": "PT30S",
    "schemaContext": [
      "https://schema.beckn.io/core/v2.0.0/",
      "https://schema.ion.id/core/participant/v1/",
      "https://schema.ion.id/core/identity/v1/"
    ]
  },
  "message": {
    "contract": {
      "commitments": [ /* same as on_select */ ],
      "consideration": [ /* same as on_select */ ],
      "participants": [
        {
          "id": "bapi-user-sari-wijayanti",
          "participantAttributes": {
            "@context": "https://schema.ion.id/core/participant/v1/",
            "@type": "ion:ParticipantAttributes",
            "ion:role": "BUYER",
            "ion:contactName": "Sari Wijayanti",
            "ion:phoneProxy": "+62-xxx-xxx-7832"
          }
        },
        {
          "id": "sellerapp.id.merchant.sai-001",
          "participantAttributes": {
            "@context": "https://schema.ion.id/core/participant/v1/",
            "@type": "ion:ParticipantAttributes",
            "ion:role": "SELLER",
            "ion:npwp": "00.000.000.0-000.000",
            "ion:nibNumber": "1234567890123",
            "ion:pkpStatus": "REGISTERED"
          }
        }
      ]
    }
  }
}
```

Notes on the Participant shape:

- Beckn `Participant` has `id`, `descriptor`, `participantAttributes`. There is no top-level `role` on `Participant` — role lives inside `participantAttributes` per the `core/participant/v1` pack.
- NPWP, NIB, PKP status — all the Indonesian regulatory identifiers — live in `participantAttributes` under the `core/participant/v1` vocabulary.
- The phone number is a proxy (privacy preserved).

SellerApp Indonesia responds via `/on_init`:

```json
{
  "context": {
    "domain": "retail",
    "action": "on_init",
    "version": "2.0.0",
    "bapId": "buyerapp.id",
    "bapUri": "https://buyerapp.id/api/beckn",
    "bppId": "sellerapp.id",
    "bppUri": "https://sellerapp.id/api/beckn",
    "transactionId": "8743f2a0-4b1c-4d8e-9a23-7f6b8c9d0e1a",
    "messageId": "2a3b4c5d-6e7f-4081-9234-56789abcdef0",
    "timestamp": "2026-04-25T10:30:14.380Z",
    "ttl": "PT30S",
    "requestDigest": { "digest": "BLAKE-512=pP9...sX==" },
    "schemaContext": [
      "https://schema.beckn.io/core/v2.0.0/",
      "https://schema.ion.id/core/payment/v1/"
    ]
  },
  "message": {
    "contract": {
      "status": { "code": "DRAFT" },
      "commitments": [
        { "id": "cmt-1", "status": { "code": "DRAFT" }, "offer": { "id": "OFR-SAI-AIRZOOM-42-BLK-STD", "resourceIds": ["SAI-RUN-AIRZOOM-42-BLK"] }, "resources": [ { "id": "SAI-RUN-AIRZOOM-42-BLK" } ] }
      ],
      "settlements": [
        {
          "id": "settle-sai-20260425-a1",
          "status": { "code": "DRAFT" },
          "considerationId": "cons-1",
          "settlementAttributes": {
            "@context": "https://schema.ion.id/core/payment/v1/",
            "@type": "ion:PaymentDeclaration",
            "ion:paymentRail": "E_WALLET",
            "ion:paymentMethod": "GOPAY",
            "ion:paymentRequestUrl": "https://sellerapp.id/pay/sai-20260425-a1",
            "ion:virtualAccount": "8809123456789012"
          }
        }
      ]
    }
  }
}
```

Now BuyerApp Indonesia has the payment link.

**Beckn shape check:** `Contract.settlements` is plural and an array. Each `Settlement` has `id`, `status`, `considerationId`, `settlementAttributes` only — these are exactly Beckn's four properties for `Settlement`. The payment-rail and method specifics live inside `settlementAttributes` carrying `core/payment/v1`.

---

## Phase 5 — Consumer pays

Sari taps "Pay" in BuyerApp Indonesia. BuyerApp Indonesia opens GoPay. GoPay processes the payment. BuyerApp Indonesia gets a callback from GoPay confirming payment received.

This happens outside ION — payment processing is between BuyerApp Indonesia, GoPay, and SellerApp Indonesia's payment receiving account. ION does not move money; it only carries metadata.

---

## Phase 6 — BAP → both BPPs: /confirm

With payment confirmed, BuyerApp Indonesia finalizes both transactions.

### `/confirm` to SellerApp Indonesia

```json
{
  "context": {
    "domain": "retail",
    "action": "confirm",
    "version": "2.0.0",
    "bapId": "buyerapp.id",
    "bapUri": "https://buyerapp.id/api/beckn",
    "bppId": "sellerapp.id",
    "bppUri": "https://sellerapp.id/api/beckn",
    "transactionId": "8743f2a0-4b1c-4d8e-9a23-7f6b8c9d0e1a",
    "messageId": "3b4c5d6e-7f80-4192-a345-6789abcdef01",
    "timestamp": "2026-04-25T10:30:45.502Z",
    "ttl": "PT30S",
    "schemaContext": [
      "https://schema.beckn.io/core/v2.0.0/",
      "https://schema.ion.id/core/payment/v1/"
    ]
  },
  "message": {
    "contract": {
      "commitments": [
        { "id": "cmt-1", "status": { "code": "ACTIVE" }, "offer": { "id": "OFR-SAI-AIRZOOM-42-BLK-STD", "resourceIds": ["SAI-RUN-AIRZOOM-42-BLK"] }, "resources": [ { "id": "SAI-RUN-AIRZOOM-42-BLK" } ] }
      ],
      "settlements": [
        {
          "id": "settle-sai-20260425-a1",
          "status": { "code": "DRAFT" },
          "considerationId": "cons-1",
          "settlementAttributes": {
            "@context": "https://schema.ion.id/core/payment/v1/",
            "@type": "ion:PaymentDeclaration",
            "ion:paymentStatus": "PAID",
            "ion:paymentReceivedAt": "2026-04-25T10:30:45.221Z",
            "ion:paymentProviderReference": "GOPAY-TXN-2026-04-25-98765432"
          }
        }
      ]
    }
  }
}
```

A note on the `commitments` block above: Beckn `Contract` has `required: [commitments]`, so every message that carries a `contract` MUST include `commitments` even when the substantive change is on `settlements`. The convention is to include each commitment by `id` plus its `status`, `offer`, and a thin `resources` array with just `id` (re-stating the identity, not the full body). That keeps the message Beckn-conformant without bloat.

SellerApp Indonesia responds with `/on_confirm`:

```json
{
  "context": {
    "domain": "retail",
    "action": "on_confirm",
    "version": "2.0.0",
    "bapId": "buyerapp.id",
    "bapUri": "https://buyerapp.id/api/beckn",
    "bppId": "sellerapp.id",
    "bppUri": "https://sellerapp.id/api/beckn",
    "transactionId": "8743f2a0-4b1c-4d8e-9a23-7f6b8c9d0e1a",
    "messageId": "4c5d6e7f-8091-42a3-b456-789abcdef012",
    "timestamp": "2026-04-25T10:30:45.812Z",
    "ttl": "PT30S",
    "requestDigest": { "digest": "BLAKE-512=qQ0...tY==" },
    "schemaContext": [
      "https://schema.beckn.io/core/v2.0.0/",
      "https://schema.ion.id/trade/resource/v1/"
    ]
  },
  "message": {
    "contract": {
      "id": "ORD-SAI-2026-04-25-00001234",
      "status": { "code": "ACTIVE" },
      "commitments": [
        {
          "id": "cmt-1",
          "status": { "code": "ACTIVE" },
          "offer": {
            "id": "OFR-SAI-AIRZOOM-42-BLK-STD",
            "resourceIds": ["SAI-RUN-AIRZOOM-42-BLK"]
          },
          "resources": [
            { "id": "SAI-RUN-AIRZOOM-42-BLK", "descriptor": { "name": "AirZoom Running Shoes — Size 42 Black" }, "resourceAttributes": { "@context": "https://schema.ion.id/trade/resource/v1/", "@type": "ion:TradeResourceAttributes", "ion:quantity": { "value": 1, "unit": "piece" } } }
          ]
        }
      ]
    }
  }
}
```

The contract is now `ACTIVE`. The `Contract.id` is now populated by the BPP (per Beckn — the BPP issues the contract identifier no later than `/on_confirm`). SellerApp Indonesia knows to pack the shoes.

### `/confirm` to LogisticsApp Indonesia (in parallel)

Same pattern. LogisticsApp Indonesia's `/on_confirm`:

```json
{
  "message": {
    "contract": {
      "id": "LAI-AWB-2026-04-25-009823",
      "status": { "code": "ACTIVE" },
      "commitments": [
        {
          "id": "cmt-logi-1",
          "status": { "code": "ACTIVE" },
          "offer": { "id": "OFR-LAI-PARCEL-NEXTDAY", "resourceIds": ["shipment-sari-2026-04-25"] },
          "resources": [ /* shipment resource */ ]
        }
      ],
      "contractAttributes": {
        "@context": "https://schema.ion.id/logistics/contract/v1/",
        "@type": "ion:LogisticsContractAttributes",
        "ion:awbNumber": "LAI-AWB-2026-04-25-009823",
        "ion:expectedPickupWindow": { "start": "2026-04-26T10:00:00+07:00", "end": "2026-04-26T14:00:00+07:00" }
      }
    }
  }
}
```

Notice the AWB number lives in `contractAttributes` (Beckn-native slot on `Contract`, line 2274 of `beckn.yaml`). The `Contract.id` is the BPP's chosen identifier — for a logistics BPP, the AWB is a natural choice.

---

## Phase 7 — Fulfilment: unsolicited /on_status pushes

Over the next two days, LogisticsApp Indonesia sends a series of `/on_status` messages (unsolicited — BuyerApp Indonesia doesn't ask; LogisticsApp Indonesia pushes as events happen). Each carries an updated `Performance` block under `Contract.performance[*]` whose `performanceAttributes` describe the current state:

```
Apr 26 10:23    on_status: performance[*].status.code = PICKED_UP
Apr 26 14:15    on_status: performance[*].status.code = AT_HUB_ORIGIN
Apr 26 23:47    on_status: performance[*].status.code = IN_TRANSIT
Apr 27 08:02    on_status: performance[*].status.code = AT_HUB_DESTINATION
Apr 27 11:30    on_status: performance[*].status.code = OUT_FOR_DELIVERY
Apr 27 15:42    on_status: performance[*].status.code = DELIVERED
```

`Performance.status` is a Beckn `Descriptor`. ION defines the allowed `code` values for logistics in the LOG-PARCEL state machine (`schema/extensions/logistics/performance-states/v1/`). Stop-level details (which hub, which agent, OTP verification, delivery timestamp) live in `performanceAttributes`.

When LogisticsApp Indonesia pushes `DELIVERED`, BuyerApp Indonesia updates Sari's order status to "Delivered" in the app. Sari gets a notification.

---

## Phase 8 — Rating and support

A day after delivery, BuyerApp Indonesia prompts Sari to rate. She gives 5 stars.

BuyerApp Indonesia → LogisticsApp Indonesia: `/rate`. ION's rating fields live inside the rating target's `*Attributes` slot per `core/rating/v1`.

If Sari had a problem ("delivered to wrong building"), BuyerApp Indonesia would fire `/support` carrying support details inside `Support.channels[*]` (a Beckn `Attributes` array — see the `Support` schema in `beckn.yaml`).

---

## Phase 9 — Reconciliation (a few days later)

After the order is complete, SellerApp Indonesia and BuyerApp Indonesia reconcile financially. BuyerApp Indonesia keeps a platform fee; the balance is remitted to SellerApp Indonesia. This happens via ION's L3 `/reconcile` extension.

The L3 spec requires the message body to carry `contract.id` and `contract.settlements[*]` (see `schema/core/v2/api/v2.0.0/ion-endpoints.yaml` → `ReconcileAction`). So the reconcile data lives on a settlement, not at message root:

```json
{
  "context": {
    "domain": "retail",
    "action": "reconcile",
    "version": "2.0.0",
    "bapId": "buyerapp.id",
    "bapUri": "https://buyerapp.id/api/beckn",
    "bppId": "sellerapp.id",
    "bppUri": "https://sellerapp.id/api/beckn",
    "transactionId": "9854f3b1-5c2d-4e9f-ba34-8e7c9d0e1f2b",
    "messageId": "5d6e7f80-9123-44b5-a678-9abcdef01234",
    "timestamp": "2026-04-29T09:00:00.000Z",
    "ttl": "PT5M",
    "schemaContext": [
      "https://schema.beckn.io/core/v2.0.0/",
      "https://schema.ion.id/core/reconcile/v1/"
    ]
  },
  "message": {
    "contract": {
      "id": "ORD-SAI-2026-04-25-00001234",
      "commitments": [
        { "id": "cmt-1", "status": { "code": "ACTIVE" }, "offer": { "id": "OFR-SAI-AIRZOOM-42-BLK-STD", "resourceIds": ["SAI-RUN-AIRZOOM-42-BLK"] }, "resources": [ { "id": "SAI-RUN-AIRZOOM-42-BLK" } ] }
      ],
      "settlements": [
        {
          "id": "settle-sai-20260425-a1-recon",
          "status": { "code": "DRAFT" },
          "considerationId": "cons-1",
          "settlementAttributes": {
            "@context": "https://schema.ion.id/core/reconcile/v1/",
            "@type": "ion:ReconcileAttributes",
            "ion:base": { "value": 500000, "currency": "IDR" },
            "ion:adjustments": [
              { "ion:type": "PLATFORM_FEE", "ion:amount": { "value": -25000, "currency": "IDR" } },
              { "ion:type": "PPN_ADJUSTMENT", "ion:amount": { "value": 0, "currency": "IDR" } }
            ],
            "ion:finalAmount": { "value": 475000, "currency": "IDR" },
            "ion:taxDeclarations": [
              { "ion:type": "PPN", "ion:rate": 0.11, "ion:base": { "value": 500000, "currency": "IDR" }, "ion:tax": { "value": 55000, "currency": "IDR" } }
            ]
          }
        }
      ]
    }
  }
}
```

SellerApp Indonesia agrees via `/on_reconcile`. The settlement status moves `DRAFT → COMMITTED`. When BuyerApp Indonesia actually transfers the money to SellerApp Indonesia's bank account, status moves `COMMITTED → COMPLETE`.

Similarly, BuyerApp Indonesia reconciles with LogisticsApp Indonesia for delivery fees.

---

## What just happened — the summary

In five seconds of elapsed API time, three minutes of consumer interaction, and two days of fulfilment:

- BuyerApp Indonesia (BAP) ran two separate transactions — one with SellerApp Indonesia (Trade), one with LogisticsApp Indonesia (Logistics)
- Roughly 10 messages went back and forth per transaction (4 forward + 4 callback + 2 unsolicited status pushes)
- Every message was cryptographically signed (Ed25519 over a BLAKE2b-512 digest)
- Every message conformed to Beckn v2.0.0 core shapes — `Resource` had only `id` + `descriptor` + `resourceAttributes`, `Contract.consideration` (singular) and `Contract.settlements` (plural) appeared in the right places, `Performance` was an array on `Contract`, and so on
- ION's L4 core vocabulary carried Indonesian specifics (NPWP, PKP status, address hierarchy, tax breakup) inside the appropriate `*Attributes` bags
- ION's L5 sector vocabulary carried retail specifics (availability, price) and logistics specifics (shipment profile, service level, AWB)
- Each `*Attributes` bag had exactly one `@context` and one `@type` — never two — and `context.schemaContext` enumerated all vocabularies the message referenced

**Sari never saw any of this.** She tapped Buy and got her shoes two days later.

---

## What happens when things go wrong

This walkthrough is the happy path. Reality has branches:

- **Payment fails** → BAP doesn't fire `/confirm`; contracts stay in `DRAFT`; expire per TTL
- **Stock unavailable at /init** → `/on_init` returns error, BAP shows "out of stock" to user
- **Seller delays dispatch** → BPP misses SLA; cancellation and refund policy trigger (see Trade branches: cancellation, updates)
- **Package damaged in transit** → buyer initiates `/update` on the Logistics contract with `disputeReason`; evidence exchanged; if unresolved, either party escalates via `/raise` (ION L3 extension)
- **Weight disputed at LogisticsApp Indonesia hub** → weight-dispute branch fires; LogisticsApp Indonesia adjusts price; BAP either accepts or escalates
- **Delivery attempt fails** → attempts branch: NDR recorded, reschedule offered; if all attempts fail, RTO branch activates; shoes go back to SellerApp Indonesia

Each of these is a branch — a specific documented sub-flow. See your sector doc for details:
- Trade branches: [`ION_Sector_A_Trade.md`](ION_Sector_A_Trade.md)
- Logistics branches: [`ION_Sector_B_Logistics.md`](ION_Sector_B_Logistics.md) §6

---

## Next steps

- Read your sector doc now that you've seen how a transaction flows
- Read [`ION_Onboarding_and_Auth.md`](ION_Onboarding_and_Auth.md) when you're ready to implement signing
- Read [`ION_Beckn_Conformance.md`](ION_Beckn_Conformance.md) before conformance testing

---

*Last updated v0.5.2-draft. Every payload in this document is shaped to validate against `schema/core/v2/api/v2.0.0/ion-with-beckn.yaml` (which composes Beckn v2.0.0 + ION L2/L3/L4/L5). If a payload here disagrees with the OpenAPI document, the OpenAPI document wins and this doc is the bug.*
