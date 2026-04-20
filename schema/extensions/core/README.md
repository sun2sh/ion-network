# ION Core Extension Packs

These packs apply to every ION sector — Trade, Mobility, Tourism, Finance, Healthcare, Logistics. A field belongs here when it is required across more than one sector.

## Packs

| Pack | Attaches to | What it covers |
|---|---|---|
| `address/v1` | `beckn:Address` | Indonesian address hierarchy below city level: provinsiCode (34 BPS provinces), kabupatenCode, kelurahan, kecamatan, RT, RW |
| `identity/v1` | `Provider.providerAttributes`, `Contract.contractAttributes` | NPWP (16-digit), NIB (13-digit), NIK, PKP status (VAT registration), legal entity name, business type |
| `payment/v1` | `Settlement.settlementAttributes` | PaymentDeclaration wrapper + typed method objects: QRIS, VirtualAccount, EWallet (10 providers), CashOnDelivery, BankTransfer, BISettlement (BI_FAST/RTGS/SKN), BNPL, CardPayment |
| `tax/v1` | `Consideration.considerationAttributes` | Tax regime (PPN/PPnBM/PPh22/PPh23/EXEMPT), tax category (BKP/JKP/NON_BKP), rate, amount, taxIncluded, eFakturRef |
| `localization/v1` | `Resource.resourceAttributes`, `Provider.descriptor` | LocalisedText pattern — name/shortDesc/longDesc as `{ id, en, ... }` keyed by ISO 639-1 |
| `product/v1` | `Resource.resourceAttributes` | Halal status + MUI cert number, BPOM registration, SNI certificate, SP-PIRT, age restriction |
| `support/v1` | `beckn:Support` | Consumer complaint ticket: category, sub-category, complainant info, description, issueActions (complainant + respondent trail), resolution, escalation level |
| `raise/v1` | ION network channel | NP-to-NP and NP-to-ION issue tickets: type, priority, thread, SLA, resolution — separate from consumer support |
| `rating/v1` | `beckn:Rate` | Rating category (PROVIDER/ITEM/FULFILLMENT/AGENT), value 1–5, feedbackText, feedbackUrl, ratingWindowDays |
| `reconcile/v1` | `Settlement.settlementAttributes` | reconId, contractId, amounts (baseContractAmount, finderFee, withholding), adjustments[], netSettlementAmount, reconStatus, recon_status (ONDC RSF compatible: 01/02/03) |

## Design rules

**Rule 1 — Cross-sector only.** A field belongs in core if and only if it applies across more than one ION sector. Physical product dimensions belong in `trade/resource/v1`. Indonesian address codes belong here because they apply to delivery addresses in every sector.

**Rule 2 — No sector assumptions.** Core packs must not assume Trade, Mobility, or any other sector. A field that only makes sense in the context of physical goods belongs in a sector pack.

**Rule 3 — Composition is safe.** Multiple core packs may attach to the same Beckn extension point simultaneously. A Trade resource carries both `localization/v1` and `product/v1` in its `resourceAttributes`. A Settlement record may carry both `payment/v1` and `reconcile/v1`.

**Rule 4 — Regulatory basis required.** Every field in a core pack must reference its Indonesian regulatory basis in `x-ion-regulatory`. Fields with no regulatory basis and no cross-sector applicability do not belong here.
