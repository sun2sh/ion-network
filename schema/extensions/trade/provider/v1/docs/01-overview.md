# Trade Provider Extension — Overview

Seller operational state and configuration. Published in catalog; used for discovery filtering and UI rendering.

## storeStatus
`TEMPORARILY_CLOSED` requires `temporaryClosureEnd`. BAP should suppress ordering UI and display the closure end time to consumer.

## operatingHours
Typed array — different hours for ORDER acceptance, DELIVERY, SELF_PICKUP, and PREPARATION (kitchen hours). BAP uses ORDER hours to gate the checkout flow; DELIVERY hours for delivery slot selection.

## invoicingModel
`CENTRAL`: one legal entity invoices for all outlets (e.g., a national chain). `PER_FULFILMENT_CENTRE`: each FC invoices independently (e.g., franchise model where each franchisee is a separate tax entity).
