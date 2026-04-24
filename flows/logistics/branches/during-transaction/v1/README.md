# During-Transaction Branch

Sub-branches that activate between `/select` and `/on_confirm`. They shape the transaction before it is committed.

## Sub-branches
| Sub-branch | When active | Purpose |
|---|---|---|
| `payment-prepaid-bap-collected` | init → on_confirm | QRIS/VA/EWallet collected by BAP before confirm |
| `payment-cod-bpp-collected` | init → on_confirm | COD — LSP collects cash at delivery |
| `payment-credit-fwa` | init → on_confirm | Post-delivery credit terms under FWA |
| `fwa-activation` | select → confirm | FWA reference in contract — rates and policies inherited |
| `technical-cancel-confirm-bap` | at confirm | BAP handles NACK or timeout gracefully |
| `technical-cancel-confirm-bpp` | at on_confirm | BPP cannot process confirm — NACKs |

## Multiple can be active simultaneously
FWA activation and payment-credit-fwa often coexist. FWA activation and eKYC branch do not — FWA waives eKYC.
