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
| **D** | docs.affinidi.com page, with URL and date checked |

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
| C2 | OPA policy input shape | **G p86** `input.caller.jwt_bearer.*` · **G p97** `input.agent.*` · **O** (Jul 2026) `input.jwt.*` · **O** (12 Oct 2026) `input.source_auth.claims.*`, `input.mcp.tool_name` on a surface policy · **D** (18 Oct 2026) two structs: `PolicyInput` → `input.source_auth.claims.*`, `McpPolicyContext` → `input.jwt.*` | **Largely resolved by scope** (#9): two structs, with a mapping table. The July `input.jwt.*` row is kept; reading it as an MCP tool policy is inferred. `input.caller.jwt_bearer.*` is absent from the current docs and marked do-not-use |
| C3 | Gateway's OAuth callback path for delegation | **G p80** `https://<host>/oauth/callback/<provider>` · **O** (Jul 2026) `https://<host>/v1/identity/oauth/callback/<provider>` | Says take the exact value from the credential provider's own screen |

C1/C2 update (16 Oct 2026, **D**): the docs reference page for OPA policies now
gives `gateway.policy` / `surface.policy` and `input.source_auth.*`, with
`input.jwt.*` only for MCP tool policies. That agrees with the observed package
names but conflicts with the **O** `input.jwt.*` claim for surface policy; left
as observed, not overwritten. Still unverified on a live gateway.

C2 update (18 Oct 2026, #9): observed 12 Oct 2026 that a surface policy reads
`input.source_auth.claims.email` and `input.mcp.tool_name`, which agrees with the
docs for surface policy. The tool-policy half (`input.jwt.*`, `input.mcp.method`)
remains docs-only; not observed.

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
| B13a | A payload-extraction schema must mark fields `"x-identity": true`; without it the save is rejected `400 … no identity fields are declared` | 28 Aug 2026 | needs a surface |
| B13b | An identity schema describes everything under the extension URI as that sender wrote it; nothing un-nests it. An inbound schema containing the `agentIdentity` wrapper extracted `identityFields: {"agentIdentity.name": …}`. **Unknown:** what the meta field does (guess: names the key under MCP `_meta`, unused for A2A). Docs refer to `_meta.[field]` but do not describe A2A or path handling | O, one working surface, host and date not recorded (#2); D, Identity reference page, 20 Oct 2026 | needs a surface |
| B13c | *Superseded by B13b, kept for traceability:* "declared paths are relative to the meta field" and dotted `identityFields` keys mean a stray meta field. Inferred 28 Aug 2026, never confirmed; contradicted by observation (#2) | 28 Aug 2026 | contradicted |
| B14 | Inbound identity travels as `…/agent-identity-binding/v1`; the response leg as `…/agent-identity-credential/v1`. Each leg's element mints its own surface-scoped `did:webvh`; the issuer is the gateway instance DID for both | 28 Aug 2026 | needs a surface |
| B15 | The response-leg credential's subject is a **`workloadBinding`** — `agentIdentity`, `userIdentity.id` (the DID minted on the inbound leg), `delegated`, `traceId` — not `identityFields`. **Unresolved:** whether the Identity element mints this alone, or a Workload Binding element was also active | 28 Aug 2026 | needs a surface |
| B16 | A payload-extraction schema on the **inbound** leg whose marked, required field is absent from the payload **saves successfully**, then refuses every message `422 identity_validation_failed: Identity field 'name' not found in payload`. Seen with a flat response-leg schema on the inbound leg of a client that nests under `agentIdentity`. **Unknown:** whether `required` or `x-identity` triggers it (the wording suggests the marker — inferred, not tested); the reverse swap on the response leg; MCP surfaces | Sep 2026, one hosted gateway, host not recorded; reported by a Lab reviewer (#4) | needs a surface |
| B20 | On a surface policy (access point → managed agent leg, MCP surface, JWT Bearer caller context vs a Keycloak issuer, identity from `email`), `input.source_auth.claims.email`, `input.mcp.tool_name` and `input.mcp.params.arguments` held the caller email and tool call, and a `deny unless admin` rule worked as written | 12 Oct 2026, one running gateway, host not recorded (#9) | needs a surface |
| B21 | With *From JWT Claims* identity extraction on a JWT Bearer surface, a request with no token and one with a junk token both got `500 … "from_jwt_claim requires jwt_bearer source auth on this surface"` instead of reaching the policy as `method: "failed"`. **Contradicts or qualifies D9.** Unknown: whether specific to *From JWT Claims*, to MCP, or by design | 12 Oct 2026, one running gateway, host not recorded (#9) | needs a surface |

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

---

## Docs-sync: OPA policies

All **D**, <https://docs.affinidi.com/products/affinidi-trust-fabric/agent-gateway/reference/surfaces/opa-policies/>, checked 16 Oct 2026. Not observed on a gateway.

| # | Claim | Where |
| --- | --- | --- |
| D1 | Gateway scope `gateway.policy`, surface and MCP-tool scope `surface.policy`; `channel.policy` rejected | configuration.md §3 |
| D2 | Optional input keys are omitted when absent, so reads are `undefined` and deny under `default allow = false` | configuration.md §3 |
| D3 | Sensitive headers stripped from `input.http.headers` | configuration.md §3 |
| D4 | Enrich-with-agent-context toggle, default off, not on response policies | configuration.md §3 |
| D5 | Rego edits create immutable versions with a SHA; Test panel dry-runs unsaved Rego | configuration.md §3 |
| D6 | Deleting a referenced policy fails closed | configuration.md §3 |
| D11 | `fabric://` address is `<connection-point-id>/<remote-access-point-id>` (not gateway/surface); the **via Gateway Connection** routing mode builds it. Supersedes the G-based S7 spelling | configuration.md §1, SKILL.md, glossary.md. D, concepts/connections/gateways, 19 Oct 2026 |
| D12 | Gateway record: self vs remote, fixed DID, Publishing tab (empty = all exposed), Global Policy direction and deny-wins, Connection failed alert | dashboard.md. D, reference/gateways/gateway, 19 Oct 2026 |
| D13 | Pairing needs a DIDComm mediator v0.17.x+ on both gateways | dashboard.md. D, concepts/connections/gateways, 19 Oct 2026 |
| D7 | Global enforcement, Monitor mode, deny-overrides order, fail-closed on unresolved Global | configuration.md §3 |
| D8 | Two input structs: `PolicyInput` (gateway, surface) and `McpPolicyContext` (MCP tool); `source_auth` shapes per method; field mapping table; per-path availability table; `input.source_auth` absent in tool policies | configuration.md §3 |
| D9 | Caller Context validates but "no longer blocks a request on its own when validation fails"; deny on `input.source_auth.method`; `source_auth` present with `method: "failed"` after a failed auth; unprotected, the request is forwarded as if Caller Context were absent. **Not observed; see B21** | configuration.md §2, SKILL.md gotcha 4, troubleshooting.md |
| D10 | `authorization`, `proxy-authorization`, `cookie`, `set-cookie` and headers containing `token`, `secret`, `credential`, `apikey`, `api-key` never appear in `input.http.headers` (extends D3) | configuration.md §3 |
