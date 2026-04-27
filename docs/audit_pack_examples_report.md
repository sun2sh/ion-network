# Examples audit (v2) — pack-content vs full-payload

- pack-content examples: 13
- full-payload examples: 10

Different rules per kind. pack-content must declare @context/@type and must NOT
use Beckn-named wrappers. full-payload must validate as Beckn-shaped.


| File | Type | Issues |
|---|---|---:|
| `flows/logistics/spines/LOG-FREIGHT/v1/examples/on-confirm-fcl.json` | full-payload | 0 |
| `flows/logistics/spines/LOG-HYPERLOCAL/v1/examples/catalog-publish.json` | full-payload | 0 |
| `flows/logistics/spines/LOG-PARCEL/v1/examples/catalog-publish.json` | full-payload | 0 |
| `flows/logistics/spines/LOG-PARCEL/v1/examples/on-confirm-response.json` | full-payload | 0 |
| `flows/logistics/spines/LOG-PARCEL/v1/examples/select-request.json` | full-payload | 0 |
| `flows/logistics/spines/LOG-RORO/v1/examples/on-confirm-ketapang-gilimanuk.json` | full-payload | 0 |
| `flows/logistics/spines/LOG-WAREHOUSE/v1/examples/on-confirm-fba-style.json` | full-payload | 0 |
| `flows/logistics/spines/LOG-XB/v1/examples/on-confirm-ddp-air.json` | full-payload | 0 |
| `flows/trade/spines/B2C-SF/v1/examples/on_confirm_response.json` | full-payload | 0 |
| `flows/trade/spines/B2C-SF/v1/examples/select_request.json` | full-payload | 0 |
| `schema/extensions/core/address/v1/examples/address-jakarta.json` | pack-content | 0 |
| `schema/extensions/core/identity/v1/examples/business-identity-pt.json` | pack-content | 0 |
| `schema/extensions/core/identity/v1/examples/individual-identity.json` | pack-content | 0 |
| `schema/extensions/core/participant/v1/examples/participant-consignee-and-merchant.json` | pack-content | 0 |
| `schema/extensions/trade/commitment/v1/examples/pizza-order.json` | pack-content | 0 |
| `schema/extensions/trade/consideration/v1/examples/pizza-order-breakup.json` | pack-content | 0 |
| `schema/extensions/trade/contract/v1/examples/b2c-confirmed-order.json` | pack-content | 0 |
| `schema/extensions/trade/offer/v1/examples/electronics-offer.json` | pack-content | 0 |
| `schema/extensions/trade/offer/v1/examples/food-offer.json` | pack-content | 0 |
| `schema/extensions/trade/performance/v1/examples/dispatched-with-agent.json` | pack-content | 0 |
| `schema/extensions/trade/resource/v1/examples/agritech-beras.json` | pack-content | 0 |
| `schema/extensions/trade/resource/v1/examples/electronics-smartphone.json` | pack-content | 0 |
| `schema/extensions/trade/resource/v1/examples/food-qsr-pizza.json` | pack-content | 0 |
| **TOTAL** | | **0** |
