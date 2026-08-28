---
name: affinidi-agent-surfaces
description: >-
  Understand, configure and debug an Agent Surface on an Affinidi Trust Fabric
  (ATF) Agent Gateway. Use whenever a task involves an ATF gateway: URLs on an
  `agentgateway.affinidi.io` or other gateway host; MCP or A2A access points;
  the words agent surface, access point, transit point, managed agent, external
  target, surface variant, caller context, credential delegation, MCP proxy,
  workload binding or trust check in an Affinidi context; errors such as "No
  route configured" or "Invalid JSON-RPC request". Covers the surface object
  model, the two agent protocols the gateway speaks, source authentication,
  agent identity and DIDs, OPA policy, credential delegation, and putting your
  own MCP server or A2A agent behind a surface — what credential the gateway
  injects and how to close the ungoverned path to the resource. Reach for it
  even when the ask is only "hit this endpoint".
---

# Agent Surfaces on the Affinidi Agent Gateway

> **Experimental.** Built from Affinidi's documentation and hands-on experience
> with the Agent Gateway. Under-tested: treat specific values as leads to confirm
> against the running gateway, and where this skill gives several candidates,
> that is because the sources disagree. Say so when a claim you are acting on is
> one of those.

The **Agent Gateway** is an intercepting proxy purpose-built for AI agents. It
sits between a caller and the agent or MCP server that caller is trying to
reach, and turns that call into a governed one.

It is **protocol-enforcing**, not a general-purpose proxy. It speaks exactly two
agent protocols — **A2A** and **MCP** — and parses them, so it can decide per
tool and per message rather than only per URL.

> **Gateway is agent-to-agent.** A surface's access point and its target always
> speak the same agent protocol; the gateway performs **no protocol translation
> on the inbound path**. There is no HTTP target and no LLM target. An LLM call,
> or an agent calling a plain web dependency, belongs to a different ATF
> appliance — **Agent Stream**, which is agent-to-*dependency* where Gateway is
> agent-to-*agent*. A REST backend can be reached, but only by giving it an MCP
> face first: see MCP Proxy below.

## Anatomy of a surface

An **Agent Surface** is the configuration and runtime unit representing **one
managed agent**. It owns **exactly one Access Point**, **exactly one External
Target**, and **zero or more Transit Points**.

```
        ┌───────────────────── the surface ─────────────────────┐
caller →│ Access Point ─── ● ─── ● ──→ Managed Agent ───────────│──→ External
        │      ↑         elements on the leg      │             │     Target
        │  source auth,                           │             │
        │  caller context,                        └─→ Transit ──│──→ some other
        │  rate limit                                  Point    │     endpoint
        └───────────────────────────────────────────────────────┘
```

| Part | What it is |
| --- | --- |
| **Access Point (AP)** | The inbound face: address, route path and protocol callers reach. Owns caller authentication and inbound rate limiting. |
| **External Target** | The real resource requests are forwarded to. Drawn *outside* the surface because it is outside the gateway's control. |
| **Managed Agent** | The agent the gateway proxies for — the in-surface twin of the External Target, and the part the gateway can configure. |
| **Transit Point (TP)** | An **agent-initiated outbound route**: the managed agent calling out through the gateway. Own listener, target, protocol, credentials, policy. |
| **Listener** | The bound address and port beneath an AP or TP. **Startup-only** — changing it needs a restart; everything else hot-reloads. |
| **Surface Variant** | A named alternative configuration, selected by appending `$alias` to the URL. How you test a change against live traffic without duplicating the surface. |

**Inbound and outbound are directions of traffic, not request and response.**
Inbound is caller → AP → Target. Outbound is managed agent → TP → TP target. The
response is the *Managed Agent → Access Point response leg* — a leg, not the
outbound direction. Getting this wrong makes Transit Points invisible.

Transit Points exist because one inbound request usually needs several outbound
calls to fulfil it. One surface with a primary path and a TP per dependency
keeps the whole flow in one governed object; the **transit token** correlates
those outbound calls back to the inbound session that authorised them.

### What a surface does to a request

1. **Accept** at the Access Point, for the declared protocol.
2. **Source authentication** — JWT bearer, API key, API key provider, DID Auth
   or mTLS. Several may be configured at once, evaluated in order.
3. **Identity resolution** — derive the caller's agent DID.
4. **Gateway-level policy** — runs first, for every request on the instance. A
   deny here is **final**.
5. **Surface-level policy**, plus rate limits, retries, circuit breakers.
6. **Validate** — required extensions and fields; identity-schema validation.
7. **Trust checks and payment**, where configured.
8. **Inject** — metadata, the identity Verifiable Presentation, delegated
   credentials from the vault.
9. **Forward** to the target.
10. **Capture** — payloads at four stages, metrics, trace ID.

