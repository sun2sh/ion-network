# ION Rating Extension — Overview

Post-transaction rating for up to four entities per delivery.

## Rating categories
- `PROVIDER`: overall seller quality — product accuracy, packaging, communication
- `ITEM`: specific product quality — taste, fit, condition, as-described
- `FULFILLMENT`: delivery experience — speed, handling, condition on arrival
- `AGENT`: delivery agent — behaviour, punctuality, professionalism

## Rating window
`ratingWindowDays` declared by BPP at on_confirm. Typical: 7 days after DELIVERED. After expiry, the `/rate` API returns an error.

## Feedback
`feedbackText` is free text (max 1000 chars). BPP may return `feedbackUrl` in on_rate for consumer to provide extended feedback on their own platform.
