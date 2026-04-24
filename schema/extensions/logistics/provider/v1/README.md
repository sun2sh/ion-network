# provider/v1

Logistics provider attributes. Attaches to `beckn:Provider.providerAttributes`.

## What it covers
Identity and licences (NIB, SIUP, ALFI, ASPERINDO), provider model (carrier vs forwarder vs aggregator vs 3PL/4PL vs warehouse), spines and modes supported, geographic coverage, capabilities (cold chain, hazmat, high-value, customs brokerage), operating hours, fleet type, warehouse locations.

## Mandatory fields (always)
`nibRegistered`, `providerCategory`, `spinesSupported`, `modesSupported`, `coverage[]`, `operatingHours[]`

## Conditional fields
`siupNumber` (freight and warehouse), `beaCukaiLicenceNumber` (LOG-XB providers), `coldChainTemperatureZones` (if coldChainCertified=true), `hazmatClasses` (if hazmatCertified=true), `warehouseLocations[]` (LOG-WAREHOUSE providers), `maxDeliveryRadiusKm` (LOG-HYPERLOCAL providers).

## Used in spines
All logistics spines. Fields applicable per spine are documented in each spine's conditional field list.
