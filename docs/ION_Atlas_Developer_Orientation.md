# ION Atlas — Developer Orientation

**Version:** 1.0 — April 2026  
**Audience:** Developers building on ION who want to understand where the specs come from and where tooling is headed

---

## ONIX — the ION reference implementation

Before diving into Atlas, one practical note on how developers are expected to build on ION.

ION provides **ONIX**, a reference implementation that handles the Beckn transport layer. ONIX is strongly recommended for all developers building on ION — whether BAP or BPP. It handles HTTP signatures, ACK routing, async callback management, catalog publication, and subscriber registry integration. Developers implement their business logic on top of ONIX, not underneath it.

ONIX is available via ION DevLabs (`devlabs.ion.id` — coming soon). It is separate from this spec repo. This repo defines what the payloads look like and what the fields mean. ONIX is the toolkit that moves those payloads correctly across the network.

The relationship between the three components:

```
ION Network Spec (this repo)
    ↓  defines the payloads, fields, and rules
ONIX
    ↓  handles transport, signatures, routing
Your business logic
    ↓  catalog content (BPP) | consumer UI and order flow (BAP)
```

Atlas — described in the rest of this document — is the schema governance registry that underlies the spec. ONIX reads from Atlas to stay in sync with field definitions and validation rules as the network evolves.

---

## What Atlas is

Atlas is ION's schema governance registry. It is the system that owns the authoritative definition of every field, every type, every valid enum value, and every validation rule on the ION network.

The YAML specs you are working with — the Dominos food example, the Indomie grocery spec, the Samsung electronics spec — are generated from Atlas. They are not hand-written documents. Atlas holds the canonical field definitions, and the YAML files are one rendered output of those definitions. The Trade Dictionary is another rendered output of the same source.

This matters for you as a developer because:

- When a field changes, Atlas changes first. The YAML and Dictionary regenerate from it. There is one source of truth.
- When you implement a field and it behaves unexpectedly, the Atlas field definition is what ION Central validates against — not the YAML comment.
- When you want to propose a new field, you are proposing an Atlas addition — which follows the governed process described below.

---

## The four layers Atlas manages

Every field in ION belongs to one of four layers. The layer determines who can propose changes and how quickly they move through governance.

**Layer 1 — Beckn Core**  
Fields defined by Beckn Protocol v2.0 itself. `context.domain`, `context.transaction_id`, `Provider.id`, `Provider.availableAt[].geo`. These are read-only in Atlas — ION never redefines them. Atlas seeds these from the Beckn v2.0 YAML at network launch and hard-blocks any attempt to override them.

**Layer 2 — ION Core**  
Fields that apply across all ION sectors. `nib`, `npwp`, `halalCertNumber`, `bpomRegistrationNumber`, `provinsiCode`, `kabupatenCode`, `bifastAccount`. These change rarely and require full ION Council ratification. They encode Indonesian law and regulatory requirements — getting them wrong has compliance consequences.

**Layer 3 — Sector**  
Fields specific to a sector (Trade, Logistics, Mobility, etc.) but applicable across all resource types within it. `dietaryClassification`, `allergens`, `customisationGroups`, `serviceabilityPolygon`, `storeStatus`. These move through a lighter governance process — ION Council review with a shorter ratification cycle. Most of the fields in the YAML specs you are working with live here.

**Layer 4 — Flow**  
Fields specific to a particular commerce pattern within a sector. `creditTermsDays` for B2B wholesale, `subscriptionBillingCycle` for subscription commerce, `minimumOrderQuantity` for wholesale. These have the lightest governance — a working group review is sufficient for non-breaking additions.

---


## The two-service catalog architecture

The catalog layer in ION is split across two distinct services. Understanding the split is essential before you implement anything.

**Catalogue Service — hosted by Beckn Fabric**

The Catalogue Service is the authoritative store of all BPP catalogs on the ION network. Beckn Fabric hosts and operates it. BPPs interact with it via `/publish_catalog` to push their catalog and incremental updates.

The Catalogue Service is network infrastructure — neither BAP developers nor BPP developers need to build or host it. BPPs call the `/publish_catalog` endpoint. That is the full extent of BPP interaction with this service.

**Discover Service — hosted by ION or by the BAP**

The Discover Service is the subscription and delivery layer. It sits between the Catalogue Service and BAPs. BAPs subscribe to it declaring what they want — sector, category, location context. The Discover Service pulls matching catalogs from the Catalogue Service and delivers them to subscribed BAPs via `/on_discover`.

Three options exist for how a BAP interacts with the Discover Service:

**Option 1 — ION shared Discover Service**
ION operates a shared Discover Service that any BAP can subscribe to. No infrastructure to run. The BAP subscribes to ION's endpoint and starts receiving matching catalogs immediately. The simplest way to understand the flow end-to-end.

**Option 2 — BAP-hosted Discover Service**
The BAP runs their own Discover Service instance, connected to the Catalogue Service. Full control over filtering, ranking, caching, and how catalog data feeds into their own search infrastructure.

**Option 3 — Integrated (vertically integrated BAP/BPP)**
A BAP that is also a BPP — same organisation on both sides — may host their own DS and wire up directly. Still formally subscribes.

In all three options, the BAP formally subscribes and delivery follows the standard `/on_discover` API into their discovery pipeline. The right option depends on scale, control needs, and architecture — all three are valid ION configurations.

