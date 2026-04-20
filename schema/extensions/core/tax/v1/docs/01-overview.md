# ION Tax Extension — Overview

Indonesian tax regimes and calculation fields for consideration breakup lines.

## Tax regimes
- **PPN 11%**: standard VAT on all BKP (taxable goods). Post HPP law (UU 7/2021).
- **PPnBM**: luxury goods tax, applied on top of PPN. Rates: 10%–125% depending on category.
- **PPh22**: income tax on imports and certain purchases. Withheld by buyer.
- **PPh23**: withholding tax on services. Withheld by buyer. 2% for non-NPWP.
- **EXEMPT**: basic foods, books, health services — zero rate.

## Faktur Pajak
PKP sellers must issue a Faktur Pajak (e-Invoice) for each B2B transaction. The `eFakturRef` field carries the DJP-issued reference number. Format: `XXX.XXX-YY.XXXXXXXX`.

## taxIncluded
When `true`, the item price already includes PPN. BAP displays the tax-inclusive price. Breakup still shows the tax component separately for transparency.
