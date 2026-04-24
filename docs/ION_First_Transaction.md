# ION First Transaction — Annotated Walkthrough

**A realistic end-to-end transaction with every message explained field-by-field.**

If you've read [`ION_Start_Here.md`](ION_Start_Here.md) and [`ION_Glossary.md`](ION_Glossary.md), you have the concepts. This doc shows them in action.

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

## A rule you will see enforced throughout

Every JSON-LD `@context` in every ION message resolves to **one of exactly two places**:

- `https://schema.beckn.io/core/v2.0.0/` — Beckn's core transport vocabulary (envelope, object model, signing). Owned by Beckn Foundation.
- `https://schema.ion.id/{layer}/{pack}/{version}/` — ION's own vocabulary (all extension attributes, policies, states, error categories). Owned by ION Network.

**No other `@context` values are valid on ION.** Beckn's domain-specific modules (`schema.beckn.io/Logistics/`, `schema.beckn.io/Retail/`, etc.) are explicitly NOT imported — their classification does not match ION's sector model. Other networks' vocabularies (ONDC, etc.) are not accepted until Council ratifies mapping entries under `schema.ion.id/mappings/`.

ION Central rejects messages carrying any other `@context` at the protocol gate.

You will see this rule in action in every payload below — every `@context` resolves to one of these two roots.

---

## Phase 0 — Catalog discovery (happens continuously, not at order time)

Before any of this starts, SellerApp Indonesia and LogisticsApp Indonesia have already published their catalogs to the Catalog Discovery Service (CDS). BuyerApp Indonesia has subscribed.

SellerApp Indonesia's catalog might include this offer (simplified):

```json
{
  "id": "SAI-RUN-AIRZOOM-42-BLK",
  "descriptor": { "name": "AirZoom Running Shoes — Size 42 Black" },
  "offerAttributes": {
    "@context": "https://schema.ion.id/trade/offer/v1/",
    "@type": "ion:TradeOffer",
    "ion:price": { "value": 500000, "currency": "IDR" },
    "ion:availability": "IN_STOCK",
    "ion:selectRequired": false,
    "ion:cancellationPolicy": "ion://policy/cancel.standard.until-dispatched",
    "ion:returnPolicy": "ion://policy/return.standard.14-days"
  }
}
```

