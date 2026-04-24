# ION — Onboarding and Authentication

**Read this before writing any integration code.** This document covers subscriber registration, request signing, callback authentication, and conformance testing. It applies to every ION sector (trade, logistics, future mobility/finance/tourism/healthcare) — authentication is network-wide, not sector-specific. All authentication follows Beckn 2.0.0 specification exactly.

---

## 1. Registry and subscriber model

Network participants register on **`dedi.global`** per Beckn 2.0.0 convention. ION operates as a namespace on dedi.global — `ion.id/{sector}@dedi.global` where `{sector}` is the active sector (`trade`, `logistics`, etc).

### Environments

| Environment | Purpose | Registry host |
|---|---|---|
| `staging` | Developer sandbox, synthetic data | `staging.dedi.global` |
| `uat` | Pre-production with real partners | `uat.dedi.global` |
| `production` | Live network | `dedi.global` |

### Subscriber identity

Every participant has a unique `subscriberId`, typically an FQDN (e.g. `jne.co.id`, `tokopedia.com`).

### Registration request

```http
POST /v1/subscribers
Host: staging.dedi.global
Content-Type: application/json

{
  "subscriberId": "seller.example.id",
  "subscriberRole": "BPP",
  "subscriberType": "MERCHANT",
  "networkIds": ["ion.id/trade"],
  "spinesSupported": ["B2C-SF", "B2C-MTO"],
  "legalEntity": {
    "registeredName": "PT Example Seller Indonesia",
    "nibNumber": "1234567890123",
    "npwp": "0123456789012345"
  },
  "endpoints": {
    "baseUrl": "https://api.seller.example.id/ion",
    "callback": "https://api.seller.example.id/ion/callback"
  },
  "signingKeys": [
    {
      "uniqueKeyId": "c1f78a2e-8e72-41f3-9e88-8f2c33dd72b4",
      "algorithm": "ed25519",
      "publicKey": "<base64-ed25519-public-key>",
      "validFrom": "2026-04-22T00:00:00Z",
      "validUntil": "2027-04-22T00:00:00Z"
    }
  ]
}
```

A logistics-sector BPP registration would use `"networkIds": ["ion.id/logistics"]`, `"subscriberType": "LSP"`, and `"spinesSupported"` drawn from the logistics spine codes (LOG-PARCEL, LOG-FREIGHT, etc). The rest of the payload shape is identical.

---

## 2. Request signing — Beckn 2.0.0 Signature

Every ION API request MUST carry an HTTP Signature in the `Authorization` header, per Beckn 2.0.0 spec exactly.

### keyId — pipe-separated triple

```
keyId="{subscriberId}|{uniqueKeyId}|{algorithm}"
```

Example:
```
keyId="jne.co.id|c1f78a2e-8e72-41f3-9e88-8f2c33dd72b4|ed25519"
```

**Incorrect:** `keyId="jne-key-2026"` (single value) — will be rejected by a conformant Beckn 2.0.0 receiver.

### Header format

```
Authorization: Signature keyId="jne.co.id|c1f78a2e-8e72-41f3-9e88-8f2c33dd72b4|ed25519",
                         algorithm="ed25519",
                         created="1745322000",
                         expires="1745322300",
                         headers="(created) (expires) digest",
                         signature="<base64Signature>"
```

### Algorithm

MUST be `ed25519`. Beckn 2.0.0 does not permit RSA, ECDSA, or other schemes.

### Signing string

Covers exactly three headers in order:
```
(created): 1745322000
(expires): 1745322300
digest: BLAKE-512={base64DigestOfRequestBody}
```

The digest is BLAKE2b-512 of the raw request body, Base64-encoded.

### Validation on receipt

1. Parse `keyId` into `subscriberId`, `uniqueKeyId`, `algorithm`
2. Resolve `subscriberId` via registry; fetch active public key for `uniqueKeyId`
3. Validate signature against signing string using Ed25519
4. Confirm `created < now < expires`
5. Confirm digest matches body hash

Failure returns HTTP 401 with `ION-LOG-9002` (INVALID_SIGNATURE).

---

## 3. CounterSignature — MANDATORY on every Ack response body

Per Beckn 2.0.0, every `Ack` response body MUST carry a `CounterSignature` proving the receiver authenticated, received, and processed the inbound request.

### CounterSignature structure

Same wire format as Signature — same keyId, algorithm, created, expires, headers, signature attributes. Differences:

| Property | Value |
|---|---|
| Signer | response receiver (not request sender) |
| Location | `Ack` response body (not Authorization header) |
| `digest` | BLAKE-512 of the Ack body (not inbound request) |

### CounterSignature signing string

```
(created): {unixTimestamp}
(expires): {unixTimestamp}
digest: BLAKE-512={base64DigestOfAckBody}
(request-digest): BLAKE-512={base64DigestOfInboundRequestBody}
(message-id): {messageId}
```

The extra `(request-digest)` and `(message-id)` tie the CounterSignature to the specific inbound request.

### Ack response structure

```json
{
  "status": "ACK",
  "signature": "Signature keyId=\"bpp.co.id|uuid|ed25519\",algorithm=\"ed25519\",created=\"1745322001\",expires=\"1745322301\",headers=\"(created) (expires) digest (request-digest) (message-id)\",signature=\"<base64>\""
}
```

