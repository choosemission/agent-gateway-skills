# Claims

Every falsifiable statement this skill makes, with where it came from and when
it was last checked. The gateway changes fast; this file is what makes
re-verification mechanical instead of a re-read.

**Provenance codes**

| Code | Meaning |
| --- | --- |
| **G** | *Affinidi Trust Fabric — Agent Gateway Reference Guide* v0.3.10, August 2026, with page |
| **O** | Observed on a running gateway, with date |
| **A** | Direct guidance from the Affinidi team, August 2026 |

**Verified against:** Reference Guide v0.3.10 · gateway observations from
`train-soap.trustgateway.affinidi.io` (July–24 Aug 2026, since deprovisioned)
and from an `agentgateway.affinidi.io` gateway (28 Aug 2026, A2A surface).
**Last full review:** 28 August 2026.

> Observations marked O and dated **before 28 Aug 2026** were made on a gateway
> that no longer exists, and have **not** been re-checked on
> `agentgateway.affinidi.io`. Treat every such row as needing re-verification on
> the next live gateway — that is the single largest block of staleness risk in
> this skill. Rows B12–B15 are the first observations from the current host.

---

## 1. Unresolved contradictions

The most valuable rows here. Each is a place where sources disagree and the
skill deliberately presents both. Resolving these with Affinidi removes real
cost from every user.

| # | Claim | Conflict | Skill says |
| --- | --- | --- | --- |
| C1 | Policy package for a surface-attached policy | **G p97** `package surface.policy` · **G p86** `package gateway.authz` · **O** `surface.policy` | Presents all three, tells the reader to take it from a working policy or the console template |
| C2 | OPA policy input shape | **G p86** `input.caller.jwt_bearer.*` · **G p97** `input.agent.*` · **O** `input.jwt.*`, `input.gateway.direction` | Presents all three, tells the reader to dump `input` on a test surface |
| C3 | Gateway's OAuth callback path for delegation | **G p80** `https://<host>/oauth/callback/<provider>` · **O** (Jul 2026) `https://<host>/v1/identity/oauth/callback/<provider>` | Says take the exact value from the credential provider's own screen |

A fourth, cosmetic: **G p32** still says "A Fabric may include Trust Gateways",
a leftover from the rename to Agent Gateway.

## 2. Structural claims — from the reference guide

Checkable by reading a current guide, not by probing.

| # | Claim | Source |
| --- | --- | --- |
| S1 | Surface protocol is **A2A or MCP only**; no protocol translation on the inbound path | G p31–32 |
| S2 | **No HTTP and no LLM targets.** LLM and agent-to-dependency traffic is Agent Stream's. HTTP unimplemented pending a customer use case | A |
| S3 | A surface owns exactly one Access Point, exactly one External Target, zero or more Transit Points | G p27 |
| S4 | Outbound = agent-initiated via a Transit Point. The response is the MA→AP response leg | G p30 |
| S5 | **Listener bindings are startup-only**; all other configuration hot-reloads without restart | G p28, p30 |
| S6 | Variants are selected by appending `$alias` to the access point URL | G p31, p97 |
| S7 | Target address schemes: `proxy://`, `a2a-proxy://{id}`, `fabric://` | G p32, p90–92 |
| S8 | Gateway-level policy runs first and **a deny is final** | G p35 |
| S9 | Policy scopes are Gateway, Agent Surfaces, Paywall | G p53, p61 |
| S10 | An MCP `tools/call` with no matching tool-policy entry and no `*` wildcard is **denied** | G p91 |
| S11 | Consent modes: pre-authorize, on-demand, elicit | G p80 |
| S12 | Delegation vault is keyed by agent identity + user identity hash + provider | G p80 |
| S13 | Source auth methods: JWT Bearer, API Key, API Key Provider, DID Auth, mTLS. Multiple allowed, evaluated in order | G p33 |
| S14 | Managed identity modes: payload extraction, mTLS, API key, static, JWT claim | G p64 |
| S15 | Identity slots: inbound, protected, external | G p34 |
| S16 | Payload extraction travels as the A2A extension `https://fabric.affinidi.io/extensions/agent-identity/v1`, or MCP `_meta.agentIdentity` | G p12 |
| S17 | Transit token modes: Embedded, Header, None | G p38 |
| S18 | Secrets are referenced as `$secret:<id>` placeholders | G p97 |
| S19 | DID documents are served at `/.well-known/did.jsonl` | G p15 |
| S20 | A2A agent card at `/.well-known/agent-card.json`, URLs rewritten to the gateway | G p93 |
| S21 | Rate limiting is token-bucket, rejecting 429 with `Retry-After` | G p16 |
| S22 | Roles: Administrator, Power User, User. **Power User cannot edit surfaces**, policies, API keys, certificates or system settings | G p98 |
| S23 | A misconfigured JWT strategy or unreachable JWKS **fails the request**; no fallback to allowing unverified traffic | G p73 |
| S24 | `X-Gateway-Trace-Id` is set on every request and appears in its log lines | G p18 |
| S25 | Payload capture has four stages: inbound request, outbound request, inbound response, outbound response | G p17 |
| S26 | MCP proxy tools are derived one per OpenAPI path/method pair | G p91 |

