# ION Tax Extension — Overview

Indonesian tax regimes and calculation fields for consideration breakup lines.

## Tax regimes
- **PPN**: standard VAT on all BKP (taxable goods). Current standard rate is 11% (PMK 131/2024 under UU 7/2021 HPP) — implementations MUST source the applicable rate from current DJP/PMK regulation, not hardcode it.
- **PPnBM**: luxury goods tax, applied on top of PPN. Rates vary by category (typical range 10%–75% under current regulations — check DJP for the applicable schedule).
- **PPh22**: income tax on imports and certain purchases. Withheld by buyer. Applicable rate per current PMK.
- **PPh23**: withholding tax on services. Withheld by buyer. Applicable rate per current PMK (higher rate applies for non-NPWP recipients under UU PPh Pasal 23).
- **EXEMPT**: basic foods, books, health services — zero rate.

## Faktur Pajak
PKP sellers must issue a Faktur Pajak (e-Invoice) for each B2B transaction. The `eFakturRef` field carries the DJP-issued reference number. Format: `XXX.XXX-YY.XXXXXXXX`.

## taxIncluded
When `true`, the item price already includes PPN. BAP displays the tax-inclusive price. Breakup still shows the tax component separately for transparency.
