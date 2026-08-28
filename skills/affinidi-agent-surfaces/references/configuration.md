# Configuration: the governed path

What you set to get a caller reaching a target under policy, with a credential
the caller never holds. This is the common path and the file to open first.

Once traffic is flowing, `identity-and-controls.md` covers what you add to a
working surface: agent identity and DIDs, transit points and outbound
governance, variants, traffic management, validation and capture.

Where a claim was **observed on a running gateway** rather than taken from the
reference guide, it says so — the two do not always agree, and the running
gateway wins on behaviour.

Settings attach to one of four places, and putting one on the wrong place is a
common source of lost time:

| Attaches to | Typical settings |
| --- | --- |
| **Gateway** | Gateway-level policy, secrets, credential providers, JWT strategies, policy definitions, issuers, authorities, proxies |
| **Access Point** | Source authentication, caller context mode, inbound rate limiting, route path |
| **Surface** | Protocol, target, identity slots, surface policy, variants, transit token mode, and the traffic controls in `identity-and-controls.md` |
| **Transit Point** | Its own listener, target, protocol, credentials, policy, payment policy, transit-token requirement, managed-identity override |

---

## 1. Protocol and target

A surface declares **one surface protocol** — A2A or MCP — spoken at both ends of
the inbound path. **No protocol translation inbound.** If the backend speaks
neither, give it an MCP face with an MCP Proxy, or the traffic does not belong on
the Gateway (see `glossary.md`, *Which appliance owns this?*).

| Target type | Address | Use when |
| --- | --- | --- |
| **HTTP(S) upstream** | `https://host/path` | The target already speaks the surface protocol |
| **MCP Proxy** | `proxy://…` | The backend is a REST API |
| **A2A Proxy** | `a2a-proxy://{id}` | The backend is a Copilot Studio agent over Direct Line |
| **Fabric** | `fabric://<gw>/<surface>` | The target is a surface on a peer gateway |

Put the **full path** on an HTTP(S) target (`https://host/mcp`, not
`https://host`). A base URL drops the path and produces a 404 from your own
framework.

Transit Points are the one exception to no-translation: a TP may use a different
protocol from its surface.

### MCP Proxy

Created under **Agent → Proxies**, then selected as a surface's target.
Configuration-only, no code:

- **Base URL** — the root of the REST API.
- **API description** — OpenAPI 3.0, YAML or JSON. **Each path/method pair
  becomes a tool** automatically. Validate before saving.
- **Routing** — listener, route prefix and custom path, forming the proxy's own
  address.
- **Parameter handling** — including *Flatten POST Parameters*, which lifts body
  parameters to the top level of the tool's input schema so clients send flat
  arguments instead of nesting them.

**The proxy supplies the tool catalogue; the surface supplies authentication,
policy and per-tool access control.** Both are needed.

A **Sandbox** tab on the proxy or surface browses the discovered catalogue and
invokes tools from the dashboard — the fastest way to confirm the spec produced
the tools you expected.

### A2A Proxy

Also under **Agent → Proxies**, behind the Copilot integration feature flag.
Three tabs: **Overview**; **Backend** (backend type, the stored Direct Line
secret, and whether to use it directly or exchange it for a per-session token —
the latter recommended for production); **Agent Card** (overrides for the
synthesised card, and the identity source: a Microsoft Entra agent identity from
Copilot header metadata mapping, or a proxy-managed subject). The proxy
synthesises an agent card, handles Direct Line's polling, and presents the bot as
a native A2A agent. All surface controls still apply.

## 2. Source authentication and caller context

The Access Point owns caller authentication. **Several methods may be configured
at once and are evaluated in order.**

| Method | Notes |
| --- | --- |
| **JWT Bearer** | Names a JWT verification strategy. Header name and scheme prefix configurable. |
| **API Key** | Against keys in **Secrets → API Keys**. Extraction names a header or query parameter. |
| **API Key Provider** | The same, delegated to an external validating service. |
| **DID Auth** | A DID-based session credential. |
| **mTLS** | Direct TLS termination or forwarded XFCC headers. Identity binds to fingerprint, subject CN, DNS SAN, URI SAN, or a custom RDN. |

