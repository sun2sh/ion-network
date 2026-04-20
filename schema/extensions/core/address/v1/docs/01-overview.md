# ION Address Extension — Overview

Extends Beckn `Address` with the Indonesian administrative hierarchy below city level.

## Why this exists
Indonesian last-mile delivery relies on RT/RW identifiers. Riders in kampung areas and dense residential zones use RT and RW to locate houses — street names alone are insufficient. Kelurahan and kecamatan are required for logistics zone resolution and tax jurisdiction assignment.

## Use alongside Beckn Address
This pack adds fields — it does not replace Beckn's `street`, `city`, `area_code`. A complete ION delivery address has both sets.

## BPS province codes
All 34 provinces encoded with `BPS-` prefix plus the 2-digit BPS numeric code. Used for serviceability polygon assignment, tax zone determination, and logistics pricing zones.
