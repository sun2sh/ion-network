# B2C Digital Goods (B2C-DIG)

Digital goods commerce on ION. No physical fulfilment — delivery is electronic.

## Applicable categories
Pulsa, data packages, electricity tokens (PLN), utility bill payments (water, PDAM, internet), BPJS contributions, gift cards, game currencies (Mobile Legends, Free Fire, Valorant, Genshin Impact), streaming service vouchers (Netflix, Disney+ Hotstar, Spotify), e-wallet top-ups, transport credits.

## Resource types used
- `DIGITAL_VOUCHER` — voucher codes, gift cards, game currency
- `DIGITAL_TOP_UP` — pulsa, data, electricity tokens, bill payments
- `DIGITAL_SUBSCRIPTION` — streaming service access, time-bound subscriptions

Each resource carries a `digital` sub-object with denomination, target type, delivery method, and category-specific fields.

## Key differences from B2C-SF

- **No shipping.** No fulfilment location, no logistics provider, no AWB, no delivery agent.
- **Fast fulfilment.** Digital fulfilment typically completes in seconds. State machine is `digital` — PENDING_OPERATOR → DELIVERED or DELIVERY_FAILED.
- **Target identifier mandatory.** Mobile number for pulsa, meter number for PLN, game user ID for game currency. Declared in `digital.target`.
- **Operator validation.** For pulsa and bill pay, BPP validates target before accepting (operator inquiry returns customer name for confirmation).
- **Typically non-refundable after delivery.** Pulsa delivered to phone cannot be recalled. Vouchers may be refundable if unredeemed.
- **Cancellation window very narrow.** Only possible before operator call is made.

## Performance state machine
`performance-states/v1/states.yaml#digital`

## Common operators / issuers
| Category | Issuers |
|---|---|
| Pulsa/Data | Telkomsel, XL, Indosat, Tri, Smartfren |
| Electricity | PLN (Perusahaan Listrik Negara) |
| Water | PDAM (per province) |
| Insurance | BPJS Kesehatan, BPJS Ketenagakerjaan |
| Gaming | Moonton (ML), Garena (FF), Riot Games (Valorant), MiHoYo (Genshin) |
| Streaming | Netflix, Disney+ Hotstar, Vidio, Iflix, Spotify |
| E-wallet | OVO, GoPay, DANA, ShopeePay top-up |

## Tax treatment
Digital goods often have specific tax treatment:
- **Pulsa and data packages**: PPN 11% applies on reseller margin (not face value) per PMK 6/2021
- **Bill payments**: typically exempt from PPN (pass-through)
- **Vouchers and gift cards**: PPN on issuance, not on redemption
- **Cross-border streaming (Netflix)**: PPN PMSE applies (PMK 48/2020)

BPP declares correct `ppnRate` per item based on category.

## Regulatory
- **UU 36/1999 tentang Telekomunikasi** — pulsa and mobile data regulated under telecoms law
- **UU 8/1999 tentang Perlindungan Konsumen** — applies to all digital purchases
- **PMK 6/2021** — PPN on pulsa, kartu perdana, token listrik
- **PMK 48/2020** — PPN PMSE for cross-border digital services
