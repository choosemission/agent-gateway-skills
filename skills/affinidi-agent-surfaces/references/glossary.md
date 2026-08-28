# Glossary

One line each, for the terms a surface author meets. Fuller treatment of
anything configurable is in `configuration.md` and `identity-and-controls.md`.

## The surface

| Term | Definition |
| --- | --- |
| **Agent Surface** (*surface*) | The configuration and runtime unit representing one managed agent: one Access Point, one External Target, zero or more Transit Points, its identity slots and any variants. |
| **Access Point (AP)** | The inbound face — address, route path and protocol. Owns caller authentication, inbound rate limiting, and the caller context mode (required, optional, anonymous). |
| **External Target** | Where a passing request is forwarded. Outside the surface boundary because it is outside the gateway's control. |
| **Managed Agent** | The agent the gateway proxies for; the in-surface twin of the External Target and the part the gateway can configure. |
| **Transit Point (TP)** | An agent-initiated outbound route, with its own listener, target, protocol, credentials, policy and payment policy. |
| **Listener** | A bound address and port. One serves many APs or TPs. Startup-only: changing it needs a process restart. |
| **Surface Variant** | A named alternative configuration of the same surface, reached by appending `$alias` to the URL. |
| **Inbound** | Caller → Access Point → Target. |
| **Outbound** | Managed agent → Transit Point → its target. Not the response path, which is the *MA → AP response leg*. |

## Protocols and endpoints

| Term | Definition |
| --- | --- |
| **Surface protocol** | The protocol at both ends of the inbound path: A2A or MCP. The gateway does not translate protocols inbound. |
| **Transit protocol** | The protocol at one Transit Point. May differ from the surface protocol. |
| **A2A** | Agent-to-Agent. Direct agent-to-agent flows. |
| **MCP** | Model Context Protocol. Enables per-tool policy and MCP-specific metadata handling. |
| **MCP Proxy** | Presents a REST/OpenAPI backend as an MCP tool catalogue and translates the calls. Target address `proxy://…`. |
| **A2A Proxy** | Bridges A2A to a backend on another interface — today Bot Framework Direct Line for Microsoft Copilot Studio. Address `a2a-proxy://{id}`. |
| **Fabric endpoint** | A target resolved through a peer gateway over DIDComm rather than the open network. Address `fabric://<gateway>/<surface>`. |
| **Fabric** | The set of DIDComm appliances connected through Connection Points — gateways, trust registries. |
| **Connection Point** | The DIDComm endpoint another fabric appliance uses to pair with this one. Not an Access Point: it pairs gateways, it does not serve callers. |
| **Gateway-to-Gateway (G2G)** | A call routed through the fabric. Identity, policy and payment controls apply on **both** gateways. |

## Identity

Five separate concerns. Collapsing them is the classic error.

| Term | Definition |
| --- | --- |
| **Source authentication** | Verifies the inbound caller. Per Access Point. Methods: JWT Bearer, API Key, API Key Provider, DID Auth, mTLS. Several may run, in order. |
| **Credential extraction** | Where to *look* for the caller's credential — header name and scheme, or query parameter. Verification is separate. |
| **Authenticated identity** | The per-request result of source auth: verified principal plus auth metadata. Not a configuration object. |
| **Identity resolution** | Derives the **caller's** agent DID from the authenticated identity. |
| **Payload extraction** | Derives a deterministic DID by hashing chosen fields the agent already sends about itself — A2A extension point, or MCP `_meta.agentIdentity`. Same values, same DID. |
| **Identity slot** | One of three DID positions on a surface: **inbound** (the caller), **protected** (a DID in a signed claim), **external** (a DID the payload refers to). |
| **Managed identity** | Derives the **managed agent's** DID. Modes: payload extraction, mTLS, API key, static, JWT claim. Versioned, so keys rotate without changing the DID. |
| **Agent DID** | A W3C DID for an agent. `did:webvh` for agent identity, `did:peer` for gateway-to-gateway. Always say *which* agent. |
| **Identity injection** | Whether the gateway attaches proof of the resolved DID to forwarded calls, as a Verifiable Presentation. |
| **Verifiable Presentation (VP)** | The signed credential bundle attached when injection is on. W3C VC 2.0, may carry caller-binding claims preventing replay. |
| **Workload Binding** | A signed VP **per request execution**, binding managed-agent identity, selected caller claims, the workload intent and a trace ID. Identity VCs attest *who an agent is*; these attest *what happened*. |
| **Trust Check** | A TRQP query to a trust registry, of two kinds: **recognition** (does authority Y recognise X?) and **authorization** (may X do Z on R, per Y?). Results reach policy as `trust_check_results`. |
| **Trust Recorder** | Writes registration records to trust registries on the response leg. Fire-and-forget: a failure is logged and does not affect the response. |
| **Issuer** | A gateway-generated DID with signing keys, registrable in a trust registry as a trust anchor. On a surface it is the default authority for caller-leg trust checks. |
| **Authority** | A record registering an **external** DID as a named trust anchor. No keys, no registry registration — it exists so a partner's DID is selectable by name. |
| **JWT verification strategy** | A reusable pairing of an expected issuer with a key source: remote JWKS URL (cached) or static stored keys. |