**What this means for each role:**

*BPP developer:* You implement `/publish_catalog` to push your catalog to the Catalogue Service. You do not implement `/on_discover` — that is sent by the Discover Service, not by you. You also implement all transaction callbacks from `/on_select` onwards, which are direct BAP-to-BPP calls.

*BAP developer:* You implement a `/subscribe` call to the Discover Service (ION-hosted or your own). You implement a `/on_discover` handler to receive and index incoming catalogs. You do not query individual BPPs for catalog. From `/select` onwards, you call BPPs directly.

**Open question — polygon matching location**

GeoJSON serviceability polygon matching determines which BPP catalogs reach which BAPs based on consumer GPS. Where this check happens — in the Catalogue Service, the Discover Service, or at the BAP — is pending ION Council decision and is tracked as an open question in the Atlas issue tracker.

## How a field gets into Atlas

The process is designed to be low-friction for additions and high-friction for changes to existing fields.

**Adding a new field:**

1. Open a GitHub Issue in this repo using the field proposal template
2. Describe the field: name, type, valid values, which layer it belongs to, which Indonesian law or use case drives it, and a concrete example
3. ION Council working group reviews in the next governance cycle (fortnightly)
4. If approved: the field is added to Atlas, the Dictionary regenerates, and a new YAML version is tagged
5. If changes are needed: the issue stays open with feedback comments

**Changing an existing field (non-breaking):**  
Adding a new enum value, relaxing a mandatory condition, adding a new language key — PR directly. Working group review only. No full Council vote.

**Breaking change (rename, type change, removal):**  
Full ION Council vote required. Breaking changes are versioned — the old field stays valid for one deprecation cycle (minimum 60 days) before removal. YAML files carry `deprecated_fields[]` for any field in the deprecation window.

---

## The ION Atlas tool

Atlas itself is a web application — the Schema Explorer. It is the developer-facing interface to the registry. From it you can:

- Search any field by name and see its full definition, layer, mandatory conditions, valid values, and regulatory source
- Browse the full field hierarchy by object (Resource, Offer, Contract, etc.)
- See which YAML specs use a given field
- View open proposals for new fields and comment on them
- Download the Trade Dictionary in JSON or Excel format

The Schema Explorer is built and running. It reads from the same Atlas registry that the YAML specs and Dictionary are generated from.

---

## AutoPilot — where tooling is heading

AutoPilot is the planned developer experience layer on top of Atlas. The concept:

A developer arrives at ION DevLabs and answers three questions:

1. What are you building? (BAP / BPP)
2. Which sector? (Trade / Logistics / Mobility / etc.)
3. Which category? (Food & QSR / Electronics / Fashion / etc.)

AutoPilot generates a personalised pack instantly:

- A custom API contract — only the APIs and fields relevant to your combination
- A pre-populated Postman collection with realistic Indonesian example data
- A starter code skeleton (Node.js or Python) with all callback handlers stubbed
- A sandbox test catalog pre-loaded with your category's products

Today, you are working with the raw YAMLs directly — which is the underlying source that AutoPilot will draw from. Your experience building with these files is actively informing what AutoPilot needs to surface and what it needs to simplify.

**AutoPilot v0** is this Claude project itself — you can ask it questions about any field, any pattern, any Indonesian regulatory requirement, and it draws from the same knowledge base that will eventually power the full AutoPilot tool.

---

## What this means for you as an early participant

You are building before Atlas has a live sandbox and before AutoPilot exists. That means two things.

First, the YAMLs in this repo are your primary implementation guide. They are the most complete and accurate representation of the ION spec that exists right now. They are also living documents — as open questions get resolved and ION Council ratifies decisions, the YAMLs will update.

Second, your implementation will find things the spec got wrong or left ambiguous. That is expected and valuable. When you hit an edge case — a field that seems missing, a validation rule that does not match your use case, a commerce pattern that needs a field the Dictionary does not have — raise a GitHub Issue. Your real implementation experience is the fastest path to a better spec.

The open questions marked in the field mapping and spec tracker are genuine open questions. Some of them will only get resolved when someone tries to implement against them.

---

## The relationship between this repo and ion.id

This repo is the working specification. `ion.id` is the production network. The relationship:

- Changes to specs in this repo go through governance before they affect the live network
- The live network runs the last tagged release version of this repo
- A sandbox network runs the current `main` branch — so your implementations against `main` are testing against what will become the next release

When you are ready to go live, your network participant registration is done through `registry.ion.id`. Sandbox registration (for development and testing) will be available at `sandbox.ion.id`. Both will be linked from this repo's README when they are available.

---

## Quick reference — Atlas field layers

```
ion://core/         — ION Core fields (cross-sector)
ion://trade/        — Trade sector fields
ion://logistics/    — Logistics sector fields  
ion://trade/flow/   — Trade flow-specific fields
ion://policy/       — Standard policy IRIs (machine-enforced)
ion://errors/       — Error code registry
```

All policy IRIs and error codes referenced in the YAML specs resolve to JSON-LD documents at these IRI roots. ION Central resolves them at transaction time — you declare the IRI in your payload, ION Central fetches and enforces the underlying policy terms.

---

*ION Atlas Developer Orientation v1.0 — April 2026*  
*For internal Atlas architecture documentation, see the ION Atlas Architecture document (ION Council internal)*
