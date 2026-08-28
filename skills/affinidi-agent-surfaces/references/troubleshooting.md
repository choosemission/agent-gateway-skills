# Troubleshooting

Match the response you got to a row, and the row names the cause. Most gateway
errors are precise about *what* failed and silent about *why*, so the mapping is
worth more than the message text.

Error strings change between versions. Match on shape, not on wording.

## Response to cause

| Response | What it means | What to do |
| --- | --- | --- |
| `404 No route configured for path: …` | No live route on that prefix and path | Confirm the configuration saved; a dashboard reload triggers a route-cache refresh. Check the prefix — the administrator chooses them per gateway. |
| `-32600 Invalid JSON-RPC request` | It is an MCP door and you sent a plain body | Wrap the call: `initialize`, then `tools/call`. |
| `Missing 'method' field in JSON-RPC request` | Envelope present, no `method` | Add one. |
| `422 … protocol 'a2a' does not match access point protocol 'mcp'` (or the reverse) | Wrong protocol for this surface | The method name selects the protocol: `message/send` is A2A, `initialize` and `tools/*` are MCP. Use the one the surface declares. |
| A policy denial, identically for every caller | Usually the policy package does not match where the policy is attached | An undefined `allow` denies. Check the package before auditing the rules — and check it against your gateway, because the documentation is inconsistent. `configuration.md` §3. |
| A policy denial for some callers only | The policy is doing its job, or the caller claims are empty | If empty for everyone, there is no Caller Auth element — see below. |
| A denial that no surface policy explains | A **gateway-level** deny, which is final and runs first | Check the Gateway scope tab, not just the surface's. Nothing at surface level can override it. |
| `tools/call` denied for a tool you did not write a rule about | MCP tool policy defaults to deny for unmatched tools | Add an entry for that tool, or a `*` wildcard entry. |
| `429` with `Retry-After` | Rate limit | Token bucket: requests per second and burst size, on the surface. |
| A circuit-breaker error with no backend call attempted | The circuit is open after consecutive failures | Fix the backend; the circuit half-opens after its timeout and closes on success. |
| Upstream returns *its own* auth error (401/403 about a bad key) | The gateway is not injecting, or is injecting the wrong thing | **Static key:** the target authentication binding — check secret value *and* header name. **Per-user OAuth:** the surface's credential delegation for that target. Two different objects. |
| The backend's own JSON-schema complaint about `jsonrpc` being an unexpected field | The agent-protocol envelope is reaching a backend that cannot read it | The target must speak the surface protocol. A REST backend needs an **MCP Proxy** in front of it. An LLM does not belong on the Gateway at all — that is Agent Stream. |
| `502 builder error for url 'proxy://<uuid>'` on a GET | A live surface, reached without the protocol handshake | Benign. POST an `initialize` instead. |
| A framework 404 from your own backend — `Cannot POST /`, or an HTML error page | The target endpoint is the origin's **base** URL, so the path is dropped | Put the full path on the endpoint (`https://host/mcp`). Serving MCP at `/` as well removes the problem permanently. |
| `406 Not Acceptable` from your backend, mentioning `text/event-stream` | MCP Streamable HTTP requires the caller to accept both `application/json` and `text/event-stream`; the relayed request may carry `*/*` or nothing | Handle it in the backend: fill the header in when the caller expressed no preference. |
| A managed-agent or target node still showing incomplete after you saved the URL | Malformed URL, or trailing whitespace | Re-save and refresh the designer. The Elements view lists every incomplete element in one place. |
| `Error 400: redirect_uri_mismatch` from the **caller's** IdP | A gateway URL is registered where the application's own callback belongs | Register your app's callback. The gateway is not in the inbound redirect flow. |
| `consent_required` on a user's first call | **Expected.** The delegation flow has not run for this user yet | The client must open the authorization URL and retry the same call. Only a bug if it never clears. |
| `consent_required` returns again after the user has approved | The credential provider's client ID/secret references, or its callback registration, do not match the upstream | Re-check the secret references and that the gateway's callback is registered at the upstream. Take the exact callback path from the provider's own screen — it has changed between versions. |
| Every user appears to share one upstream credential | Caller identity extraction is unset or on a non-unique claim | The vault is keyed by agent identity + user identity + provider. Set extraction to a unique claim. |
| A tool call demands an API key the gateway was meant to inject | Delegation or target authentication is not bound for that target | The caller should not need to supply it. Check the binding, not the caller. |
| The audit log shows no records | Workload Binding is absent, or its enable toggle is off | It is a separate element and must be added deliberately. |
| The agent's DID changes between otherwise identical calls | A dynamic value is marked as an identity field in the payload schema | Timestamps and request IDs must not be identity fields. Mark only stable, configuration-level fields. |
| `400 … identity extraction is configured (meta_field='…') but no identity fields are declared` | The schema describes the payload but marks nothing as contributing to the DID | Add `"x-identity": true` to each field that should form the identity. Describing a field is not declaring it. |
| `identityFields` keys come back dotted — `{"agentIdentity.name": …}` — on a leg you meant to be flat | The meta field was left set, so declared paths are relative to it | Clear the meta field when the sender writes its descriptor flat. The two ends of one exchange often nest differently and need different schemas. |
| The agent's DID changes after a redeploy | A version field is marked as an identity field | Mark `name`, `model` and `role`; leave `version` out, as Affinidi's own `identity-extension.json` does. |
| The reply carries no credential, though the inbound message does | Identity is configured on the inbound leg only | The agent's own identity is a **second** Identity element, on the managed agent → access point **response leg** — not a setting on the Managed Agent node, which offers only the *Identity Binding VP* switch. |
| A change to a listener address or port has no effect | Listener bindings are **startup-only** | Everything else hot-reloads; this needs a process restart. |

