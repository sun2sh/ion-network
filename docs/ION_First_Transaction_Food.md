# ION First Transaction (Food) — Linked Trade + Hyperlocal Logistics

**Status: v0.5.3-draft**

This walkthrough complements `ION_First_Transaction.md` (running shoes + parcel delivery). It shows a different sector pair — **food order + hyperlocal courier** — and demonstrates how ION links two transactions into a single causally-related pair.

If you've already read the running-shoes doc, you can skim this one for the differences. Most of the Beckn shape is the same; what's different is:

- **Domain pair:** `ion:food` for the order, `ion:logistics-hyperlocal` for the delivery.
- **Linkage:** the logistics contract carries `parentContractReference` pointing back to the trade contract; the trade contract carries `linkedContractId` pointing to the logistics contract. This is the formal mechanism for "this delivery transaction serves this order transaction."
- **Pack mix:** `core/localization`, `core/product`, `trade/resource`, `trade/offer`, `trade/contract` on the trade side; `logistics/resource`, `logistics/offer`, `logistics/contract`, `logistics/performance`, `logistics/tracking` on the logistics side.

---

## The scenario

Andi Pratama in South Jakarta opens GoFood (a hypothetical BAP) at 19:30 on a Tuesday and orders Nasi Goreng Spesial + Es Teh Manis from Restoran Sumber Rejeki, a halal-certified warung 800 metres away. Delivery is by Gojek-Cabang Hyperlocal — a hyperlocal logistics BPP — by motorcycle. ETA 25 minutes.

Participants:

