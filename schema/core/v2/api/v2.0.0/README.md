# ION Network Profile — v2.0.0

`ion.yaml` is the ION network profile overlay on Beckn Protocol v2.0.1.

It does **not** replace `beckn.yaml`. Beckn's core transport specification lives at:
https://github.com/beckn/protocol-specifications-v2

`ion.yaml` declares:
- Network ID, registry URL, catalog service URL
- Localization defaults (IDR currency, Asia/Jakarta timezone, id language)
- Compliance requirements (NPWP mandatory, PPN 11%, data residency Indonesia)
- Security requirements (Ed25519 signing, BLAKE2b-512 digest)
- Mandatory action sets for BAP and BPP
- Settlement model and allowed payment rails
- Schema pack conformance matrix

All ION implementations must satisfy both `beckn.yaml` and `ion.yaml`.
