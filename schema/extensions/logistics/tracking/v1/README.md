# tracking/v1 — Logistics Tracking Attributes

Attaches to `beckn:Tracking.trackingAttributes`.

## What it covers

Tracking-specific extension fields that ride on Beckn 2.0's native `Tracking` schema. When a BAP calls `/track`, the BPP returns a `Tracking` object whose `trackingAttributes` slot carries these ION-specific fields.

## Five tracking modes

| trackingType | When to use |
|---|---|
| `LIVE_GPS` | LOG-HYPERLOCAL real-time rider position |
| `AWB_URL` | LOG-PARCEL AWB tracking on carrier's own website |
| `WEBHOOK` | Event-driven push to BAP's registered webhook URL |
| `WEBSOCKET` | Bidirectional streaming for high-throughput integrations |
| `POLLING_API` | Request/response queries (legacy integrations) |

## Relationship to Beckn 2.0 Tracking

Beckn 2.0 `Tracking` schema:
```yaml
Tracking:
  properties:
    contract: { $ref: Contract }     # Native — contract reference
    status: [ACTIVE, INACTIVE]       # Native — high-level status
    url: format: uri                 # Native — URL / handle
    trackingAttributes: Attributes   # ION extends here
```

ION adds refresh interval, credentials, current location snapshot, ETA, agent details, and carrier-redirect pattern via `trackingAttributes`.

## Example — Hyperlocal live GPS

```yaml
message:
  tracking:
    contract:
      id: "gosend-20260422-0abc"
    status: ACTIVE
    url: "wss://track.gosend.com/ws/gosend-20260422-0abc"
    trackingAttributes:
      "@context": "https://schema.ion.id/logistics/v1/tracking/context.jsonld"
      "@type": "ion:LogisticsTrackingAttributes"
      trackingType: WEBSOCKET
      refreshIntervalSeconds: 5
      credentials:
        type: BEARER_TOKEN
        value: "<token>"
        validUntil: "2026-04-22T11:30:00Z"
      currentLocation:
        latitude: -6.2088
        longitude: 106.8456
        timestamp: "2026-04-22T10:45:12Z"
        accuracyMeters: 8
        heading: 142
        speedKmh: 28
      etaMinutes: 7
      agentDetails:
        name: "Budi S."
        phone: "+62811XXXXXXX"
        vehicleType: "motorcycle"
        vehiclePlate: "B 1234 ABC"
```

## Example — Parcel AWB URL

```yaml
message:
  tracking:
    contract:
      id: "jne-20260422-0xyz"
    status: ACTIVE
    url: "https://jne.co.id/tracking?awb=CGK12345678"
    trackingAttributes:
      "@context": "https://schema.ion.id/logistics/v1/tracking/context.jsonld"
      "@type": "ion:LogisticsTrackingAttributes"
      trackingType: AWB_URL
      trackingHandoffToCarrier: true
      carrierTrackingUrlPattern: "https://jne.co.id/tracking?awb={awbNumber}"
```
