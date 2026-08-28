# Worked patterns

Three end-to-end examples. Read once you know what you are building;
`configuration.md` and `identity-and-controls.md` are the per-setting references.

## 1 — your own MCP server behind a governed surface

The simplest governed target, and a good first thing on an unfamiliar gateway.

```
Caller → MCP surface (policy) → HTTP(S) target → your MCP server
                                     ↑
                              API key injected
```

0. **Create the secret first**, at gateway level. The surface cannot select a key
   that does not exist yet.
1. **Host the MCP server** at a reachable URL, serving MCP at a known path.
2. **Require a credential on it** — `securing-the-resource.md`. Do this as you
   stand it up, not afterwards: the moment it is reachable enough for the gateway
   to call, it is reachable enough for everyone else.
3. **Create the surface** from the MCP template, HTTP(S) target with the **full
   path** (`https://host/mcp`).
4. **Bind the target credential** — the secret, on the header name the server
   reads. `configuration.md` §4.
5. **Attach a policy**, with the package your gateway expects.
6. **Verify both directions** — the access point works with no credential of your
   own; the server's own URL returns 401.

Expect the backend to want an SSE-friendly `Accept` header. The gateway relays
what the caller sent, so handle the empty case in the server.

Add **Caller Auth** once that works, and only then write a policy gating on
caller claims. A policy reading claims before Caller Auth exists denies
everything and looks like a Rego bug.

## 2 — a REST backend given an MCP face

```
Caller → MCP surface (policy, tool policy) → MCP Proxy (tools ← OpenAPI) → REST API
```

**Create the proxy** (Agent → Proxies → New MCP Proxy) with the API's base URL,
its OpenAPI 3.0 spec, and routing. Each path/method pair becomes a tool; Validate
before saving. **Create an MCP surface** with target type MCP Proxy and pick it —
the gateway writes the `proxy://…` reference. Then **configure surface controls**,
all of which apply because the traffic is MCP: source auth on the Access Point, a
surface policy, and **MCP Tool Policy** entries per tool. `*` is the wildcard, and
a `tools/call` with **no matching entry and no wildcard is denied** — so an
incomplete tool policy silently becomes a deny-list.

**Test** with the **Sandbox** tab on the proxy or surface, which browses the
discovered catalogue and invokes tools from the dashboard. Then from outside:

```bash
URL="https://$HOST/$PREFIX/$PATH"
H=(-H "Content-Type: application/json" -H "Accept: application/json, text/event-stream")
curl -s -X POST "$URL" "${H[@]}" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | sed -n 's/^data: //p'
```

Two details that catch people:

- **Arguments nest under `request_body`** for OpenAPI-derived proxy tools, unless
  you enabled parameter flattening.
- **The response is double-wrapped.** MCP `result.content[].text` holds a JSON
  string, and inside it `{"status":200,"body":{…}}` is the proxied HTTP response.
  Parse twice.

On a `tools/list` against an OpenAPI-wrapped proxy, a secret parameter such as an
API key may still appear in a tool's input schema. The gateway should inject it
and you should omit it; if a call fails demanding it, the binding is not set up
and the caller is being asked to hold what it never should.

### Choosing a target type

Ask what the backend already speaks, not what it is called.

| Backend | Target type |
| --- | --- |
| Already speaks MCP or A2A | HTTP(S) upstream |
| Speaks REST / OpenAPI | MCP Proxy |
| A Microsoft Copilot Studio agent | A2A Proxy |
| Lives behind another gateway | Fabric (`fabric://…`) |
| Is an LLM, or a plain web dependency the agent calls | **Not the Gateway.** Agent Stream — `glossary.md` |

## 3 — user-scoped credential delegation

A signed-in human reaches a protected upstream through the gateway, and the
gateway attaches *that user's* upstream credential. The application holds only
the user's own identity token and never sees the upstream secret.

```
Browser → your client → MCP surface → upstream MCP service
              │              │
        caller's IdP    gateway's delegation vault
        (JWT, verified) (keyed per agent + user + provider)
```

Affinidi's canonical example is a chatbot reaching the GitHub MCP server with
Microsoft Entra as the corporate IdP. The shape generalises to any IdP and any
upstream. Ordered setup is in `configuration.md` §5 — out of order means
revisiting screens, because each step yields a value the next one needs. The
surface ends up carrying **Caller Auth**, **Identity**, **Credential Delegation**
on the MA→External leg, and **Workload Binding**, plus a policy.

**The first call is supposed to fail.** In on-demand mode:

1. The client registers the access point as an MCP server and initialises.
2. The gateway tries the upstream, holds no credential for this user, and returns
   `consent_required` with an authorization URL.
3. The user approves. **The token goes to the gateway's callback, not the
   client** — the client never sees it.
4. The client retries the same call and it succeeds.
5. Every later request from that user has the credential injected automatically.

**How to tell it is genuinely per-user:** a **second** user gets their own consent
prompt rather than inheriting the first user's access. That is what distinguishes
real delegation from one shared credential.

**What the audit shows** — two kinds of record, both signed VPs. A **consent
record** for the initial authorisation (JWT issuer, client, subject, target
server, the tool that triggered consent, the agent's DID, the trace ID), and a
**workload record** per tool call (the same binding plus the tool chosen and the
full intent payload). Together they attest which user, using what credential,
through which agent, reached which server, with what intent, and what happened —
each independently verifiable from the gateway's public key material.

Turn on **PII obfuscation** if those records will be retained.

**Tunnel churn is the main time sink.** A restarted tunnel changes the hostname,
invalidating the target URL, the IdP redirect registration and the application's
own base URL at once — and the errors point at whichever you notice first.
Reserve a static tunnel domain before iterating.

## Changing a live surface without breaking it

Use a **variant**, not an in-place edit and not a clone.

1. Create a variant from the current base, with a descriptive alias.
2. Make the change on the variant only.
3. Point a test client at the **same** access point URL with `$alias` appended.
   Production traffic, arriving without it, still gets the base.
4. Promote the alias to default. All traffic follows, no URL change for callers.

## Probing an unfamiliar gateway

```bash
# Which prefixes are proxy-handled rather than served by the dashboard?
for p in routes agents mcp a2a inbound agent tools connect; do
  out=$(curl -s -m 15 "https://$HOST/$p/__probe__")
  echo "$out" | grep -q 'a2a-protocol.org' && echo "PROXY-HANDLED: /$p" || echo "               /$p"
done
```

Route prefixes are per gateway, so discover rather than assume: the listener form
is `scheme://host/route/custom/path`. Management APIs return 401 to anonymous
callers — that is the expected result, and it tells you the prefix exists.

For an A2A surface, the agent card is served from the access point at
`/.well-known/agent-card.json`, with URLs rewritten to point at the gateway.

**One thing the topology graph does not do.** Arrows declare who may call whom,
not translation. Re-pointing them will not change the bytes on the wire; only an
MCP-proxy or A2A-proxy target changes the payload.