Surfaces resolve at write time into immutable in-memory snapshots, so a saved
change is live on the next call without dropping in-flight requests.

### Protocols and targets

One **surface protocol** — A2A or MCP — spoken at both ends of the inbound path.
A Transit Point may use a different **transit protocol** from its surface.

| Target kind | Address | Use when |
| --- | --- | --- |
| **HTTP(S) upstream** | `https://host/path` | The target already speaks the surface protocol. Put the **full path** on it. |
| **MCP Proxy** | `proxy://…` | The backend is a REST API. Reads its OpenAPI spec, presents each path/method as an MCP tool, translates the calls. |
| **A2A Proxy** | `a2a-proxy://{id}` | The backend is a Microsoft Copilot Studio agent over Bot Framework Direct Line. |
| **Fabric** | `fabric://<gw>/<surface>` | The target is a surface on a peer gateway, wrapped in DIDComm and routed via a mediator. The caller's identity travels with it, so the second gateway decides for itself. |

"HTTP(S) upstream" is the **transport** by which the gateway reaches a target
that speaks A2A or MCP. It is not permission to point a surface at an arbitrary
web API — that is what MCP Proxy is for, and the proxy is what makes the traffic
MCP.

## Build order: define, then reference

The rule that governs the dashboard, and not knowing it is why configuring a
surface feels like it keeps sending you backwards.

**Gateway level** holds reusable objects: secrets, credential providers, JWT
verification strategies, policy definitions, proxies. **Surface level** only
*references* them. So a setting will be greyed out or offer an empty dropdown
because the object it selects from does not exist yet.

| To configure this on a surface | First create this at gateway level |
| --- | --- |
| A key presented to the external target | The secret (**Management → Secrets**) |
| Bearer-token caller authentication | The JWT verification strategy |
| Per-user credential delegation | The secrets, *then* the credential provider |
| A policy on any leg | The policy definition |
| An MCP or A2A proxy target | The proxy (**Agent → Proxies**) |

Create the prerequisites first and the surface configures in one sitting.

## A surface is a door, not a wall

The idea most worth internalising, because getting it wrong produces no error at
all.

You host a resource, put it behind a surface, and get a new URL carrying policy,
identity, credential injection and an audit trail. What did not happen: **the
original URL did not go away.**

```
                ┌─ access point ─ policy · identity · audit · [key injected] ─┐
  any caller ──┤                                                              ├─→ resource
                └─ target URL ───────────── direct, ungoverned ──────────────┘
                                              ▲
                                     this path must return 401
```

The gateway is a second door into the same room, and the first door is still
open. Both URLs sit side by side in the surface editor, so handing out the wrong
one is a copy away.

**The governance is real to the extent the ungoverned path is closed.** Close it
by requiring a credential on the resource and giving that credential to the
gateway to inject. The credential is not really protecting the data — the gateway
presents it for anyone the policy admits. It is making the governed door the only
door. What it buys is a **chokepoint**.

```bash
curl -s -o /dev/null -w '%{http_code}\n' "$TARGET_URL"   # want 401/403, never 200
```

Re-run after every redeploy, tunnel restart and secret rotation. This is the
property that regresses silently. A deliberate *authenticated* second door is a
legitimate design, not a bypass — the bypass is specifically the
**unauthenticated** path. `references/securing-the-resource.md` covers fitting
the lock, rotation and dual-leg targets.

The same logic runs outbound: an agent can call destinations that do not transit
the gateway at all, and nothing can be enforced on those. Routing dependencies
through Transit Points is what makes outbound governance real.

## The two OAuth legs

Two separate OAuth relationships, easy to conflate. Keeping them apart resolves
most identity confusion on a gateway.

| | **Caller context** (inbound) | **Credential delegation** (outbound) |
| --- | --- | --- |
| Answers | Who is calling *in*? | What do we present *upstream*? |
| Runs the OAuth dance | **Your application** | **The gateway** |
| Gateway's role | Verifies the JWT against the issuer's JWKS | Is the OAuth client; stores tokens in its vault |
| Redirect URI at that IdP | **Your app's** callback | **The gateway's** callback |
| Configured as | A JWT verification strategy → the **Caller Auth** element | Secrets → credential provider → **Credential Delegation** on the MA→External leg |

**On the inbound leg the gateway never participates in a redirect.** Your app
signs the user in and sends the JWT as a bearer token; the gateway checks the
signature. Registering a gateway URL at the caller's IdP produces
`redirect_uri_mismatch`, and no gateway configuration will fix it.

Two things to know before starting:

- **Caller identity extraction is what makes delegation per-user.** Vault entries
  are keyed by agent identity + user identity + provider. If every user appears
  to share one credential, that extraction is unset or on a non-unique claim.