**Caller context mode** on the Access Point decides whether caller identity is
**required**, **optional**, or whether **anonymous** requests are allowed. This is
the switch behind `x-caller-did: anonymous`.

### The JWT verification strategy

Created once at gateway level (**Management → Credentials → JWT Verification**),
referenced by any number of surfaces:

- **Expected issuer** — the exact value `iss` must match.
- **Key source** — **Remote** (fetch and cache the issuer's JWKS; keys rotate
  with no config change, but the URL must be reachable at verification time) or
  **Static** (keys stored in the strategy; no dependency, manual rotation).

Take both from the IdP's `/.well-known/openid-configuration` rather than typing
them.

Validation order: read the token → look up the strategy → obtain keys → verify
the signature → check `iss` matches exactly, the token is unexpired, and the
audience is acceptable if the surface names any → claims become available to
policy.

**A misconfigured strategy or unreachable keys fail the request** — the gateway
never falls back to allowing unverified traffic once inbound authentication is
configured. Deleting a strategy immediately breaks every surface referencing it.

### On the surface: the Caller Auth element

Drag **Caller Auth** onto the leg between access point and managed agent, set the
extraction method, select the IdP, and optionally restrict acceptable audiences.
Blank audiences accept any valid one — fine for first testing, not production.

Claims then reach every later element: policy, identity resolution, workload
binding, the audit log.

## 3. Policy

OPA/Rego, stored as **policy definitions** at gateway level and attached by
**reference**, so one definition serves many surfaces and an edit propagates.
Changes take effect on the next request, no restart. A **disabled** policy is
skipped entirely, which allows the traffic it would have governed.

| Scope | When it runs |
| --- | --- |
| **Gateway** | First, for every request on the instance. **A deny is final.** |
| **Agent Surfaces** | Only if the gateway gate passed, close to the point of forwarding. |
| **Paywall** | Payment conditions. |

### Package names — verify against your gateway

The package must match where the policy is attached, or `allow` lands in a
namespace the evaluator never reads — and an undefined `allow` denies,
identically for every caller.

**The vendor documentation is not self-consistent here**, so verify rather than
assume:

| Source | Package |
| --- | --- |
| Observed on a running gateway (Jul–Aug 2026), gateway level | `package gateway.policy` |
| Observed on a running gateway (Jul–Aug 2026), surface level | `package surface.policy` |
| Reference guide v0.3.10, surface-level example | `package surface.policy` |
| Reference guide v0.3.10, delegation walkthrough, surface-attached element | `package gateway.authz` |

Take the package from a working policy on the gateway in front of you, or from
the console's own template, and report the inconsistency to Affinidi.

### What a policy can read

Also version-sensitive:

| Source | Shape |
| --- | --- |
| Reference guide, delegation walkthrough | `input.caller.jwt_bearer.iss`, `.groups` |
| Reference guide, Q&A section | `input.agent.trust_verification` |
| Observed on a running gateway (Jul 2026) | `input.jwt.*`, `input.http.method/.path/.headers`, `input.gateway.direction` |

By content the bundle carries: HTTP method, path and headers; direction and the
source and target identities; surface context including name and selected
variant; the caller's verified claims; protocol-specific detail such as the MCP
method; `trust_check_results`; and payment and metadata context.

**Print the input before writing rules against it.** A policy that returns
`input` on a permissive test surface tells you the real shape in one request,
which beats reasoning from any document.

```rego
package surface.policy

default allow = false

# Anything with a verified caller identity.
allow if {
  input.jwt.sub
}
```

Start from `default allow = false` for anything beyond a throwaway test. A
surface with `default allow = true` is callable by any anonymous client on the
public internet.

Two recurring traps that look like gateway problems: an `iss` comparison failing
on a **trailing slash**, and a **group claim absent** because the IdP was never
told to include it (with Entra, an app-manifest change).

### MCP tool policy

