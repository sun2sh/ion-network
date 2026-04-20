# Forward Auction (AUC-F)

English ascending auction. Seller sets starting price; buyers bid up. Highest bid wins.

## Applicable categories
Agritech produce lots (coffee, cocoa, mangoes), collectibles, excess inventory clearance, used electronics, art

## Mechanism
- Offer carries `offerType = AUCTION`, `startAt`, `endAt`, `min_bid_increment`, `reserve_price_set`
- `/select` = bid submission (bid amount in offer.price)
- `on_select` acknowledges: LEADING / OUTBID / REJECTED
- BPP sends unsolicited `on_select` when bidder is outbid
- At auction close: BPP sends unsolicited `on_update[AUCTION_CLOSED]` to winner
- Winner proceeds: init → on_init → confirm → on_confirm → standard fulfilment

## Post-award
Identical to B2C-SF from init onwards. Cancellation typically not permitted after confirm for auction winners.

## Performance state machine
`performance-states/v1/states.yaml#standard`
Standard delivery machine from DISPATCHED onwards (post auction-award fulfilment).
