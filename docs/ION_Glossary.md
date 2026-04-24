# ION Glossary

Every acronym, role, and ION-specific term in one place. Use Cmd/Ctrl-F.

If an acronym is missing, it's a bug — file an issue.

---

## Network roles

| Term | Stands for | What it is |
|---|---|---|
| **BAP** | Beckn Application Platform | The buyer-side app. Marketplaces, brand apps, consumer apps, procurement platforms. |
| **BPP** | Beckn Provider Platform | The seller-side app. Merchants, LSPs, warehouses, wholesalers. |
| **CDS** | Catalog Discovery Service | Beckn v2's catalog service. BPPs publish catalogs; BAPs query or subscribe. |
| **BG** | Beckn Gateway | Beckn v1 term. Replaced by CDS in v2. |
| **LSP** | Logistics Service Provider | JNE, J&T, SiCepat, GoSend — BPPs in the logistics sector. |
| **3PL / 4PL** | Third/Fourth-Party Logistics | Logistics aggregators. ION treats them as BPPs representing underlying carriers. |
| **MP** | Marketplace | A marketplace-type BAP or the MP-IH/MP-IL spine family. |
| **Principal** | The legal entity in a transaction (seller, buyer) | Not an API role — a commercial one. |

## ION organization

| Term | What it is |
|---|---|
| **ION** | The network itself, or the organization that governs it. |
| **ION Council** | Governance body. Approves spec changes, policy ratifications, FWA registrations. |
| **ION Central** | The network's technical infrastructure — registry, schema gate, policy engine. |
| **ION Registry** | Participant directory. Technically hosted on DeDi, but participants only see "ION Registry." |
| **ONIX** | Beckn's reference implementation adapter. BPPs and BAPs plug into ONIX to get signing, validation, and routing for free. |
| **DeDi** | Decentralized Directory protocol. Underlying tech for ION Registry. Participants don't interact with it directly. |

## Protocol concepts

| Term | What it is |
|---|---|
| **Beckn** | The upstream open protocol ION is built on. Currently v2.0.0-rc1. |
| **Beckn core** | The universal envelope — transport, signing, object model. At `schema.beckn.io/core/`. |
| **ION profile** | ION's configuration of Beckn — `ion.yaml`. Declares what's mandatory, what's optional, what ION extends. |
| **L1/L2/L3/L4/L5** | ION's five-layer model. See [`ION_Layer_Model.md`](ION_Layer_Model.md). |
| **Attributes slot** | A field on a Beckn object (e.g., `Offer.offerAttributes`) where ION extension data lives. |
| **Extension pack** | A folder under `schema/extensions/{layer}/{pack}/v1/` defining a coherent set of ION extension fields. |
| **Spine** | A distinct API sequence defining one commerce pattern. Trade has 13 spines; Logistics has 6. |
| **Branch** | A conditional sub-flow that activates on a specific condition during a spine transaction (e.g., cancellation, weight dispute). |
| **Policy IRI** | A URL identifying a commercial policy: `ion://policy/{category}.{subcategory}.{variant}`. |
| **Framework Agreement (FWA)** | A pre-negotiated enterprise contract between BAP and BPP. Registered as a policy; enables bulk/repeat transactions under agreed terms. |

## Transaction endpoints (Beckn v2.0.0)

| Endpoint | Direction | Purpose |
|---|---|---|
| `/discover` | BAP → CDS | Active query for providers/offers |
| `/on_discover` | CDS → BAP | Results of a discover query |
| `/catalog/publish` | BPP → CDS | BPP publishes/updates its catalog |
| `/catalog/subscription` | BAP → CDS | BAP subscribes to catalog updates |
| `/select` | BAP → BPP | Request a binding quote for a specific offer |
| `/on_select` | BPP → BAP | Quote + capacity confirmation |
| `/init` | BAP → BPP | Lock in the terms, get payment link |
| `/on_init` | BPP → BAP | Terms confirmed, payment details |
| `/confirm` | BAP → BPP | Payment done, execute the order |
| `/on_confirm` | BPP → BAP | Order accepted, identifiers assigned |
| `/status` | BAP → BPP | Poll current state |
| `/on_status` | BPP → BAP | State push (also unsolicited during fulfilment) |
| `/track` | BAP → BPP | Request tracking handle |
| `/on_track` | BPP → BAP | Tracking URL or WebSocket |
| `/update` | BAP ↔ BPP | Modify contract (address change, dispute, etc.) |
| `/on_update` | other side | Response to update |
| `/cancel` | BAP ↔ BPP | Cancel contract |
| `/on_cancel` | other side | Cancellation outcome |
| `/rate` | BAP → BPP | Post-delivery rating |
| `/on_rate` | BPP → BAP | Rating acknowledgement |
| `/support` | BAP → BPP | Customer support query |
| `/on_support` | BPP → BAP | Support response |

