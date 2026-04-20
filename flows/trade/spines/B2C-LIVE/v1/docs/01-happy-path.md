# B2C-LIVE — Happy Path

See `spine.yaml` for the full step-by-step sequence. Key phases:

1. **Live session starts.** BPP publishes incremental catalog update binding offers to the live session (`startAt`, `endAt`, short `reservationWindowSeconds`).
2. **Consumer discovers during session.** BAP surfaces the live session; consumer taps a featured product.
3. **Select with attribution.** BAP sends `/select` including `liveCommerceContext` (source channel, streamer ID, OTT content ref, etc.).
4. **On_select with commission.** BPP returns quote including `STREAMER_COMMISSION` / `AFFILIATE_COMMISSION` breakup line. If queue is enabled, returns queue position.
5. **Short-fuse init → confirm.** Reservation window typically 60-180s; consumer must proceed quickly.
6. **On_confirm.** Order confirmed. For group-buy, state may be `ACTIVE_PENDING_GROUP` until min participants reached.
7. **Standard fulfilment.** Identical to B2C-SF from here.
8. **Reconcile with commission split.** `streamerCommissionAmount` / `affiliateCommissionAmount` settled to creator's subscriber ID separately from BPP payout.

For OTT-embedded flow specifically: the consumer may tap a product during playback, or after playback completes (if the OTT platform preserves the shoppable moment). `ottTimestampSeconds` captures the original in-content moment regardless of when the tap happens.
