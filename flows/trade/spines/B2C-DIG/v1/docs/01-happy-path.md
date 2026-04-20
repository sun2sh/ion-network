# B2C-DIG — Happy Path

See `spine.yaml` for the full API sequence.

Typical flow — pulsa top-up example:

1. Consumer enters mobile number in BAP → BAP sends `/select` with `digital.target.type=MOBILE_NUMBER` and `digital.target.value=081234567890`.
2. BPP validates number with operator (inquiry API) → returns customer name in on_select, allows consumer confirmation.
3. Consumer selects denomination (Pulsa Rp 50.000) → standard init → on_init → confirm.
4. On confirm, BPP immediately calls operator API → state becomes `PENDING_OPERATOR`.
5. Operator confirms pulsa credited (usually < 10 seconds) → state transitions to `DELIVERED`. Contract `COMPLETE`.
6. If operator fails → state `DELIVERY_FAILED` → automatic refund triggered.

Voucher flow — game currency example:

1. Consumer enters game user ID → BAP sends `/select` with `digital.target.type=GAME_USER_ID`.
2. Issuer (Moonton/Garena) validates user ID exists → on_select returns validation.
3. Confirm → BPP calls issuer API → diamonds/coins credited to game account → `DELIVERED`.
4. Some games require redemption code delivery — `redemptionCode` in on_status[DELIVERED].
