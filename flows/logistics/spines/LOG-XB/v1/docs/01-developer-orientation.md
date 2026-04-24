# LOG-XB — Developer Orientation

## What this spine is for

You are building a cross-border freight integration — either as an international carrier or freight forwarder (BPP) handling customs clearance, or as a BAP (exporter, importer, marketplace) shipping goods across borders.

LOG-XB extends LOG-FREIGHT with customs clearance as a gating concern. Bea Cukai (DJBC — Direktorat Jenderal Bea dan Cukai) events are first-class state transitions. A shipment can be terminated at customs, which is a valid and expected terminal path — not an error.

## Customs broker as a participant

LOG-XB adds a third participant: the CUSTOMS_BROKER (PPJK — Pengusaha Pengurusan Jasa Kepabeanan). The BPP may either have in-house customs brokerage capability or reference a partner PPJK. The `beaCukaiLicenceNumber` is a required catalog field for LOG-XB providers.

## Mandatory documents at /init

Unlike LOG-FREIGHT, LOG-XB requires documentation at `/init`:
- Commercial invoice (mandatory)
- Certificate of origin (mandatory for most categories)  
- Packing list (mandatory)
- HS codes per line item (mandatory)
- Import/export licences (conditional — pharma, electronics, food, CITES)

## Duty and tax flow

At `/on_select`, BPP returns `dutyEstimate` and `taxEstimate` in the breakup — indicative amounts based on HS codes and incoterms. Actual duty and tax amounts (`actualDuty`, `actualTax`) are confirmed in the `IMPORT_CUSTOMS_CLEARED` `on_status` push.

For DDP (Delivered Duty Paid) incoterms, duties are the shipper's responsibility and included in the freight quote. For DAP, buyer pays on delivery.

## Customs hold resolution

When `IMPORT_CUSTOMS_HELD` fires, the BAP has a `buyerResolutionDeadline` to provide documentation via `/update`. Customs hold reasons (documentation incomplete, restricted goods verification, inspection) each have a defined resolution path. Unresolved holds progress to `IMPORT_CUSTOMS_REJECTED`.

## The three rejection outcomes

When `IMPORT_CUSTOMS_REJECTED` fires, BAP must choose:
1. `RETURN_TO_ORIGIN` — triggers `reverse-xb` branch (dual customs on both legs)
2. `DESTROY_IN_PLACE` — requires written BAP authorisation; no RTO
3. `RE_EXPORT_TO_THIRD_COUNTRY` — BAP provides destination country and carrier

Storage fees at the destination port accrue from the rejection date regardless of choice.

## Incoterms and how they affect the spec

Incoterms determine who handles and pays for customs, insurance, and freight at each point. The incoterm selected at `/select` affects: who is CONSIGNOR and CONSIGNEE in the API participants, who the CUSTOMS_BROKER works for, and how the consideration breakup is structured.

## Beckn 2.0 endpoints used

```
/catalog/publish → /catalog/on_publish
/select → /on_select           (HS codes in request; duty estimates in response)
/init → /on_init               (commercial invoice, cert of origin, packing list)
/confirm → /on_confirm
/on_status (customs clearance events — many more states than domestic)
/track → /on_track
/update → /on_update           (customs hold resolution, duty dispute)
/cancel → /on_cancel           (window closes at EXPORT_CUSTOMS_SUBMITTED)
/rate → /on_rate
/reconcile → /on_reconcile
/raise → ... (duty dispute escalation)
/support → /on_support
```

## Relationship to LOG-FREIGHT

LOG-XB inherits from LOG-FREIGHT. The capacity booking mechanics (selectRequired always, bill of lading, departure events) are identical. The diff is: customs clearance states added, additional documents at init, additional participants (customs broker), and three possible terminal states instead of one.
