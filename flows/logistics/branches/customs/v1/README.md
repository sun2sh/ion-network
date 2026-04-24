# Customs Branch

Cross-border customs clearance events for LOG-XB spine.

## Applies to
LOG-XB exclusively.

## Sub-branches
`customs-export-clearance`, `customs-import-clearance`, `customs-hold`, `customs-rejection`, `duty-dispute`.

## Customs authority
Import: Bea Cukai (DJBC — Direktorat Jenderal Bea dan Cukai). Export: varies by origin country.

## Hold resolution
BAP provides required documentation via `/update` (invoices, licences, HS code corrections). BPP submits to customs; state transitions back to cleared or rejected.

## Rejection outcomes
Three options: `RETURN_TO_ORIGIN` (reverse-xb branch), `DESTROY_IN_PLACE` (written authorisation required), `RE_EXPORT_TO_THIRD_COUNTRY` (destination + carrier required).
