# Trade Consideration Extension — Overview

Price breakup line types and tax rate declarations for the trade sector.

## breakupLineType
Every line in `quote.breakup[]` must carry a `breakupLineType`. The full set: ITEM, DELIVERY, TAX, TAX_PPNBM, HANDLING, PACKAGING, INSURANCE, PROVIDER_BENEFIT, BUYER_BENEFIT, COD_FEE, TRADE_IN, LOYALTY_REDEEM, FINANCE_CHARGE, GIFT_WRAP, PLATFORM_FEE.

## Tax lines
`TAX` line carries `ppnRate = 0.11`. `TAX_PPNBM` line carries `ppnbmRate` for luxury goods. Both are separate breakup lines — not embedded in the ITEM line.

## Discount lines
`PROVIDER_BENEFIT`: seller-funded discount. `BUYER_BENEFIT`: BAP-funded cashback or platform voucher. `subsidyBreakup` in the offer declares who funds what proportion.