Missing or invalid CounterSignature returns `ION-LOG-9006` (COUNTER_SIGNATURE_MISSING_OR_INVALID).

---

## 4. Context schema compliance

### version — literal const

```yaml
version: "2.0.0"
```

Exactly this string. Any other value fails schema validation.

### action — matched to endpoint

Action name must match the endpoint. `/on_confirm` carries `context.action: "on_confirm"`.

### networkId format

```
networkId: "ion.id/logistics@dedi.global"
```

Or `"ion.id/logistics"` if dedi-host is default. Format: `{namespace_id}/{registry_id}@{dedi-host}`.

### transactionId, messageId

Both UUID format. `transactionId` persists across the full transaction (discover → confirm → complete); `messageId` regenerates per request/callback pair.

### timestamp, ttl

`timestamp` in RFC 3339 format. `ttl` in ISO 8601 duration (e.g. `PT5M`).

### schemaContext (optional but recommended)

Array of JSON-LD context URIs used in the message:

```json
"schemaContext": [
  "https://schema.ion.id/logistics/v1/provider/context.jsonld",
  "https://schema.ion.id/logistics/v1/offer/context.jsonld"
]
```

### try (sandbox mode)

Per Beckn 2.0.0: `context.try: true` on `/update`, `/cancel`, `/rate`, `/support`. ION also enables on `/reconcile` (ION extension).

---

## 5. Key management

### Key rotation

Overlapping validity, minimum 30 days:

```
Key A — uniqueKeyId: uuid-a, validFrom: 2026-01-01, validUntil: 2026-06-30
Key B — uniqueKeyId: uuid-b, validFrom: 2026-06-01, validUntil: 2026-12-31
```

During overlap, either key is accepted. After `validUntil` of Key A, only Key B is accepted.

### Key revocation

`POST /v1/subscribers/{subscriberId}/keys/{uniqueKeyId}/revoke` with signed revocation reason. Registry propagates within minutes.

### Storage

- HSM or KMS for production
- Separate keys per environment
- Rotate at least annually
- Never transmit private keys

---

## 6. Callback authentication

Callbacks are signed by sender (same Ed25519 scheme as requests).

### Callback URL registration

Every subscriber declares a single base callback URL. Network routes all `/on_*` to `{baseUrl}/{action}`.

### Callback retry

```
2xx                        accepted, no retry
408/429/5xx                retry with exponential backoff (1s, 2s, 4s, 8s, 16s, 32s; cap 5)
4xx (non-408/429)          no retry, surface as ION-LOG-9005
```

---

## 7. Onboarding flow

```
Day 1       Submit registration to staging dedi.global
Day 1       Registry provisions subscriberId + sandbox keys
Day 2-5     Integrate /catalog/publish
Day 5-10    Implement /on_select, /on_init, /on_confirm, /on_status
Day 10-15   Implement applicable branches per spine
Day 15-20   Staging conformance suite
Day 20      Request UAT access
Day 21-30   UAT with named partners
Day 30-45   UAT reliability & load testing
Day 45      Request production access
```

---

## 8. Conformance suite coverage

### Transport compliance
- Signature keyId pipe-triple format, algorithm=ed25519, digest BLAKE-512
- CounterSignature on every Ack body
- Correct header casing and formats

### Schema compliance
- `context.version == "2.0.0"` on every message
- Every extension `Attributes` carries `@context` and `@type`
- Enums resolve against schema

### Beckn 2.0.0 state compliance
- `Contract.status` uses only {DRAFT, ACTIVE, CANCELLED, COMPLETE}
- `Settlement.status` uses only {DRAFT, COMMITTED, COMPLETE}
- `Contract.commitments[]` has `minItems: 1`
- No use of deprecated `publishDirectives`

### ION extension compliance
- `/raise` family endpoints reachable
- `/reconcile`, `/on_reconcile` endpoints reachable
- `context.try` supported on all extended actions

Pass criteria: 100% transport & schema, ≥95% spine/branch coverage.

---

## 9. Rate limits

Production BPP default:
- Outbound: 100 req/s burst, 50 req/s sustained
- Inbound callbacks: no rate limit (gateway buffers)
- `/catalog/publish`: 1/hour per catalog shard
- `/catalog/pull`: 60/hour per BAP

---

## 10. Security compliance

- TLS 1.3 only
- OWASP Top 10 scan quarterly
- SOC 2 Type II or ISO 27001 (waived first 12 months)
- Security incidents within 72 hours via `/raise` with `type: SECURITY_INCIDENT`
- Log request/response 2 years (Indonesian PDP Law)
- Encrypt PII at rest (AES-256 minimum)

---

## See also

- **New to ION?** [`ION_Start_Here.md`](ION_Start_Here.md)
- **Glossary?** [`ION_Glossary.md`](ION_Glossary.md)
- **Conformance testing?** [`ION_Beckn_Conformance.md`](ION_Beckn_Conformance.md)
- **End-to-end transaction example?** [`ION_First_Transaction.md`](ION_First_Transaction.md)