## Policy

| Term | Definition |
| --- | --- |
| **Gateway-level policy** | Runs first, for every request on the instance. A deny is **final** and unappealable by any surface policy. |
| **Surface-level policy** | Runs only if the gateway gate passed. Scoped to a surface or transit flow. |
| **Paywall scope** | The third policy scope, governing payment conditions. |
| **Policy definition** | The stored Rego plus name, description and version. Reusable across surfaces. |
| **Policy reference** | The pointer from a surface field to a definition. Updating the definition propagates without editing each surface. |
| **MCP tool policy** | A per-tool entry on an MCP target. `*` is a wildcard, and a `tools/call` with no matching entry and no wildcard is **denied**. |

## Credentials, delegation and payment

| Term | Definition |
| --- | --- |
| **Credential** | How the gateway obtains authorisation to call an external service on the **outbound** path. Never used to check who is calling in. |
| **Credential provider types** | OAuth 2.0 Authorization Code (three-legged, user-consented), OAuth 2.0 Client Credentials (machine-to-machine), API Key. |
| **Delegation vault** | Encrypted store of delegated credentials, keyed by **agent identity + user identity hash + provider**. |
| **Consent modes** | **Pre-authorize** — block at initialisation until all credentials are present. **On-demand** — return `consent_required` and let the client handle it out-of-band and retry. **Elicit** — MCP-native, an elicitation over the open stream with the call resumed in place. |
| **Secret types** | Generic secrets (referenced as `$secret:…`), API keys (inbound auth), client certificates (server leaf / client leaf / CA), delegation tokens (gateway-to-gateway). |
| **Transit token** | A short-lived signed token injected inbound and echoed back by the managed agent on outbound calls. Carries the caller's identity, the originating surface, and which Transit Points this session may use. Modes: Embedded, Header, None. |
| **x402** | HTTP 402-based payments protocol for blockchain-settled access. |
| **MPP** | Machine Payments Protocol, HTTP challenge/response payment auth. Experimental, vendor preview. |

Source auth answers *who is this caller?*; the transit token answers *what
outbound actions is this caller's session permitted to trigger?* Orthogonal, and
deliberately kept apart.

## Which appliance owns this?

Agent Gateway is one appliance in the **Affinidi Trust Fabric** suite. Sending a
question to the wrong one is the most expensive mistake here, because the
configuration you are looking for genuinely is not there.

| Concern | Appliance |
| --- | --- |
| Agent-to-agent traffic: A2A and MCP, identity, policy, delegation, payments, cross-boundary routing | **Agent Gateway** |
| Agent-to-dependency traffic: LLM safety, content moderation, cost management | **Agent Stream** |
| Agentic payments and MCP monetisation as a product surface | **Agent Pay** |
| Recognition and authorisation records, TRQP | **Affinidi Radix — Trust Registry**, a fabric participant the Gateway queries |

**HTTP traffic is handled by neither today.** Affinidi's position (Aug 2026) is
that plain HTTP would belong with Agent Stream, as agent-to-dependency, and is
not implemented pending a customer use case.

Agent Surfaces are not exclusive to the Gateway — Agent Stream uses the same
canvas construct. Say **Agent Gateway surface** where the appliance matters.

---

Sourced from the *Affinidi Trust Fabric — Agent Gateway Reference Guide* v0.3.10
(August 2026), except the appliance-boundary note on HTTP and LLM traffic, which
is direct guidance from the Affinidi team, August 2026. Where this skill records
something **observed** on a running gateway that the guide does not cover or
contradicts, it says so at that point. Prefer the running gateway for behaviour.