## ION protocol extensions (L3)

| Endpoint | Direction | Purpose |
|---|---|---|
| `/raise` | party → ION | Escalate dispute after bilateral resolution failed |
| `/on_raise` | ION → party | Ticket accepted |
| `/raise_status` | party → ION | Poll raise status |
| `/on_raise_status` | ION → party | Current state |
| `/raise_details` | party → ION | Request full case detail |
| `/on_raise_details` | ION → party | Full case record |
| `/reconcile` | party → counter | Settlement reconciliation — base, adjustments, rebates, tax |
| `/on_reconcile` | counter → party | Agreement or dispute |

## Indonesian regulatory terms

| Term | Stands for | What it is |
|---|---|---|
| **NPWP** | Nomor Pokok Wajib Pajak | 16-digit tax ID. Required for every business. |
| **NIB** | Nomor Induk Berusaha | 13-digit business registration. Required under UU 11/2020 (Cipta Kerja). |
| **PKP** | Pengusaha Kena Pajak | VAT-registered business status. |
| **PPN** | Pajak Pertambahan Nilai | VAT. Standard rate is 0.11 (11%) per PMK 131/2024 — check DJP for current. |
| **PPh** | Pajak Penghasilan | Income tax. Withholding rates vary by type (PPh 23 for services, PPh 22 for imports). |
| **PPNBM** | Pajak Penjualan Barang Mewah | Luxury sales tax. Applied in addition to PPN on luxury categories. Rates 10-75%. |
| **SIUP** | Surat Izin Usaha Perdagangan | Trade business licence. Required for freight and warehouse operations. |
| **DJP** | Direktorat Jenderal Pajak | Tax authority (finance ministry). |
| **Bea Cukai** | Directorate General of Customs and Excise | Customs authority. Matters for cross-border. |
| **PMK** | Peraturan Menteri Keuangan | Regulation of the Minister of Finance. |
| **Permen** | Peraturan Menteri | Ministerial regulation (general). |
| **Kominfo** | Kementerian Komunikasi dan Informatika | Ministry of Communications. Governs data residency, personal data protection. |
| **PDP** | Pelindungan Data Pribadi | Personal data protection. UU 27/2022. |
| **Kemendag** | Kementerian Perdagangan | Ministry of Trade. |
| **Kominfo** | Same as above. |

## Indonesian geography

| Term | What it is |
|---|---|
| **Provinsi** | Province. 34 provinces. BPS codes `11`–`94`. |
| **Kabupaten / Kota** | Regency / City. 4-digit BPS code. |
| **Kecamatan** | District / sub-city. |
| **Kelurahan / Desa** | Village / urban zone. |
| **RT** | Rukun Tetangga — neighborhood group. Critical for last-mile delivery. |
| **RW** | Rukun Warga — association of RTs. |
| **Patokan** | Informal landmark used to find addresses (e.g., "next to the blue mosque"). |
| **BPS** | Badan Pusat Statistik — statistics agency, owns the geographic codes. |

## Identity documents

| Term | What it is |
|---|---|
| **KTP** | Kartu Tanda Penduduk — national ID card. Used for eKYC. |
| **NIK** | Nomor Induk Kependudukan — 16-digit number on the KTP. |
| **Passport** | For non-Indonesian participants (cross-border or foreign entities). |
| **SIM** | Surat Izin Mengemudi — driver's licence. Categories A, B1, B2, C, D. |
| **NPWP** | (see regulatory) Individual taxpayers have these too. |

## Logistics-specific

| Term | What it is |
|---|---|
| **AWB** | Airway Bill — tracking number for parcel shipments (despite the name, used for ground too). |
| **B/L** | Bill of Lading — tracking document for freight. |
| **NDR** | Non-Delivery Report — why a delivery attempt failed. |
| **RTO** | Return to Origin — failed delivery, sent back. |
| **RTS** | Return to Seller — handoff of an RTO to the seller or their warehouse. |
| **COD** | Cash on Delivery. |
| **DDP** | Delivered Duty Paid (incoterm). Seller pays all costs including duties. |
| **CIF / FOB / FCA** | Incoterms (international shipping cost allocation). |
| **FTL / LTL / FCL / LCL** | Freight modes: Full Truckload / Less-Than-Truckload / Full Container Load / Less-Than-Container Load. |
| **HS Code** | Harmonized System — international product classification for customs. |
| **PPJK** | Pengusaha Pengurusan Jasa Kepabeanan — customs broker. Licence required for cross-border. |
| **ALFI** | Asosiasi Logistik dan Forwarder Indonesia — Indonesian logistics association. |
| **ASPERINDO** | Asosiasi Perusahaan Jasa Ekspres, Pos, dan Logistik Indonesia — Indonesian express/postal/logistics association. |
| **Ro-Ro** | Roll-on/Roll-off — ferry transport where vehicles (cars, trucks) board with their cargo. |
| **Hyperlocal** | Same-city, sub-day delivery. Usually single-rider. |
| **Cold chain** | Temperature-controlled transport for perishables. |
| **Milk run** | Repeating daily delivery between fixed points (typical B2B). |
| **Hub** | Parcel sorting facility. |
| **P2P / P2H2P / P2H2H2P** | Parcel routing topologies: Point-to-Point / Point-to-Hub-to-Point / Point-to-Hub-to-Hub-to-Point. |
| **Slot** | A scheduled delivery window. |
| **SLA** | Service Level Agreement. |

