# LOG-RORO — Roll-on/Roll-off

Self-accompanied cargo on Ro-Ro vessels and ferries. The consignor typically drives or accompanies the cargo onto the vessel at origin port and off at destination port.

## Applicable service types
Strait crossings (Java-Bali Ketapang-Gilimanuk, Java-Sumatra Merak-Bakauheni), inter-island Ro-Ro freight with accompanying drivers, motorcycle and car ferry services. Covers ASDP Indonesia Ferry and private Ro-Ro operators.

## Delta from LOG-FREIGHT
- Resource is a vehicle (car, truck, trailer, motorcycle), not a cargo unit
- Consignor and consignee often the same party (owner/driver rides along)
- No pickup/drop addresses — drive-in and drive-out at ports
- Ticket reference replaces bill-of-lading
- Port events (CHECKED_IN, BOARDED, SAILED, DISEMBARKED, EXITED_PORT) replace freight events
- Driver identity and vehicle registration mandatory
- `PER_VESSEL_SLOT` capacity model

## Vehicle categories
Passenger car, light truck, heavy truck, motorcycle, trailer, bus. Each has different slot allocation and pricing on the sailing.

## Available branches
- `cancellation` (window ends at CHECKED_IN)
- `missed-sailing` (if vehicle doesn't board in time — rebook or refund per policy)
- Cross-cutting: `support`, `rating`, `raise`

## Key fields introduced
`portsServed[]`, `vehicleCategoriesAccepted[]`, `sailingSchedule[]`, `crossingDuration`, `vesselCapacityPerSailing`, `requestedSailing`, `confirmedSailing`, `boardingWindow`, `ticketReference`, `boardingGate`, `vehicleDetails`, `vehicleRegistration`, `DRIVER` participant role.
