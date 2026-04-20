# B2C Live Commerce (B2C-LIVE)

Commerce pattern for orders placed from live streams, short video, OTT shoppable content, affiliate links, and group buys.

## Applicable categories
Fashion, Beauty, Electronics, FMCG, Home & Kitchen, Agritech, Food QSR.

## Source channels covered
- **LIVE_STREAM** — Shopee Live, Tokopedia Play, TikTok Shop-style live sessions
- **SHORT_VIDEO** — shoppable reels, creator content with product pins
- **OTT_EMBEDDED** — Vidio, Netflix, Disney+ Hotstar, iflix, Viu, Genflix, WeTV in-video commerce (watch a movie or match, buy the item)
- **SOCIAL_POST** — Instagram, Facebook shoppable posts routed through ION
- **AFFILIATE_LINK** — creator affiliate links with commission attribution
- **GROUP_BUY** — group purchase unlocking volume discount
- **SHOPPABLE_AD** — in-ad direct purchase

## Key differences from B2C-SF

- **Source attribution mandatory.** `contractAttributes.liveCommerceContext` required at select, carries source channel, streamer ID, OTT content reference, group-buy session ID.
- **Time-bounded offers.** Offer `startAt` and `endAt` strictly enforced — BPP returns ION-3010 for out-of-window orders.
- **Short reservation window.** `reservationWindowSeconds` typically 60-180s for flash-style live drops. BAP must show urgency UI.
- **Queue mechanics.** When `queueEnabled=true`, BPP returns `queuePosition` and `estimatedWaitSeconds` in on_select for high-demand drops.
- **Stock caps.** `totalStockCap` and `perUserQuantityCap` enforced atomically; ION-3008 returned when exceeded.
- **Streamer/affiliate commission.** Declared in consideration breakup (`STREAMER_COMMISSION`, `AFFILIATE_COMMISSION` line types). Settled separately at reconcile.
- **Group-buy pending state.** Orders via GROUP_BUY channel remain `ACTIVE_PENDING_GROUP` until minimum participants reached.

## OTT embedded commerce — how it works

Consumer is watching content on Vidio/Netflix/Disney+ Hotstar. The OTT platform surfaces a shoppable moment (jersey during a match, outfit in a movie). Tapping the moment launches ION select with:

- `sourceChannel: OTT_EMBEDDED`
- `ottPlatform: VIDIO`
- `ottContentId: VIDIO-MATCH-PERSIJA-PERSIB-2026-04-19`
- `ottTimestampSeconds: 2847` (playback position when tapped)

The OTT platform acts as a BAP surface (may be the same legal BAP as a marketplace or a distinct one); the product seller is the BPP. OTT platform may earn a revenue share declared as an `AFFILIATE_COMMISSION` line.

## Performance state machine
`performance-states/v1/states.yaml#standard`

Standard delivery from DISPATCHED onwards. For group-buy, `PLANNED` may extend while awaiting minimum participants.

## Applicable branches
All branches available. Flash-sale cancellation is typically not permitted after confirm — enforced by offer's cancellationPolicy.

## Regulatory
- **Kemendag Permen 31/2023** — social commerce must operate as e-commerce. ION Live Commerce is a compliant e-commerce flow; the `sourceChannel` field records the origin for transparency without making it a social media transaction.
- **UU 11/2008 tentang ITE** — electronic transactions; applies as standard.
- **OJK POJK 69/POJK.05/2016** — if live session promotes financial products, additional OJK compliance applies (not covered in Trade sector).
