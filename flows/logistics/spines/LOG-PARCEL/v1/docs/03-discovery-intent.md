# ION Logistics — DiscoverAction Intent Patterns

When a BAP calls Beckn 2.0 `/discover`, it sends a `DiscoverAction` carrying an `intent` object. This document specifies the intent patterns BAPs use to query ION Logistics BPPs.

Two equivalent query expressions exist:
- **Flat text search** — `textSearch` field; natural-language query
- **Structured intent** — `intent` object with fields targeting resources, offers, and providers

BAPs SHOULD use structured intent whenever they have the data to populate it. BPPs MUST support both patterns.

## Intent pattern examples

### Pattern 1 — Parcel rate lookup (Jakarta → Surabaya, 2.5kg)

```json
{
  "context": {
    "action": "discover",
    "version": "2.0.0",
    "bapId": "tokopedia.com",
    "bapUri": "https://api.tokopedia.com/ion",
    "networkId": "ion.id/logistics",
    "transactionId": "550e8400-e29b-41d4-a716-446655440000",
    "messageId": "550e8400-e29b-41d4-a716-446655440001",
    "timestamp": "2026-04-22T09:00:00.000Z"
  },
  "message": {
    "intent": {
      "provider": {
        "providerAttributes": {
          "@context": "https://schema.ion.id/logistics/v1/provider/context.jsonld",
          "@type": "ion:LogisticsProviderAttributes",
          "spinesSupported": ["LOG-PARCEL"]
        }
      },
      "offer": {
        "offerAttributes": {
          "@context": "https://schema.ion.id/logistics/v1/offer/context.jsonld",
          "@type": "ion:LogisticsOfferAttributes",
          "serviceLevel": "NEXT_DAY",
          "availableOnCod": false
        }
      },
      "fulfillment": {
        "stops": [
          {
            "type": "START",
            "location": {
              "address": {
                "postalCode": "10110",
                "addressCountry": "ID"
              }
            }
          },
          {
            "type": "END",
            "location": {
              "address": {
                "postalCode": "60111",
                "addressCountry": "ID"
              }
            }
          }
        ]
      },
      "item": {
        "resourceAttributes": {
          "@context": "https://schema.ion.id/logistics/v1/resource/context.jsonld",
          "@type": "ion:LogisticsResourceAttributes",
          "serviceType": "PARCEL",
          "weight": { "value": 2.5, "unit": "kilogram" },
          "dimensions": { "length": 30, "width": 20, "height": 15, "unit": "centimeter" }
        }
      }
    }
  }
}
```

### Pattern 2 — Hyperlocal on-demand rider

```json
{
  "message": {
    "intent": {
      "provider": {
        "providerAttributes": {
          "@context": "https://schema.ion.id/logistics/v1/provider/context.jsonld",
          "@type": "ion:LogisticsProviderAttributes",
          "spinesSupported": ["LOG-HYPERLOCAL"]
        }
      },
      "offer": {
        "offerAttributes": {
          "@context": "https://schema.ion.id/logistics/v1/offer/context.jsonld",
          "@type": "ion:LogisticsOfferAttributes",
          "serviceLevel": "INSTANT",
          "transportMode": "motorcycle"
        }
      },
      "fulfillment": {
        "stops": [
          {
            "type": "START",
            "location": {
              "gps": "-6.2088,106.8456",
              "address": { "postalCode": "12190", "addressCountry": "ID" }
            }
          },
          {
            "type": "END",
            "location": {
              "gps": "-6.2146,106.8452",
              "address": { "postalCode": "12210", "addressCountry": "ID" }
            }
          }
        ]
      }
    }
  }
}
```

### Pattern 3 — Freight FCL booking (ocean)

```json
{
  "message": {
    "intent": {
      "offer": {
        "offerAttributes": {
          "@context": "https://schema.ion.id/logistics/v1/offer/context.jsonld",
          "@type": "ion:LogisticsOfferAttributes",
          "transportMode": "sea",
          "consolidationType": "FCL"
        }
      },
      "fulfillment": {
        "stops": [
          {
            "type": "START",
            "location": { "address": { "postalCode": "IDSUB" } }
          },
          {
            "type": "END",
            "location": { "address": { "postalCode": "SGSIN" } }
          }
        ]
      },
      "item": {
        "resourceAttributes": {
          "@context": "https://schema.ion.id/logistics/v1/resource/context.jsonld",
          "@type": "ion:LogisticsResourceAttributes",
          "serviceType": "FREIGHT",
          "cargoManifest": [
            {
              "description": "Consumer electronics",
              "hsCode": "8517.12.00",
              "quantity": 500,
              "unitWeight": 0.17
            }
          ]
        }
      }
    }
  }
}
```

### Pattern 4 — Cross-border air (Indonesia → Japan, pharma)

```json
{
  "message": {
    "intent": {
      "offer": {
        "offerAttributes": {
          "@context": "https://schema.ion.id/logistics/v1/offer/context.jsonld",
          "@type": "ion:LogisticsOfferAttributes",
          "serviceLevel": "STANDARD_2_3D",
          "transportMode": "air",
          "incotermsSupported": ["DDP", "DAP"]
        }
      },
      "fulfillment": {
        "stops": [
          {
            "type": "START",
            "location": { "address": { "addressCountry": "ID", "postalCode": "10110" } }
          },
          {
            "type": "END",
            "location": { "address": { "addressCountry": "JP", "postalCode": "100-0001" } }
          }
        ]
      },
      "item": {
        "resourceAttributes": {
          "@context": "https://schema.ion.id/logistics/v1/resource/context.jsonld",
          "@type": "ion:LogisticsResourceAttributes",
          "serviceType": "PARCEL",
          "productCategory": "PHARMA",
          "temperatureRequirement": {
            "controlled": true,
            "minTempC": 2,
            "maxTempC": 8,
            "category": "CHILLED"
          },
          "weight": { "value": 15, "unit": "kilogram" },
          "hsCodes": ["3004.90.59"]
        }
      }
    }
  }
}
```

### Pattern 5 — Simple text search fallback

When BAP lacks structured data or wants to fan-out to many BPPs:

```json
{
  "message": {
    "textSearch": "parcel delivery jakarta to surabaya next day 2.5kg"
  }
}
```

BPPs handle text search per their own NLU or keyword-matching logic. Structured intent returns deterministic results.

## BPP response pattern (`/on_discover`)

The BPP returns catalogs via `/on_discover`:

```json
{
  "context": {
    "action": "on_discover",
    "version": "2.0.0",
    ...
  },
  "message": {
    "catalogs": [
      {
        "bppId": "jne.co.id",
        "bppUri": "https://api.jne.co.id/ion",
        "providers": [...],
        "resources": [...],
        "offers": [...]
      }
    ]
  }
}
```

Only offers matching the intent are returned. If the intent specifies a corridor not served by the BPP, an empty catalog is returned (still wrapped in the catalogs array).

## Combining discovery with subscription

BAPs can use BOTH patterns:
1. **Subscribe** to BPP catalog updates via `/catalog/subscription` for continuous refresh
2. **Discover** via `/discover` for one-off queries with specific intent (e.g. spot rate lookups)

Both result in `/on_discover` callbacks. BAP de-duplicates by `context.transactionId`.