- **Consent has three modes.** *On-demand* returns `consent_required` with an
  authorization URL and the client retries the same call. *Pre-authorize* blocks
  at initialisation until every credential is present. *Elicit* is the MCP-native
  version — an elicitation over the open stream, the original call resumed in
  place. Pick the one the client can actually handle; a client treating
  `consent_required` as fatal looks permanently broken.

## First contact with a surface

Identify the route before sending a payload. It costs one request.

```bash
curl -s "$URL"
```

- **No live route** → `404 … "No route configured for path: …"`
- **Live surface** → often `502 builder error for url 'proxy://<uuid>'`. Benign:
  you did a GET instead of the protocol handshake.
- **A2A surface** → the agent card at `<access-point>/.well-known/agent-card.json`.

Route prefixes are chosen per gateway — the listener is
`scheme://host/route/custom/path`. Discover rather than assume; the probe loop is
in `references/patterns.md`.

MCP responses arrive as Server-Sent Events, so send the SSE `Accept` header and
strip the `data: ` prefix:

```bash
H=(-H "Content-Type: application/json" -H "Accept: application/json, text/event-stream")
curl -s -X POST "$URL" "${H[@]}" -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"probe","version":"1"}}}' | sed 's/^data: //'
```

The method name selects the protocol: `initialize` and `tools/*` are MCP,
`message/send` is A2A. Sending one to a surface declaring the other returns a 422
naming both. Append `$alias` to target a variant.

## The gotchas that cost the most time

**1. Treating the gateway as a general-purpose proxy.** Pointing a surface at an
LLM API or a plain REST endpoint. The symptom is the backend's own complaint
about `jsonrpc` being an unexpected field, wrapped in a gateway error. REST goes
behind an MCP Proxy; LLM traffic belongs to Agent Stream.

**2. Policy package name.** A Rego policy must declare the package matching where
it is attached, or `allow` lands in a namespace the evaluator never reads — and
an undefined `allow` denies, identically for every caller. Check the package
before auditing the rules. `references/configuration.md` §3 records what has been
observed and where the vendor documentation disagrees with itself.

**3. Base URL on the target.** `https://host` rather than `https://host/mcp`
drops the path and gives you a framework 404 from your own backend
(`Cannot POST /`). Put the full path on the endpoint.

**4. No caller context, and a policy that assumes one.** A surface with no Caller
Auth element forwards `x-caller-did: anonymous` — identity was never switched on,
not a user named "anonymous". A policy gating on caller claims against such a
surface denies everything and looks like a Rego bug.

**5. Tunnel churn.** A restarted tunnel changes the hostname, invalidating the
target URL, the IdP redirect registration and your app's base URL at once — and
the errors point at whichever you notice first. Reserve a static tunnel domain.

**6. Hunting for the agent's own identity on the Managed Agent node.** Identity
is configured **per leg**: an Identity element on the inbound leg resolves the
caller, and a second one on the **managed agent → access point response leg**
resolves the agent. The Managed Agent itself offers only the *Identity Binding
VP* switch, so looking there and finding nothing reads as a missing feature. Note
also that "outbound" on this gateway means Transit Points, never the response
leg. `references/identity-and-controls.md` §1.

## Working style on an unfamiliar gateway

1. `GET` the route before sending anything.
2. Unsure which protocol? Try MCP `initialize` and A2A `message/send`; the error
   names the door faster than reading configuration.
3. On a denial, check the policy package and scope before the credentials.
4. On an OAuth error, name the **leg** first — inbound or outbound. Naming it
   usually names the fix.
5. Test the backend directly before testing through the gateway. That turns a
   five-layer debug into two one-layer debugs.
6. Turn on **payload capture** rather than inferring what the gateway sent.
7. Quote `X-Gateway-Trace-Id` with a timestamp when asking an operator for help.
8. After standing up or redeploying a target, curl its **own** URL with no
   credential. The only check here that fails silently.

**The gateway is evolving quickly.** Where written guidance and an observed
response disagree, the running gateway is the authority on its own behaviour.

## Where to go next

- `references/dashboard.md` — how the control plane is organised, the canvas and
  its elements, templates and partials. Read before configuring a surface.
- `references/configuration.md` — the governed path: protocols and targets,
  source authentication and caller context, policy, the target credential,
  credential delegation.
- `references/identity-and-controls.md` — what you add to a working surface:
  agent identity and DIDs, transit points and outbound governance, variants,
  traffic management, validation and capture.
- `references/troubleshooting.md` — the response-to-cause table and the identity
  failures in detail.
- `references/securing-the-resource.md` — closing the ungoverned path, rotation,
  dual-leg targets.
- `references/patterns.md` — worked examples: your own MCP server behind a
  surface, a REST backend via MCP Proxy, user-scoped delegation.
- `references/glossary.md` — one-line definitions, and which ATF appliance owns
  which concern.
