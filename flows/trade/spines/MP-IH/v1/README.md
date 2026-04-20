# Marketplace Inventory Held (MP-IH)

Marketplace holds physical stock. Single BPP (the marketplace) serves multiple brands.

## Architecture
```
Consumer → Marketplace BAP
           Marketplace BPP ← holds stock in own FC
           Brand A, Brand B, Brand C (each = a provider in catalog)
```
The marketplace IS the BPP. Brands supply stock on consignment or 1P. The marketplace picks, packs, and ships.

## Key differences from B2C-SF
- `invoicingModel = CENTRAL` — marketplace invoices, not individual brand
- `fulfillingLocationId` = marketplace FC ID (fast assignment at on_confirm)
- Marketplace SLA guarantees apply — faster and more reliable than 3P
- Returns handled by marketplace FC
- Brand payout is handled by marketplace's internal financial system — not via ION reconcile

## State machine
`performance-states/v1/states.yaml#standard`