## Trade-specific

| Term | What it is |
|---|---|
| **SKU** | Stock Keeping Unit — a specific variant of a product. |
| **B2C** | Business-to-Consumer. |
| **B2B** | Business-to-Business. |
| **MTO** | Make-To-Order (produced on demand). |
| **DIG** | Digital goods (pulsa, PLN tokens, vouchers). |
| **LIVE** | Live / social commerce (livestream shopping, OTT-embedded). |
| **SF** | Storefront (traditional e-commerce). |
| **SUB** | Subscription commerce. |
| **PP** | Purchase Order. |
| **CR** | Contract/Procurement. |
| **AUC-F / AUC-R** | Forward / Reverse Auction. |
| **B2G** | Business-to-Government. |
| **XB** | Cross-Border. |
| **IH / IL** | Inventory-Held / Inventory-Less (for marketplaces — whether the marketplace owns inventory or passes orders to sellers). |
| **Pulsa** | Mobile top-up credit. |
| **E-commerce** | General term for online commerce. Kemendag Permen 31/2023 governs. |

## Payment & settlement

| Term | What it is |
|---|---|
| **QRIS** | Quick Response Code Indonesian Standard. Unified QR payment. |
| **BI-FAST** | Bank Indonesia fast real-time payment system. |
| **E-Wallet** | Digital wallet (GoPay, OVO, DANA, ShopeePay, LinkAja, etc.). |
| **Virtual Account (VA)** | Unique bank account number for receiving payment. |
| **BNPL** | Buy Now Pay Later. |
| **Faktur Pajak** | Tax invoice. Required for B2B VAT transactions. |
| **Reconcile** | Post-fulfilment financial settlement. See `/reconcile` endpoint. |
| **Remittance** | Payment transfer (often COD cash from LSP to seller). |

## Technical / crypto

| Term | What it is |
|---|---|
| **Ed25519** | Digital signature algorithm. ION uses it for all message signing. |
| **BLAKE2b-512** | Hash algorithm for message digest. Wire token is `BLAKE-512` (Beckn convention). |
| **CounterSignature** | Receiver's signed acknowledgement on every Ack. |
| **keyId** | Pipe-separated triple: `{subscriberId}|{uniqueKeyId}|{algorithm}`. |
| **subscriberId** | Participant's unique ID on the ION Registry. |
| **JSON-LD** | Linked Data format. ION extension attributes use it via `@context` + `@type`. |
| **IRI** | Internationalized Resource Identifier. Like a URL, but can identify concepts, not just documents. |
| **schema.ion.id** | ION's vocabulary publication endpoint. |
| **schema.beckn.io** | Beckn's vocabulary endpoint. |

## States

| State family | Values |
|---|---|
| **Contract.status** | `DRAFT`, `ACTIVE`, `CANCELLED`, `COMPLETE` (4 values) |
| **Commitment.status** | `DRAFT`, `ACTIVE`, `CLOSED` (3 values — distinct from Contract) |
| **Settlement.status** | `DRAFT`, `COMMITTED`, `COMPLETE` (3 values) |
| **Tracking.status** | `ACTIVE`, `INACTIVE` |
| **Performance.status** | Open-ended — ION defines per spine (e.g., `PICKED_UP`, `OUT_FOR_DELIVERY`, `DELIVERED`) |

## Errors

| Prefix | What it is |
|---|---|
| **ION-Nxxx** | Cross-sector ION error code (e.g., `ION-1001` = AUTH_FAILED) |
| **ION-LOG-Nxxx** | Logistics-specific error code |
| **NackBadRequest** | Beckn-native 400-equivalent response |
| **NackUnauthorized** | Beckn-native 401-equivalent response |
| **ServerError** | Beckn-native 500-equivalent response |

---

*Last updated v0.5.2-draft.*