## When identity looks broken

Two symptoms, one cause. Both mean **the surface has no caller context**, not
that something rejected the caller:

```
x-caller-did: anonymous
x-caller-identity-source: gateway-computed
```

and, inside a policy, empty caller claims.

Add a **Caller Auth** element referencing a JWT verification strategy, and set
caller identity extraction; `x-caller-did` then carries the extracted claim. The
Access Point's **caller context mode** (required / optional / anonymous) is the
other half of the switch.

Log `anonymous` distinctly in your target, because it otherwise reads as a
participant whose name happens to be "anonymous", and you can spend a while
wondering why identity is not working when it was never switched on.

A policy that gates on caller claims against a surface with no caller context
denies every request and looks like a Rego bug.

Two related traps that look like gateway problems and are not:

- An `iss` comparison failing on a **trailing slash**.
- A **group claim absent from the token** because the IdP was never told to
  include it. With Entra that is an app-manifest change.

## Which OAuth leg?

Almost every identity problem resolves once you name the leg. Ask: *is this about
who is calling in, or about what we present upstream?*

| | Inbound (caller context) | Outbound (delegation) |
| --- | --- | --- |
| Symptom lives at | The caller's IdP, or the policy | The upstream service |
| Redirect URI | Your application's callback | The gateway's own callback, registered upstream |
| `redirect_uri_mismatch` means | You registered a gateway URL here | The provider name or callback path does not match what is registered upstream |
| Empty result | Empty caller claims, `x-caller-did: anonymous` | Upstream's own 401, or a consent loop |

## MCP client sign-in against a gateway URL

Before designing around a standard MCP client discovering and completing OAuth
against a gateway route unaided, check the discovery chain:

```bash
curl -si "https://$HOST/.well-known/oauth-protected-resource" | head -20
curl -si "https://$HOST/.well-known/oauth-authorization-server" | head -20
```

You want JSON with the right content type, and an **absolute** URL in the
`resource_metadata` parameter of the `WWW-Authenticate` challenge. If either
document returns HTML, the client follows the pointer, receives a web page and
stops.

Observed on one hosted gateway in July 2026: the challenge was issued and token
verification worked, but the discovery documents returned the dashboard's HTML.
Verify rather than assume, and raise it with Affinidi if you find it. Where a
client must sign in for itself today, the **dual-leg** pattern in
`securing-the-resource.md` is the practical arrangement.

## Debugging order

1. **Identify the route** before sending a payload — `GET` it.
2. **Test the backend directly**, outside the gateway. Separating "is the backend
   up" from "is the trust layer working" turns one five-layer problem into two
   one-layer problems.
3. **Turn on payload capture** for the surface. Four stages — inbound request,
   outbound request, inbound response, outbound response — will show you exactly
   what the gateway sent, which is faster than inferring it.
4. **Check the Audit view** for the policy decision and its reason before
   rewriting the policy.
5. **Read the trace ID.** `X-Gateway-Trace-Id` ties the dashboard's record to your
   logs; quote it, with a timestamp, when asking an operator for help.
6. **Change one thing.** Tunnel hostname, target URL, secret and redirect
   registration all fail with overlapping symptoms; changing two at once means
   learning nothing from the result.

## Common mistakes

- **Expecting the gateway to relay non-agent traffic.** It enforces A2A and MCP
  and translates neither on the inbound path. REST goes behind an MCP Proxy; LLM
  and agent-to-dependency traffic is Agent Stream's job, not the Gateway's.
- **An MCP proxy in front of a backend that already speaks MCP.** The proxy exists
  to turn REST into tool calls; an MCP backend wants the envelope relayed
  untouched, which is a plain HTTP(S) target.
- **Right Rego, wrong package or wrong scope.** A permissive rule in the wrong
  package denies everything; a gateway-scope deny cannot be argued with at surface
  level.
- **Looking for outbound settings on the response path.** Outbound means
  agent-initiated calls through a **Transit Point**. The response is the
  MA→Access-Point response leg. Two different things.
- **Rewiring the topology graph expecting the bytes to change.** Arrows declare
  who may call whom, not translation. What a `GET` on the route reports is the
  runtime binding, and that is the source of truth.
- **Omitting the SSE `Accept` header** on MCP calls. Send
  `Accept: application/json, text/event-stream` and strip the `data: ` prefix.
- **Leaving the resource's own URL open after putting it behind a surface.**
  Produces no error; the tell is an audit trail quieter than your traffic. See
  `securing-the-resource.md`.
