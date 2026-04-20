# B2G Government Procurement (B2G)

Seller to government entity (K/L/D/I). Governed by Perpres 16/2018. LKPP e-Katalog compatible.

## Applicable categories
All — government procures from all Trade categories


## Performance state machine
`performance-states/v1/states.yaml#standard`
Plus BAST signing step before SP2D payment is triggered.

## Key differences from B2B-PP
- Government identity: `kldi_code` (Kementerian/Lembaga/Daerah/Institusi code)
- `sp_reference` (Surat Pesanan) or `spk_reference` (Surat Perintah Kerja)
- `dipa_reference` — budget line (Daftar Isian Pelaksanaan Anggaran)
- `tkdn_percentage` — Tingkat Komponen Dalam Negeri (local content %)
- `lkpp_catalog_id` — links product to LKPP e-Katalog listing
- Payment via SP2D (Surat Perintah Pencairan Dana) through KPPN — POST_FULFILLMENT
- BAST required before payment: Berita Acara Serah Terima signed by government official
- `bast_reference`, `bast_signed_by`, `bast_signed_at` in on_update after delivery
- PPh22 withheld by government: 1.5% deducted from payment; `pph22_withheld` declared
- `bukti_potong_reference` — PPh22 withholding certificate issued by government buyer
- Regulatory: Perpres 16/2018, Perpres 12/2021, PMK 190/PMK.05/2012
