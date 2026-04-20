# B2B Wholesale Prepaid (B2B-PP)

Business buyer purchases wholesale from distributor or brand. Payment upfront.

## Applicable categories
FMCG distribution, electronics wholesale, agritech bulk, fashion wholesale, B2B pharmaceutical

## Key differences from B2C-SF
- MOQ enforced: `offer.minimumOrderQuantity` required; select rejects below MOQ
- Bulk pricing tiers in on_select breakup
- `purchaseOrderReference` required at init (SP / SPK / PO number)
- `invoicePreferences.invoiceType = TAX_INVOICE` standard; requires PKP seller + NPWP buyer
- `fakturPajakReference` assigned by BPP at on_confirm for PKP sellers
- Payment rails: RTGS / BI_FAST preferred over QRIS
- `partialCancellationAllowed` recommended true for multi-line orders
- Delivery receipt: Surat Jalan / Delivery Order reference at DELIVERED

## State machine
`performance-states/v1/states.yaml#standard`
