# trade/performance-states/v1

Canonical performance state codes for all Trade sector fulfilment flows.

This is not a schema pack — it has no `attributes.yaml` or `profile.json`. It is a vocabulary definition file that spine and branch files reference for state codes.

## File

`states.yaml` — defines all state machines with valid transitions.

## State machines

| Machine | Used in |
|---|---|
| `standard` | B2C-SF, B2B-PP, B2B-CR, MP-IH, AUC-F, XB — standard packaged goods delivery |
| `mto` | B2C-MTO — make-to-order (food QSR, custom bakery, tailoring) |
| `self_pickup` | When performanceMode=SELF_PICKUP on any spine |
| `return` | Returns branch |
| `replacement` | Returns branch — replacement sub-flow |
| `rto` | RTO branch |

## How BPPs use these

BPPs set `beckn:Performance.status.code` using these codes. The BPP picks the appropriate state machine based on the performanceMode and resourceStructure.

## How BAPs use these

BAPs map incoming state codes to consumer-facing labels:

| Code | Suggested display (Bahasa Indonesia) |
|---|---|
| PLANNED | Pesanan dikonfirmasi, sedang diproses |
| PACKED | Pesanan dikemas, menunggu kurir |
| DISPATCHED | Pesanan dalam perjalanan |
| OUT_FOR_DELIVERY | Kurir sedang menuju lokasi Anda |
| DELIVERED | Pesanan telah diterima |
| PREPARING | Sedang dipersiapkan |
| READY | Siap diambil |
| RETURN_INITIATED | Permintaan retur diterima |
| RETURN_APPROVED | Retur disetujui |
| RETURN_PICKED | Barang sudah dijemput kurir |
| RETURN_DELIVERED | Barang sudah sampai ke penjual |
| RTO_INITIATED | Pengiriman gagal, barang dikembalikan ke penjual |
| RTO_DELIVERED | Barang sudah kembali ke penjual |