Finer-grained than the surface policy. On an MCP target, each entry names a tool
and points at a policy definition. `*` is a wildcard. **A `tools/call` for a tool
with no matching entry and no wildcard is denied** — an incomplete tool policy is
a deny-list by accident. Tool visibility can also be filtered by JWT claims, so
an unauthorised tool is invisible in `tools/list` rather than refused on call.

## 4. Target authentication — the static outbound credential

One secret, presented on every call to the external target. No user, no consent,
no per-caller scoping. This is what closes the ungoverned path to your resource.

The key is one **you invent** — nothing issues it and the gateway does not
generate one:

1. Generate it: `openssl rand -hex 32`.
2. Configure the resource to require it on a header of your choosing
   (`x-api-key` conventionally), rejecting unconditionally and early.
3. **Management → Secrets** → new secret holding that value.
4. On the surface, set the credential the managed agent presents to the target:
   select the secret, set the header name from step 2. This has appeared both as
   *Target Authentication* on the Managed Agent node and as an API Key credential
   binding on the MA→External leg — check which your version offers.

**Two things must match, not one:** the header name the resource reads, *and* the
secret value it expects. Either mismatch produces the same symptom — the
resource's own 401 arriving through a surface that is otherwise working — which
reads like the gateway is not injecting at all.

Secrets are referenced by identifier (`$secret:…`) so the value never appears in
a surface's config. Generic secrets are shown in full **once**, at creation.

Rotation and verification: `securing-the-resource.md`.

## 5. Credential delegation (per-user OAuth, outbound)

For when the upstream needs *the calling user's* credential rather than one
shared secret. Order matters — each step yields a value the next one needs.

1. **Expose the upstream** and note its URL.
2. **Build the surface.** Save the **Access Point URL** and the
   **credential-provider callback URL**.
3. **Register your application's own callback** at the caller's IdP.
4. **Register the gateway's callback** at the **upstream** provider. The path has
   changed between versions — the guide shows
   `https://<gw-host>/oauth/callback/<provider-name>`, while
   `https://<gw-host>/v1/identity/oauth/callback/<provider-name>` was observed in
   July 2026. **Take the exact value from the credential provider's own screen.**
5. **Create secrets** for the upstream's client ID and secret.
6. **Create the credential provider** (**Management → Credentials → Credential
   Providers**), type OAuth 2.0 Authorization Code, pointing client ID and secret
   at the **secret references**. Set scopes and auto-refresh. Take the
   authorization and token endpoints from the upstream's
   `/.well-known/openid-configuration`.
7. **Create the JWT verification strategy** for the caller's IdP.
8. **Wire both into the surface** — Caller Auth inbound, and a **Credential
   Delegation** element on the MA→External leg.

Steps 3 and 4 are different callbacks at different providers for different
reasons — see the two-legs table in `SKILL.md`.

Per binding on the delegation element: credential provider, scopes, **consent
mode**, *required for* (all outbound requests, or narrower), and **inject as**
(Bearer header, custom header, or protocol metadata).

### Consent modes

| Mode | Behaviour | Choose when |
| --- | --- | --- |
| **Pre-authorize** | Blocks the session at MCP initialisation if any required credential is missing, returning the authorisation URLs. | You would rather fail at connect time than mid-task. |
| **On-demand** | Proceeds until a tool call needs a missing credential, then returns a structured error carrying `consent_required` and the authorization URL. The client completes OAuth out-of-band and **retries the same call**. | The client can handle an out-of-band prompt. The common default. |
| **Elicit** | MCP-native. An elicitation over the established stream, original call held open, resumed in place once the credential lands. | The client implements MCP elicitation. Best experience where it works. |

In all modes the token goes to the **gateway's** callback, never to the client.

**Proof it is per-user:** a second user gets their own consent prompt instead of
inheriting the first user's access. Vault entries are keyed by agent identity +
user identity hash + provider, so if that is not what happens, caller identity
extraction is unset or on a non-unique claim.

The **Delegation Tokens** tab shows the vault; **Credential Audit** shows which
agent called which provider for which user, the outcome, and the trace ID.