Notice:
- The `id` is the offer ID — this is what the BAP quotes back in `/select`
- `offerAttributes` carries `@context` pointing at `schema.ion.id` (our L5 vocabulary)
- Fields are prefixed `ion:` to identify them as ION-vocabulary terms
- `selectRequired: false` — BAP can skip `/select` and go straight to `/init` for this offer
- `cancellationPolicy` is a policy IRI — the actual terms are looked up in ION's policy registry

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
    "@context": "https://schema.beckn.io/core/v2.0.0/",
    "domain": "retail",
    "action": "select",
    "version": "2.0.0",
    "bapId": "buyerapp.id",
    "bapUri": "https://buyerapp.id/api/beckn",
    "bppId": "sellerapp.id",
    "bppUri": "https://sellerapp.id/api/beckn",
    "transactionId": "txn-bapi-20260425-8743f2",
    "messageId": "msg-bapi-20260425-ab91c0",
    "timestamp": "2026-04-25T10:30:12.445Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "commitments": [
        {
          "id": "cmt-1",
          "resources": [
            {
              "id": "SAI-RUN-AIRZOOM-42-BLK",
              "quantity": {
                "value": 1,
                "unit": "piece"
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
| `context.@context` | Declares this is a Beckn v2.0.0 message |
| `context.domain` | Which sector — `retail` for trade transactions |
| `context.action` | Which endpoint is being invoked (must match URL) |
| `context.version` | MUST be `"2.0.0"` (Beckn's `Context.version` is `const: "2.0.0"`) |
| `context.bapId`/`bppId` | Registered subscriber IDs on the ION Registry |
| `context.transactionId` | Unique for this whole order lifecycle (same across select/init/confirm) |
| `context.messageId` | Unique for THIS specific message |
| `context.timestamp` | When BAP generated the message |
| `context.ttl` | How long this message is valid (30 seconds here) |
| `message.contract.commitments` | What the BAP is asking to commit to — one line: one pair of shoes |
| `resources[*].id` | Matches an offer ID from the catalog |
| `resources[*].quantity` | Required field. `unit: piece` because it's a product SKU. |

Also required but not shown: the `Authorization: Signature ...` HTTP header with Ed25519 signature. See [`ION_Onboarding_and_Auth.md`](ION_Onboarding_and_Auth.md) for exact signing format.

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
    "@context": "https://schema.beckn.io/core/v2.0.0/",
    "domain": "retail",
    "action": "on_select",
    "version": "2.0.0",
    "bapId": "buyerapp.id",
    "bapUri": "https://buyerapp.id/api/beckn",
    "bppId": "sellerapp.id",
    "bppUri": "https://sellerapp.id/api/beckn",
    "transactionId": "txn-bapi-20260425-8743f2",   // same transactionId
    "messageId": "msg-sai-20260425-cd7e14",         // new messageId
    "timestamp": "2026-04-25T10:30:12.702Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "status": { "descriptor": { "code": "DRAFT" } },
      "commitments": [
        {
          "id": "cmt-1",
          "status": { "descriptor": { "code": "DRAFT" } },
          "resources": [
            {
              "id": "SAI-RUN-AIRZOOM-42-BLK",
              "quantity": { "value": 1, "unit": "piece" },
              "resourceAttributes": {
                "@context": "https://schema.ion.id/trade/resource/v1/",
                "@type": "ion:TradeResource",
                "ion:availability": "IN_STOCK",
                "ion:countryOfOrigin": "ID"
              }
            }
          ]
        }
      ],
      "considerations": [
        {
          "id": "cons-1",
          "amount": { "value": 500000, "currency": "IDR" },
          "considerationAttributes": {
            "@context": "https://schema.ion.id/trade/consideration/v1/",
            "@type": "ion:TradeConsideration",
            "ion:breakup": [
              { "type": "ITEM", "amount": 500000 },
              { "type": "PPN", "amount": 55000, "note": "Applicable rate per current DJP regulation" }
            ]
          }
        }
      ]
    }
  }
}
```

Now BuyerApp Indonesia knows:
- Stock is available (`availability: IN_STOCK`)
- Price is confirmed (500,000 IDR + 55,000 PPN = 555,000 IDR)
- Contract is in `DRAFT` status (not committed yet)

Note: Contract status is `DRAFT` (4-value enum). Commitment status is also `DRAFT` (3-value enum — remember `Commitment.status` uses `DRAFT/ACTIVE/CLOSED`, distinct from Contract's `DRAFT/ACTIVE/CANCELLED/COMPLETE`).

---

## Phase 3 — BAP → Logistics BPP: /select (for delivery)

In parallel with (or right after) the shoe `/select`, BuyerApp Indonesia asks LogisticsApp Indonesia for a delivery quote.

```json
{
  "context": {
    "domain": "logistics",       // different sector
    "action": "select",
    "bapId": "buyerapp.id",
    "bppId": "logisticsapp.id",
    "transactionId": "txn-bapi-20260425-logi-4b9c21",  // DIFFERENT transaction
    "messageId": "msg-bapi-20260425-logi-xyz",
    "version": "2.0.0",
    // ... other context fields
  },
  "message": {
    "contract": {
      "commitments": [
        {
          "id": "cmt-logi-1",
          "resources": [
            {
              "id": "shipment-sari-2026-04-25",
              "quantity": { "value": 1, "unit": "package" },
              "resourceAttributes": {
                "@context": "https://schema.ion.id/logistics/resource/v1/",
                "@type": "ion:LogisticsShipment",
                "ion:serviceType": "PARCEL",
                "ion:weight": { "value": 1.2, "unit": "kilogram" },
                "ion:dimensions": { "length": 35, "width": 25, "height": 15, "unit": "centimeter" },
                "ion:declaredValue": { "amount": 555000, "currency": "IDR" }
              }
            }
          ]
        }
      ],
      "performance": {
        "performanceAttributes": {
          "@context": "https://schema.ion.id/logistics/performance/v1/",
          "@type": "ion:LogisticsPerformance",
          "ion:stops": [
            {
              "type": "PICKUP",
              "location": {
                "address": { "streetAddress": "Jl. Cendrawasih 15", "addressLocality": "Jakarta Pusat", "postalCode": "10710" },
                "ionSubdivisions": { "provinsiCode": "BPS-31", "kabupatenCode": "3173", "kecamatan": "Menteng", "kelurahan": "Cikini", "rt": "02", "rw": "05" }
              }
            },
            {
              "type": "DROPOFF",
              "location": {
                "address": { "streetAddress": "Jl. Pemuda 89", "addressLocality": "Surabaya", "postalCode": "60271" },
                "ionSubdivisions": { "provinsiCode": "BPS-35", "kabupatenCode": "3578", "kecamatan": "Genteng", "kelurahan": "Embong Kaliasin", "rt": "04", "rw": "02" }
              }
            }
          ]
        }
      }
    }
  }
}
```

Key things to notice:
- **Different `transactionId`** — Trade and Logistics are separate transactions
- `resourceAttributes` has `@type: ion:LogisticsShipment` (different L5 vocabulary)
- `ionSubdivisions` carries the Indonesian address hierarchy (provinsi/kabupaten/kecamatan/kelurahan/RT/RW) — these are from `core/address/v1`
- RT/RW are included because they're needed for last-mile delivery in Indonesia

LogisticsApp Indonesia responds via `/on_select` callback with a binding quote:

```json
{
  "message": {
    "contract": {
      "status": { "descriptor": { "code": "DRAFT" } },
      "considerations": [
        {
          "amount": { "value": 18000, "currency": "IDR" },
          "considerationAttributes": {
            "@context": "https://schema.ion.id/logistics/consideration/v1/",
            "@type": "ion:LogisticsConsideration",
            "ion:breakup": [
              { "type": "FREIGHT_BASE", "amount": 15000 },
              { "type": "PPN", "amount": 1650 },
              { "type": "FUEL_SURCHARGE", "amount": 1350 }
            ]
          }
        }
      ],
      "performance": {
        "performanceAttributes": {
          "ion:estimatedDeliveryTime": "2026-04-27T18:00:00+07:00",
          "ion:quoteValidityWindow": "PT30M"
        }
      }
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

The request echoes back the quote from `/on_select`, adding the delivery address (for tax jurisdiction computation) and the buyer's details:

```json
{
  "context": { /* ... */ "action": "init", "transactionId": "txn-bapi-20260425-8743f2" },
  "message": {
    "contract": {
      "commitments": [ /* same as select */ ],
      "considerations": [ /* same as on_select */ ],
      "participants": [
        {
          "role": "BUYER",
          "id": "bapi-user-sari-wijayanti",
          "participantAttributes": {
            "@context": "https://schema.ion.id/core/participant/v1/",
            "@type": "ion:ParticipantAttributes",
            "ion:contactName": "Sari Wijayanti",
            "ion:phoneProxy": "+62-xxx-xxx-7832"   // proxy, not real number
          }
        },
        {
          "role": "SELLER",
          "id": "sellerapp.id.merchant.sai-001",
          "participantAttributes": {
            "@context": "https://schema.ion.id/core/participant/v1/",
            "ion:npwp": "XX.XXX.XXX.X-XXX.XXX",
            "ion:nibNumber": "1234567890123",
            "ion:pkpStatus": "REGISTERED"
          }
        }
      ]
    }
  }
}
```

SellerApp Indonesia responds via `/on_init`:

```json
{
  "message": {
    "contract": {
      "status": { "descriptor": { "code": "DRAFT" } },
      "settlement": {
        "id": "settle-sai-20260425-a1",
        "status": { "descriptor": { "code": "DRAFT" } },
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
    }
  }
}
```

Now BuyerApp Indonesia has the payment link.

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
  "context": { /* ... */ "action": "confirm", "transactionId": "txn-bapi-20260425-8743f2" },
  "message": {
    "contract": {
      "settlement": {
        "settlementAttributes": {
          "@type": "ion:PaymentDeclaration",
          "ion:paymentStatus": "PAID",
          "ion:paymentReceivedAt": "2026-04-25T10:30:45.221Z",
          "ion:paymentProviderReference": "GOPAY-TXN-2026-04-25-98765432"
        }
      }
    }
  }
}
```

SellerApp Indonesia responds with `/on_confirm`:

```json
{
  "message": {
    "contract": {
      "id": "ORD-SAI-2026-04-25-00001234",          // SellerApp Indonesia's order ID
      "status": { "descriptor": { "code": "ACTIVE" } },
      "commitments": [
        {
          "id": "cmt-1",
          "status": { "descriptor": { "code": "ACTIVE" } }
        }
      ]
    }
  }
}
```

The contract is now `ACTIVE`. SellerApp Indonesia knows to pack the shoes.

### `/confirm` to LogisticsApp Indonesia (in parallel)

Same pattern. BuyerApp Indonesia tells LogisticsApp Indonesia "go ahead with delivery, here's the shipment detail." LogisticsApp Indonesia responds with `/on_confirm`:

```json
{
  "message": {
    "contract": {
      "id": "LogisticsApp Indonesia-AWB-2026-04-25-009823",           // LogisticsApp Indonesia's AWB
      "status": { "descriptor": { "code": "ACTIVE" } },
      "contractAttributes": {
        "@type": "ion:LogisticsContract",
        "ion:awbNumber": "LogisticsApp Indonesia-AWB-2026-04-25-009823",
        "ion:expectedPickupWindow": { "start": "2026-04-26T10:00:00+07:00", "end": "2026-04-26T14:00:00+07:00" }
      }
    }
  }
}
```

---

## Phase 7 — Fulfilment: unsolicited /on_status pushes

Over the next two days, LogisticsApp Indonesia sends a series of `/on_status` messages (unsolicited — BuyerApp Indonesia doesn't ask; LogisticsApp Indonesia pushes as events happen).

```
Apr 26 10:23    on_status: { status: "PICKED_UP", performance.currentStop: pickup }
Apr 26 14:15    on_status: { status: "AT_HUB_ORIGIN", performance.hubLocation: "Jakarta hub" }
Apr 26 23:47    on_status: { status: "IN_TRANSIT", performance.leg: "JKT-to-SUB" }
Apr 27 08:02    on_status: { status: "AT_HUB_DESTINATION", performance.hubLocation: "Surabaya hub" }
Apr 27 11:30    on_status: { status: "OUT_FOR_DELIVERY", performance.agentDetails: { name: "Budi", phoneProxy: "+62-xxx-xxx-1122" } }
Apr 27 15:42    on_status: { status: "DELIVERED", performance.deliveryOtp: "verified", performance.deliveredAt: "2026-04-27T15:42:11+07:00" }
```

`Performance.status.descriptor.code` values are open — ION defines them in the LOG-PARCEL state machine. `PICKED_UP`, `IN_TRANSIT`, `OUT_FOR_DELIVERY`, `DELIVERED` are the main ones for this spine.

When LogisticsApp Indonesia pushes `DELIVERED`, BuyerApp Indonesia updates Sari's order status to "Delivered" in the app. Sari gets a notification.

---

## Phase 8 — Rating and support

A day after delivery, BuyerApp Indonesia prompts Sari to rate. She gives 5 stars.

BuyerApp Indonesia → LogisticsApp Indonesia: `/rate` with `RatingInput` (see Beckn `RatingInput.target.targetAttributes` for where ION's rating fields live).

If Sari had a problem ("delivered to wrong building"), BuyerApp Indonesia would fire `/support` with `IONSupportTicket` inside `Support.channels[*]`.

---

## Phase 9 — Reconciliation (a few days later)

After the order is complete, SellerApp Indonesia and BuyerApp Indonesia reconcile financially. BuyerApp Indonesia keeps a platform fee; the balance is remitted to SellerApp Indonesia. This happens via ION's L3 `/reconcile` extension.

```json
{
  "action": "reconcile",
  "message": {
    "settlement": {
      "settlementAttributes": {
        "@type": "ion:ReconcileAttributes",
        "ion:base": { "value": 500000, "currency": "IDR" },
        "ion:adjustments": [
          { "type": "PLATFORM_FEE", "amount": -25000 },
          { "type": "PPN_ADJUSTMENT", "amount": 0 }
        ],
        "ion:finalAmount": { "value": 475000, "currency": "IDR" },
        "ion:taxDeclarations": [
          { "type": "PPN", "rate": 0.11, "base": 500000, "tax": 55000 }
        ]
      }
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
- 10 messages went back and forth per transaction (4 forward + 4 callback + 2 unsolicited status pushes, roughly)
- Every message was cryptographically signed
- ION's L4 core vocabulary carried Indonesian specifics (NPWP, PKP status, address hierarchy, tax breakup)
- ION's L5 sector vocabulary carried retail specifics (availability, price) and logistics specifics (shipment profile, service level, AWB)
- Beckn's L1 core envelope (context, status, commitments, considerations, settlement) held everything together

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

*Last updated v0.5.2-draft. Illustrative — exact payload shapes may evolve; see `schema/core/v2/api/v2.0.0/ion-with-beckn.yaml` for the authoritative schemas.*
