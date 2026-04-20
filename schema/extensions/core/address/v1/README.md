# ion-core/address/v1

Indonesian address subdivisions extending Beckn Address.

## Attaches to
`beckn:Address` — used in delivery addresses, provider locations, and fulfilment endpoints.

## Fields
| Field | Type | Mandatory | Description |
|---|---|---|---|
| provinsiCode | enum | always | BPS province code (BPS-11 to BPS-94). 34 provinces. |
| kabupatenCode | string | optional | BPS 4-digit kabupaten/kota code |
| kelurahan | string | conditional | Village/urban zone. Required for delivery addresses. |
| kecamatan | string | conditional | District/sub-city. Required for delivery addresses. |
| rt | string | optional | Rukun Tetangga — neighborhood group |
| rw | string | optional | Rukun Warga — association of RTs |

## Why RT/RW
RT and RW are critical for last-mile delivery in Indonesia. Riders use RT/RW to locate specific houses in dense residential kampung areas where street names alone are insufficient.

## Regulatory
Permendagri 72/2019 tentang Perubahan atas Permendagri 137/2017