- **Buyer:** Andi Pratama in Kebayoran Baru, South Jakarta.
- **BAP:** GoFood (the consumer app).
- **Seller BPP:** RestoranSumberRejeki (the warung's commerce app, registered as `restoran-sumber-rejeki.ion.id`).
- **Logistics BPP:** GojekCabangHyperlocal (`gojek-cabang.ion.id`).

Two ION transactions happen, formally linked:

1. **Trade transaction** (`tx-food-A1B2C3`) — GoFood ↔ RestoranSumberRejeki. Domain `ion:food`. Produces a `Contract` whose `contractAttributes.linkedContractId` points at transaction 2.
2. **Logistics transaction** (`tx-log-D4E5F6`) — GoFood ↔ GojekCabangHyperlocal. Domain `ion:logistics-hyperlocal`. Produces a `Contract` whose `contractAttributes.parentContractReference` points at transaction 1.

The two `Context.transactionId` values are different — they have to be, because each is a separate Beckn transaction with its own message thread. The **link** is in the ION-extension fields on the contract layer, not in `Context`. (Beckn v2.0 does not have a built-in parent/child transaction primitive — see "Why the link lives in `contractAttributes`" near the end of this doc.)

---

## Two conformance rules (same as the shoes doc)

**Rule 1 — Beckn shapes are not negotiable.** Every Beckn core object has a fixed shape in `beckn.yaml` v2.0.0. ION never adds top-level fields to Beckn objects. Extensions live inside `*Attributes` slots.

**Rule 2 — One vocabulary per `*Attributes` bag.** Each bag is a JSON-LD container with exactly one `@context`. Multiple ION packs participate by being declared at the message level via `Context.schemaContext`.

---

## Phase 0 — Catalogue discovery (off-transaction)

RestoranSumberRejeki publishes its menu via `/publish_catalog`. We won't show the full catalogue here; assume the BAP has already discovered the restaurant and the consumer has tapped "Nasi Goreng Spesial."

What matters for this walkthrough: the catalogue has registered the restaurant location at lat/lon `(-6.2425, 106.7980)` (Kebayoran Baru), and the offered menu items each carry `Resource.resourceAttributes` with halal status, allergen info, prep time. The consumer is at `(-6.2418, 106.8025)` — about 800 m away.

---

## Phase 1 — Consumer taps "Order"

The BAP composes a `/select` to the seller. This is one Beckn transaction (`tx-food-A1B2C3`). The logistics transaction has not started yet.

---

## Phase 2 — BAP → Seller BPP: `/select`

### Request: `POST https://restoran-sumber-rejeki.ion.id/api/beckn/select`

```json
{
  "context": {
    "domain": "ion:food",
    "action": "select",
    "version": "2.0.0",
    "bapId": "gofood.ion.id",
    "bapUri": "https://gofood.ion.id/api/beckn",
    "bppId": "restoran-sumber-rejeki.ion.id",
    "bppUri": "https://restoran-sumber-rejeki.ion.id/api/beckn",
    "transactionId": "tx-food-A1B2C3",
    "messageId": "msg-food-select-001",
    "networkId": "ion.id",
    "timestamp": "2026-04-29T12:30:00.000Z",
    "ttl": "PT30S",
    "schemaContext": [
      "https://schema.beckn.io/core/v2.0.0/",
      "https://schema.ion.id/extensions/core/localization/v1/context.jsonld",
      "https://schema.ion.id/extensions/core/product/v1/context.jsonld",
      "https://schema.ion.id/extensions/trade/resource/v1/context.jsonld",
      "https://schema.ion.id/extensions/trade/offer/v1/context.jsonld"
    ]
  },
  "message": {
    "contract": {
      "id": "draft-contract-A1B2C3",
      "status": {
        "descriptor": { "code": "DRAFT", "shortDesc": "Draft contract — quote requested" }
      },
      "commitments": [
        {
          "id": "cmt-food-001",
          "status": {
            "descriptor": { "code": "PROPOSED", "shortDesc": "Line proposed by BAP" }
          },
          "offer": { "id": "off-nasi-goreng-spesial" },
          "resources": [
            {
              "id": "res-nasi-goreng-spesial",
              "descriptor": { "name": "Nasi Goreng Spesial" },
              "resourceAttributes": {
                "@context": "https://schema.ion.id/extensions/trade/resource/v1/context.jsonld",
                "@type": "ion:TradeResourceAttributes",
                "quantity": { "count": 1 }
              }
            }
          ],
          "commitmentAttributes": {
            "@context": "https://schema.ion.id/extensions/trade/commitment/v1/context.jsonld",
            "@type": "ion:TradeCommitmentAttributes",
            "lineId": "L01",
            "specialInstructions": "Tidak pedas, tanpa MSG"
          }
        },
        {
          "id": "cmt-food-002",
          "status": {
            "descriptor": { "code": "PROPOSED", "shortDesc": "Line proposed by BAP" }
          },
          "offer": { "id": "off-es-teh-manis" },
          "resources": [
            {
              "id": "res-es-teh-manis",
              "descriptor": { "name": "Es Teh Manis" },
              "resourceAttributes": {
                "@context": "https://schema.ion.id/extensions/trade/resource/v1/context.jsonld",
                "@type": "ion:TradeResourceAttributes",
                "quantity": { "count": 1 }
              }
            }
          ],
          "commitmentAttributes": {
            "@context": "https://schema.ion.id/extensions/trade/commitment/v1/context.jsonld",
            "@type": "ion:TradeCommitmentAttributes",
            "lineId": "L02"
          }
        }
      ]
    }
  }
}
```

### Async callback: `POST https://gofood.ion.id/api/beckn/on_select`

The seller replies with prices and a quoted prep time. The Consideration carries the price breakdown including the food cost — but **not delivery cost** (that's the logistics BPP's job, in a separate transaction).

```json
{
  "context": {
    "domain": "ion:food",
    "action": "on_select",
    "version": "2.0.0",
    "bapId": "gofood.ion.id",
    "bapUri": "https://gofood.ion.id/api/beckn",
    "bppId": "restoran-sumber-rejeki.ion.id",
    "bppUri": "https://restoran-sumber-rejeki.ion.id/api/beckn",
    "transactionId": "tx-food-A1B2C3",
    "messageId": "msg-food-onselect-001",
    "networkId": "ion.id",
    "timestamp": "2026-04-29T12:30:02.480Z",
    "ttl": "PT30S",
    "schemaContext": [
      "https://schema.beckn.io/core/v2.0.0/",
      "https://schema.ion.id/extensions/core/tax/v1/context.jsonld",
      "https://schema.ion.id/extensions/trade/consideration/v1/context.jsonld",
      "https://schema.ion.id/extensions/trade/performance/v1/context.jsonld"
    ]
  },
  "message": {
    "contract": {
      "id": "quote-contract-A1B2C3",
      "status": {
        "descriptor": { "code": "QUOTED", "shortDesc": "Quote returned by seller" }
      },
      "commitments": [
        {
          "id": "cmt-food-001",
          "status": {
            "descriptor": { "code": "QUOTED", "shortDesc": "Line priced" }
          },
          "offer": { "id": "off-nasi-goreng-spesial" },
          "resources": [
            {
              "id": "res-nasi-goreng-spesial",
              "resourceAttributes": {
                "@context": "https://schema.ion.id/extensions/trade/resource/v1/context.jsonld",
                "@type": "ion:TradeResourceAttributes",
                "quantity": { "count": 1 }
              }
            }
          ]
        },
        {
          "id": "cmt-food-002",
          "status": {
            "descriptor": { "code": "QUOTED", "shortDesc": "Line priced" }
          },
          "offer": { "id": "off-es-teh-manis" },
          "resources": [
            {
              "id": "res-es-teh-manis",
              "resourceAttributes": {
                "@context": "https://schema.ion.id/extensions/trade/resource/v1/context.jsonld",
                "@type": "ion:TradeResourceAttributes",
                "quantity": { "count": 1 }
              }
            }
          ]
        }
      ],
      "consideration": [
        {
          "id": "cnsr-food-A1B2C3",
          "status": {
            "descriptor": { "code": "QUOTED", "shortDesc": "Total quoted to BAP" }
          },
          "considerationAttributes": {
            "@context": "https://schema.ion.id/extensions/trade/consideration/v1/context.jsonld",
            "@type": "ion:TradeConsiderationAttributes",
            "totalAmount": "35000",
            "currency": "IDR",
            "breakup": [
              { "type": "RESOURCE", "lineId": "L01", "amount": "27000" },
              { "type": "RESOURCE", "lineId": "L02", "amount": "8000" }
            ],
            "ppnRate": "0.00",
            "_note": "Restoran Sumber Rejeki is non-PKP (turnover < IDR 4.8B/year), so PPN = 0."
          }
        }
      ],
      "performance": [
        {
          "id": "perf-food-A1B2C3",
          "performanceAttributes": {
            "@context": "https://schema.ion.id/extensions/trade/performance/v1/context.jsonld",
            "@type": "ion:TradePerformanceAttributes",
            "prepTimeMinutes": 12,
            "readyByEstimate": "2026-04-29T12:42:00.000Z"
          }
        }
      ]
    }
  }
}
```

**What the BAP knows now:**
- Food cost: IDR 35,000.
- The kitchen will be ready in ~12 minutes (12:42).
- Delivery is the BAP's job to arrange — the food contract says nothing about delivery method, fee, or ETA.

---

## Phase 3 — BAP → Logistics BPP: `/select` (the linked transaction begins)

The BAP, knowing the pickup address (the restaurant's lat/lon from the catalogue) and the dropoff address (the consumer's), opens **a separate Beckn transaction** with GojekCabangHyperlocal. This is `tx-log-D4E5F6` — different `transactionId` from the food order.

The crucial linking move is in the request payload: the logistics commitment's `commitmentAttributes` carries `parentTradeTransactionId: "tx-food-A1B2C3"` and the contract-level `parentContractReference` will be set when contracts firm up.

### Request: `POST https://gojek-cabang.ion.id/api/beckn/select`

```json
{
  "context": {
    "domain": "ion:logistics-hyperlocal",
    "action": "select",
    "version": "2.0.0",
    "bapId": "gofood.ion.id",
    "bapUri": "https://gofood.ion.id/api/beckn",
    "bppId": "gojek-cabang.ion.id",
    "bppUri": "https://gojek-cabang.ion.id/api/beckn",
    "transactionId": "tx-log-D4E5F6",
    "messageId": "msg-log-select-001",
    "networkId": "ion.id",
    "timestamp": "2026-04-29T12:30:03.100Z",
    "ttl": "PT30S",
    "schemaContext": [
      "https://schema.beckn.io/core/v2.0.0/",
      "https://schema.ion.id/extensions/logistics/resource/v1/context.jsonld",
      "https://schema.ion.id/extensions/logistics/offer/v1/context.jsonld",
      "https://schema.ion.id/extensions/logistics/performance/v1/context.jsonld"
    ]
  },
  "message": {
    "contract": {
      "id": "draft-contract-D4E5F6",
      "status": {
        "descriptor": { "code": "DRAFT", "shortDesc": "Quote requested" }
      },
      "commitments": [
        {
          "id": "cmt-log-001",
          "status": {
            "descriptor": { "code": "PROPOSED", "shortDesc": "Delivery line proposed" }
          },
          "offer": { "id": "off-hyperlocal-bike" },
          "resources": [
            {
              "id": "res-package-A1B2C3",
              "descriptor": { "name": "Food package — 2 items, ~600g" },
              "resourceAttributes": {
                "@context": "https://schema.ion.id/extensions/logistics/resource/v1/context.jsonld",
                "@type": "ion:LogisticsResourceAttributes",
                "serviceType": "HYPERLOCAL_BIKE",
                "quantity": { "count": 1 },
                "weight": { "value": 0.6, "unit": "kg" },
                "declaredValue": { "value": 35000, "currency": "IDR" },
                "temperatureControl": "AMBIENT_HOT"
              }
            }
          ],
          "commitmentAttributes": {
            "@context": "https://schema.ion.id/extensions/logistics/commitment/v1/context.jsonld",
            "@type": "ion:LogisticsCommitmentAttributes",
            "parentTradeTransactionId": "tx-food-A1B2C3",
            "_note": "This delivery is for food contract tx-food-A1B2C3"
          }
        }
      ],
      "performance": [
        {
          "id": "perf-log-D4E5F6",
          "performanceAttributes": {
            "@context": "https://schema.ion.id/extensions/logistics/performance/v1/context.jsonld",
            "@type": "ion:LogisticsPerformanceAttributes",
            "stops": [
              {
                "type": "PICKUP",
                "location": { "gps": "-6.2425,106.7980" },
                "address": { "name": "Restoran Sumber Rejeki", "city": "Jakarta Selatan" },
                "windowStart": "2026-04-29T12:42:00.000Z",
                "windowEnd": "2026-04-29T12:50:00.000Z"
              },
              {
                "type": "DROPOFF",
                "location": { "gps": "-6.2418,106.8025" },
                "address": { "name": "Buyer location", "city": "Jakarta Selatan" },
                "windowStart": "2026-04-29T12:55:00.000Z",
                "windowEnd": "2026-04-29T13:05:00.000Z"
              }
            ]
          }
        }
      ]
    }
  }
}
```

### Async callback: `POST https://gofood.ion.id/api/beckn/on_select` (logistics)

```json
{
  "context": {
    "domain": "ion:logistics-hyperlocal",
    "action": "on_select",
    "version": "2.0.0",
    "bapId": "gofood.ion.id",
    "bapUri": "https://gofood.ion.id/api/beckn",
    "bppId": "gojek-cabang.ion.id",
    "bppUri": "https://gojek-cabang.ion.id/api/beckn",
    "transactionId": "tx-log-D4E5F6",
    "messageId": "msg-log-onselect-001",
    "networkId": "ion.id",
    "timestamp": "2026-04-29T12:30:04.350Z",
    "ttl": "PT30S",
    "schemaContext": [
      "https://schema.beckn.io/core/v2.0.0/",
      "https://schema.ion.id/extensions/logistics/consideration/v1/context.jsonld",
      "https://schema.ion.id/extensions/logistics/performance/v1/context.jsonld"
    ]
  },
  "message": {
    "contract": {
      "id": "quote-contract-D4E5F6",
      "status": {
        "descriptor": { "code": "QUOTED", "shortDesc": "Logistics quote returned" }
      },
      "commitments": [
        {
          "id": "cmt-log-001",
          "status": {
            "descriptor": { "code": "QUOTED", "shortDesc": "Delivery priced" }
          },
          "offer": { "id": "off-hyperlocal-bike" },
          "resources": [
            {
              "id": "res-package-A1B2C3",
              "resourceAttributes": {
                "@context": "https://schema.ion.id/extensions/logistics/resource/v1/context.jsonld",
                "@type": "ion:LogisticsResourceAttributes",
                "serviceType": "HYPERLOCAL_BIKE",
                "quantity": { "count": 1 }
              }
            }
          ]
        }
      ],
      "consideration": [
        {
          "id": "cnsr-log-D4E5F6",
          "status": {
            "descriptor": { "code": "QUOTED", "shortDesc": "Delivery cost quoted" }
          },
          "considerationAttributes": {
            "@context": "https://schema.ion.id/extensions/logistics/consideration/v1/context.jsonld",
            "@type": "ion:LogisticsConsiderationAttributes",
            "totalAmount": "8000",
            "currency": "IDR",
            "breakup": [
              { "type": "BASE_FARE", "amount": "5000" },
              { "type": "DISTANCE", "amount": "3000", "_note": "0.8 km @ IDR 3,750/km" }
            ]
          }
        }
      ],
      "performance": [
        {
          "id": "perf-log-D4E5F6",
          "performanceAttributes": {
            "@context": "https://schema.ion.id/extensions/logistics/performance/v1/context.jsonld",
            "@type": "ion:LogisticsPerformanceAttributes",
            "estimatedPickupAt": "2026-04-29T12:46:00.000Z",
            "estimatedDeliveryAt": "2026-04-29T12:58:00.000Z"
          }
        }
      ]
    }
  }
}
```

**The BAP now displays to the consumer:**
- Food: IDR 35,000
- Delivery: IDR 8,000
- Total: IDR 43,000
- ETA: 28 minutes

The two amounts came from two separate `/on_select` callbacks against two separate transactions. The BAP composes them; ION does not require either BPP to know about the other.

---

## Phase 4 — `/init` and `/confirm` to both BPPs (parallel, with the formal link set)

Once the consumer taps "Place Order," the BAP fires `/init` then `/confirm` to both BPPs in parallel. **At `/confirm` time, the contracts firm up, and the linkage gets stamped on both sides.**

### `/confirm` to RestoranSumberRejeki — `contract.contractAttributes.linkedContractId` is set

```json
{
  "context": {
    "domain": "ion:food",
    "action": "confirm",
    "version": "2.0.0",
    "bapId": "gofood.ion.id",
    "bapUri": "https://gofood.ion.id/api/beckn",
    "bppId": "restoran-sumber-rejeki.ion.id",
    "bppUri": "https://restoran-sumber-rejeki.ion.id/api/beckn",
    "transactionId": "tx-food-A1B2C3",
    "messageId": "msg-food-confirm-001",
    "networkId": "ion.id",
    "timestamp": "2026-04-29T12:30:18.000Z",
    "ttl": "PT30S",
    "schemaContext": [
      "https://schema.beckn.io/core/v2.0.0/",
      "https://schema.ion.id/extensions/trade/contract/v1/context.jsonld"
    ]
  },
  "message": {
    "contract": {
      "id": "tc-food-A1B2C3",
      "status": {
        "descriptor": { "code": "CONFIRMED", "shortDesc": "Order confirmed by buyer" }
      },
      "contractAttributes": {
        "@context": "https://schema.ion.id/extensions/trade/contract/v1/context.jsonld",
        "@type": "ion:TradeContractAttributes",
        "linkedContractId": "tc-log-D4E5F6",
        "_note": "Trade contract linked to logistics contract for delivery"
      },
      "commitments": [
        {
          "id": "cmt-food-001",
          "status": {
            "descriptor": { "code": "CONFIRMED", "shortDesc": "Line confirmed" }
          },
          "offer": { "id": "off-nasi-goreng-spesial" },
          "resources": [
            {
              "id": "res-nasi-goreng-spesial",
              "resourceAttributes": {
                "@context": "https://schema.ion.id/extensions/trade/resource/v1/context.jsonld",
                "@type": "ion:TradeResourceAttributes",
                "quantity": { "count": 1 }
              }
            }
          ]
        },
        {
          "id": "cmt-food-002",
          "status": {
            "descriptor": { "code": "CONFIRMED", "shortDesc": "Line confirmed" }
          },
          "offer": { "id": "off-es-teh-manis" },
          "resources": [
            {
              "id": "res-es-teh-manis",
              "resourceAttributes": {
                "@context": "https://schema.ion.id/extensions/trade/resource/v1/context.jsonld",
                "@type": "ion:TradeResourceAttributes",
                "quantity": { "count": 1 }
              }
            }
          ]
        }
      ]
    }
  }
}
```

### `/confirm` to GojekCabangHyperlocal — `contract.contractAttributes.parentContractReference` is set

```json
{
  "context": {
    "domain": "ion:logistics-hyperlocal",
    "action": "confirm",
    "version": "2.0.0",
    "bapId": "gofood.ion.id",
    "bapUri": "https://gofood.ion.id/api/beckn",
    "bppId": "gojek-cabang.ion.id",
    "bppUri": "https://gojek-cabang.ion.id/api/beckn",
    "transactionId": "tx-log-D4E5F6",
    "messageId": "msg-log-confirm-001",
    "networkId": "ion.id",
    "timestamp": "2026-04-29T12:30:18.500Z",
    "ttl": "PT30S",
    "schemaContext": [
      "https://schema.beckn.io/core/v2.0.0/",
      "https://schema.ion.id/extensions/logistics/contract/v1/context.jsonld"
    ]
  },
  "message": {
    "contract": {
      "id": "tc-log-D4E5F6",
      "status": {
        "descriptor": { "code": "CONFIRMED", "shortDesc": "Delivery confirmed" }
      },
      "contractAttributes": {
        "@context": "https://schema.ion.id/extensions/logistics/contract/v1/context.jsonld",
        "@type": "ion:LogisticsContractAttributes",
        "parentContractReference": "tc-food-A1B2C3",
        "_note": "This delivery serves trade contract tc-food-A1B2C3"
      },
      "commitments": [
        {
          "id": "cmt-log-001",
          "status": {
            "descriptor": { "code": "CONFIRMED", "shortDesc": "Delivery confirmed" }
          },
          "offer": { "id": "off-hyperlocal-bike" },
          "resources": [
            {
              "id": "res-package-A1B2C3",
              "resourceAttributes": {
                "@context": "https://schema.ion.id/extensions/logistics/resource/v1/context.jsonld",
                "@type": "ion:LogisticsResourceAttributes",
                "serviceType": "HYPERLOCAL_BIKE",
                "quantity": { "count": 1 }
              }
            }
          ]
        }
      ]
    }
  }
}
```

After this round of `/confirm`, both contracts exist independently in their respective BPPs' systems but each contains a reference to the other. ION Central can trace the causal relationship via these references when answering "show me everything for order tx-food-A1B2C3" — it walks the link to find the delivery transaction.

---

## Phase 5 — Lifecycle pushes (each transaction owns its own status)

The two transactions now run in parallel, each pushing `/on_status` updates to the BAP for their own commitments:

**Trade transaction `tx-food-A1B2C3` pushes:**
- `cmt-food-001.status.code`: CONFIRMED → PREPARING (12:31) → READY (12:42)

**Logistics transaction `tx-log-D4E5F6` pushes:**
- `cmt-log-001.status.code`: CONFIRMED → COURIER_ASSIGNED (12:32) → AT_PICKUP (12:46) → IN_TRANSIT (12:48) → DELIVERED (12:57)

The BAP correlates these via its own internal mapping (`tx-food-A1B2C3 ↔ tx-log-D4E5F6`) and renders a unified order-tracking screen for the consumer.

ION Central's Catalog Discovery Service does NOT correlate them automatically — that's BAP responsibility. The `linkedContractId` and `parentContractReference` fields are for **post-hoc tracing** (audit, dispute resolution, reconciliation), not real-time message correlation.

---

## Why the link lives in `contractAttributes`

This is worth being explicit about because it's an architectural choice ION made.

**Beckn v2.0 does not have a built-in parent/child transaction primitive.** I checked: the `Context` object has `transactionId`, `messageId`, `bapId`, `bppId`, `networkId`, `requestDigest`, and 11 other fields — none of them is `parentTransactionId`, `childOf`, or anything similar. The closest Beckn comes is `Context.schemaContext`, which is for vocabulary declarations, not transaction linkage.

**Three ways ION could have encoded the food↔delivery link:**

| Option | Where | Verdict |
|---|---|---|
| Add `parentTransactionId` to Beckn `Context` | Beckn-owned territory | Forbidden by Rule 1 (ION never adds fields to Beckn objects) |
| Use `Context.schemaContext` with a relation URI | Hijacks vocabulary mechanism | Misuses the field; not what `schemaContext` means |
| Add link fields on `*Attributes` slots | ION-owned territory | Correct — extension slots are for exactly this |

ION chose option 3. The trade pack defines `TradeContractAttributes.linkedContractId`, the logistics pack defines `LogisticsContractAttributes.parentContractReference`. Both are existing fields in v0.5.3 (you'll find them in `schema/extensions/trade/contract/v1/attributes.yaml` and `schema/extensions/logistics/contract/v1/attributes.yaml`).

**One implication worth understanding:** because the link is in `contractAttributes`, it appears at `/init` time at the earliest, and is firm at `/confirm`. It is NOT in `/select` headers — the linkage is not part of the discovery/quote round. We carry the future-link signal in `commitmentAttributes.parentTradeTransactionId` during `/select` so the logistics BPP can quote correctly (knowing this is for an existing food order, not a standalone parcel pickup). At `/confirm`, the link gets stamped on both contracts.

---

## Reconciliation a few days later

Friday morning, ION Central's reconciliation service runs:

1. Pulls all confirmed contracts in the `ion:food` domain for Tuesday.
2. For each, follows `linkedContractId` to find the matching logistics contract.
3. Cross-checks: did delivery actually happen? Was the COD amount (if any) collected and remitted? Did the food cost match the breakup?

For our scenario the answer is "yes, all three" — the trade `Settlement` shows IDR 35,000 paid by GoPay to RestoranSumberRejeki, the logistics `Settlement` shows IDR 8,000 paid by GoFood to GojekCabangHyperlocal, and the consumer's GoPay statement shows the IDR 43,000 charge. Reconciliation passes.

The `parentContractReference` on the logistics side is what makes this trace possible. Without it, the reconciliation service would have no way to correlate `tx-log-D4E5F6` with `tx-food-A1B2C3` — they're two unrelated Beckn transactions as far as Beckn itself is concerned.

---

## What just happened — the summary

A consumer placed one logical order ("Nasi Goreng + Es Teh, deliver to me"). Behind the scenes that became **two ION transactions**, each Beckn-conformant on its own, but **causally linked via two ION extension fields**:

- **Trade contract → logistics contract**: `TradeContractAttributes.linkedContractId`
- **Logistics contract → trade contract**: `LogisticsContractAttributes.parentContractReference`

The linkage is bidirectional, lives on ION-owned `*Attributes` slots, requires no Beckn changes, and is enforceable at the contract level by ION Central's reconciliation logic.

Compare with the running-shoes scenario in `ION_First_Transaction.md`: same mechanism, different sectors. The pattern generalises — any time ION needs a multi-BPP coordinated transaction (food + delivery, e-commerce + logistics, ride + insurance, etc.), the link goes in `contractAttributes` on both sides.

---

## Differences from the shoes scenario

| Aspect | Shoes (ION_First_Transaction.md) | Food (this doc) |
|---|---|---|
| Trade domain | `ion:trade` | `ion:food` |
| Logistics domain | `ion:logistics-parcel` | `ion:logistics-hyperlocal` |
| Delivery time | 2-3 days | 25-30 minutes |
| Distance | Jakarta → Surabaya (~700 km) | 0.8 km |
| Pickup window | "Anytime today" | Tight: 12:42–12:50 |
| Resource attributes | dimensions, weight, country of origin | weight, declared value, temperature |
| Performance attributes | tracking number, ETA in days | stops with GPS+windows, ETA in minutes |
| Linkage encoding | identical | identical |

The link mechanism is invariant across sector pairs. That's the whole point.

---

*Last updated: v0.5.3-draft, 2026-04-29.*