## 3. Behavioural claims — observed, need re-verification

**Every row here was seen on a gateway that has since been deprovisioned.**
`scripts/verify-claims.sh` probes the ones a script can reach.

| # | Claim | Observed | Probe |
| --- | --- | --- | --- |
| B1 | An unknown path on a proxy-handled prefix returns a JSON error citing `a2a-protocol.org` | Jul–Aug 2026 | yes |
| B2 | No live route → `404 … "No route configured for path: …"` | Jul–Aug 2026 | yes |
| B3 | A GET on a live MCP/A2A surface → `502 builder error for url 'proxy://<uuid>'` | Jul–Aug 2026 | yes |
| B4 | Protocol mismatch → `422 … protocol 'a2a' does not match access point protocol 'mcp'` | Jul–Aug 2026 | yes |
| B5 | A surface with no caller context forwards `x-caller-did: anonymous` and `x-caller-identity-source: gateway-computed` | Aug 2026 | needs a surface |
| B6 | MCP-proxy tool arguments nest under `request_body` unless POST-parameter flattening is on | Aug 2026 | needs a surface |
| B7 | MCP-proxy responses are double-wrapped: `result.content[].text` is a JSON string containing `{"status":…,"body":…}` | Aug 2026 | needs a surface |
| B8 | RFC 9728 discovery documents returned the dashboard's HTML while the `WWW-Authenticate` challenge and JWKS verification worked | Jul 2026 | yes |
| B9 | A page reload refreshes the surface route cache | Aug 2026 | manual |
| B10 | Palette entries appear greyed in a pattern not established — possibly one-per-surface | Aug 2026 | manual, **unexplained** |
| B11 | DID Auth caller context expects an opaque session token, and no handshake endpoint is exposed | 24 Aug 2026 | needs a surface |
| B12 | Identity is configured **per leg**: an Identity element on the MA→AP **response leg** resolves the managed agent's identity. The Managed Agent node offers only the *Identity Binding VP* switch, no identity definition | 28 Aug 2026 | needs a surface |
| B13 | A payload-extraction schema must mark fields `"x-identity": true`; without it the save is rejected `400 … no identity fields are declared`. Declared paths are relative to the **meta field**, and `identityFields` keys preserve the dotted path | 28 Aug 2026 | needs a surface |
| B14 | Inbound identity travels as `…/agent-identity-binding/v1`; the response leg as `…/agent-identity-credential/v1`. Each leg's element mints its own surface-scoped `did:webvh`; the issuer is the gateway instance DID for both | 28 Aug 2026 | needs a surface |
| B15 | The response-leg credential's subject is a **`workloadBinding`** — `agentIdentity`, `userIdentity.id` (the DID minted on the inbound leg), `delegated`, `traceId` — not `identityFields`. **Unresolved:** whether the Identity element mints this alone, or a Workload Binding element was also active | 28 Aug 2026 | needs a surface |

## 4. Claims about our own work

| # | Claim | Source |
| --- | --- | --- |
| L1 | The dual-leg pattern was built and verified end to end for the Lab's catalog server | `docs/catalog-mcp.md` in the affinidi-lab repo |

---

## Re-verification procedure

1. Run `scripts/verify-claims.sh` against a live gateway. It covers §3 rows
   marked *probe*.
2. Read the current reference guide's concepts and capabilities sections against
   §2. Structural claims drift on version boundaries, not gradually.
3. Re-test §3 rows marked *needs a surface* by standing up one MCP surface —
   pattern 1 in `references/patterns.md`.
4. Re-ask Affinidi about §1. If any resolve, remove the hedging from the skill:
   presenting three possibilities is a cost the reader pays on every lookup.
5. Update **Last full review** above, and add a `CHANGELOG.md` entry naming the
   gateway version checked.
