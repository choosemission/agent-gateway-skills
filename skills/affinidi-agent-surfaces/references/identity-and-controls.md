# Identity and controls

What you add to a surface that already carries traffic: a verifiable agent
identity, governance over what the agent calls *out* to, and the operational
controls. `configuration.md` is the file for getting a governed call flowing in
the first place.

---

## 1. Agent identity

**Identity is configured per leg.** You drag an **Identity** element onto a leg
of the surface, and it resolves a DID from what crosses that leg.

| Leg | Resolves | Extension seen on the wire |
| --- | --- | --- |
| Access Point → Managed Agent (**inbound**) | the **caller's** identity | `…/agent-identity-binding/v1` |
| Managed Agent → Access Point (**the response leg**) | the **managed agent's** identity | `…/agent-identity-credential/v1` |

Both legs can carry one at once, and each element mints its **own**
surface-scoped `did:webvh` — two elements on one surface produce two different
DIDs.

> **The agent's own identity is configured on the response leg, not on the
> Managed Agent node.** The Managed Agent carries only *Identity Binding VP*
> ("send signed identity VP to target"), which decides whether what has already
> been resolved is stamped into the forwarded request. It is a switch, not a
> place to define an identity. Looking for identity configuration there and
> concluding the feature is missing costs an hour.
>
> Mind the vocabulary while you are there: this is the **response leg**, not the
> "outbound leg". Outbound on this gateway means Transit Points. The canvas
> invites the other reading, and the product does not use the word that way.

### Managed identity modes

| Mode | DID derived from |
| --- | --- |
| **Payload extraction** | Fields in the request payload, against a schema |
| **From mTLS** | The client certificate — fingerprint, subject CN, DNS or URI SAN, or a named subject field |
| **From API key** | The inbound key's **identifier** |
| **Static** | A fixed DID regardless of caller |
| **From JWT claim** | A claim in the validated token, with optional namespace claims (issuer, tenant) folded in so the same value under different tenants yields distinct identities. This is the Microsoft Entra Agent ID mode. |

For credential-based modes the DID comes from the credential's **identifier**,
not its secret — so rotating the secret keeps the DID stable. Managed identities
are versioned: rotate keys to refresh cryptographic material while the stable DID
others rely on survives.

**Payload extraction is self-asserted.** The DID is a deterministic hash of
fields the sender chose to send about itself, so the same fields always yield the
same DID — a stable pseudonymous identifier the gateway signs, not proof that the
sender is who it says. When the DID must be anchored in something the caller has
to possess, use mTLS, API key or JWT claim instead. Say which of the two you mean
when you tell someone the traffic is "identified".

### Payload extraction

The deterministic-DID path: the gateway hashes fields the agent already sends
about itself and mints or reuses a `did:webvh` for that exact configuration.

- **A2A** — the agent names the extension point
  `https://fabric.affinidi.io/extensions/agent-identity/v1` in `extensions` and
  supplies the descriptor under the same key in `metadata`.
- **MCP** — the descriptor sits under `_meta.agentIdentity`, keeping identity out
  of tool parameters and working across HTTP, SSE and stdio.

Configuring it:

1. Drag the **Identity** element onto the leg you mean — inbound for the caller,
   the response leg for the managed agent.
2. Set extraction type to **Payload**.
3. Set the **meta field** to match how that sender nests its descriptor, and
   leave it **empty** when the descriptor is flat. Declared field paths are
   relative to it.
4. Give it a JSON Schema and **mark every identity field with
   `"x-identity": true`**. That marker is what declares a field as contributing
   to the DID. A schema that describes the payload but marks nothing is rejected:
   `400 … identity extraction is configured (meta_field='…') but no identity
   fields are declared`.
5. Optionally mark fields **required** (requests omitting them are rejected) or
   give them **value constraints** (only a named model or provider may call).

Rather than hand-write the schema, **capture a live payload**: *Capture Identity
Payload* exposes a temporary endpoint with automatic expiry; point your client at
it, trigger a call, then select the captured request and click *Use This Schema*.

A schema for an agent that sends its descriptor flat:

```json
{
  "type": "object",
  "properties": {
    "name":  { "type": "string", "x-identity": true },
    "model": { "type": "string", "x-identity": true },
    "role":  { "type": "string", "x-identity": true }
  },
  "required": ["name", "model", "role"]
}
```

**The two ends of one exchange often nest differently**, so a surface with
identity on both legs needs two different schemas. In Affinidi's own `a2a/`
sample:

- the **client** sends `{"agentIdentity": {"name": …}}` under the extension key
  → meta field `agentIdentity`, path `agentIdentity.name`
- the **server** sends `{"name": …, "model": …, "role": …}` flat under the same
  key → meta field empty, paths `name`, `model`, `role`

The credential preserves whatever path you declared, so `identityFields` coming
back as `{"agentIdentity.name": …}` on a leg you meant to be flat tells you the
meta field was left set.

The failures to expect:

- **A DID that changes every call** — a dynamic value, a timestamp or a request
  ID, was marked as an identity field. Mark only stable, configuration-level
  fields.
- **A DID that changes on redeploy** — a version field was marked. Affinidi's own
  `identity-extension.json` marks `name`, `model` and `role` and deliberately
  leaves `version` out, for exactly this reason.

### What each leg puts on the wire

Observed 28 August 2026 on an `agentgateway.affinidi.io` gateway, A2A surface,
payload extraction on both legs.

**The presentation is serialised.** Under both extension keys, the metadata
entry is `{"verifiablePresentation": "<JSON string>"}` — a string, not a nested
object (the response leg adds a sibling `did`). A receiver that walks the
metadata as objects finds nothing and reports that no identity was presented,
which reads as a gateway misconfiguration and is not one. `json.loads` it first.

**Inbound.** The caller's message reaches the agent carrying
`…/agent-identity-binding/v1`, whose credential subject — once decoded — is the
resolved caller DID and the extracted values:

```json
"credentialSubject": {
  "id": "did:webvh:…:surface:<uuid-A>",
  "identityFields": { "agentIdentity.name": "A2A Test Client" }
}
```

**The response leg.** The agent's reply reaches the caller carrying
`…/agent-identity-credential/v1` — and its subject is **not** `identityFields`
but a **workload binding**:

```json
"credentialSubject": {
  "id": "did:webvh:…:surface:<uuid-B>",
  "workloadBinding": {
    "agentIdentity": { "name": …, "model": …, "role": … },
    "userIdentity":  { "id": "did:webvh:…:surface:<uuid-A>" },
    "delegated": true,
    "traceId": "…"
  }
}
```

`userIdentity.id` is the DID minted on the **inbound** leg. The gateway stitches
the two together, so a single exchange yields a signed record of *which agent
acted for which caller on this request*, with a trace ID that ties it to the
Payload Capture entry. Neither side wrote code to produce it.

Both credentials are issued by the **gateway instance** DID and held by the
surface-scoped DID of their own leg, so the holder differs per leg while the
issuer does not.

Whether the response-leg Identity element mints that workload binding on its own,
or whether a separate Workload Binding element must also be active, is **not
established** — see `CLAIMS.md` B12.

### Identity slots

Three DID positions on a surface, each with its own extraction rules and schema
validation: **inbound** (the caller), **protected** (a DID in a signed claim in
the payload), **external** (a DID the payload refers to that is not the caller).
The design lets a policy reason at once about who is calling, who is being
proxied for, and who the payload refers to.

### Identity injection and workload binding

**Identity injection** decides whether a Verifiable Presentation proving the
resolved DID is attached to forwarded calls. On the Managed Agent this is the
*Identity Binding VP* toggle; with nothing resolved on either leg it has no
effect, and the gateway log records a "skipped" entry.

**Workload Binding** is a separate element producing a signed VP **per request
execution**:

- **Enable workload binding** — the toggle. If the audit log shows no records,
  this is usually why.
- **Caller context source** — fixed to *Authorization bearer JWT* on the
  MA→External leg; on other transit points, that or *Transit token*.
- **Caller field allowlist** — top-level claims copied into the binding (`sub`,
  `email`, `name`, `org`). Empty binds agent identity only. **Nested claim paths
  are not supported.**
- **Chain caller-supplied credentials** — include a caller-presented VC/VP so a
  downstream gateway sees the full delegation chain.
- **PII obfuscation** — a surface setting replacing subject and email with a
  deterministic, non-reversible representation, so records stay correlatable
  without exposing identifiers. Off by default.

Identity VCs attest *who an agent is*. Workload binding VPs attest *what
happened*: which user, through which agent, called which tool, with what intent,
and how each credential binding resolved. The response-leg observation above is
the second kind arriving under the first kind's extension name.

DID documents are served at `/.well-known/did.jsonl`.

You can also keep key custody yourself: with Affinidi's Trust Developer Kit the
developer manages DIDs and signing, and the gateway lets an already-signed VP
transit unchanged rather than injecting its own.

## 2. Transit Points — governing what the agent calls out to

The outbound half, and the part most often missed. Each TP has its own listener,
target endpoint, transit protocol, service credentials, policy reference,
optional payment policy, transit-token flag, and managed-identity override.

### The transit token

Injected into every inbound request; the managed agent echoes it back when
calling a TP listener. It carries the caller's authenticated identity, the
originating surface ID, and the TP IDs this session may use. The gateway
validates it on the outbound call and confirms the TP is in the allowed set.

That closes the loop between inbound caller context and outbound capability:
without it, a managed agent can make outbound calls no inbound request
authorised.

**Transit token mode** is a surface-level default: **Embedded** (in the outbound
body), **Header**, or **None**.

An agent can always be pointed at destinations that do not transit the gateway,
and the gateway cannot see or control those. Routing dependencies through Transit
Points is what makes outbound governance real rather than nominal.

## 3. Surface variants

A named alternative configuration backed by one surface record. Callers select
one by appending `$alias` to the access-point URL; without it they get the
default. So you can point a test client at the same listener production is using,
target the new variant, and leave production untouched. When satisfied, promote
the alias to default and all traffic follows with no URL change.

This is the sanctioned way to change a live surface. Duplicating the surface
record instead gives you two records that diverge.

## 4. Traffic management

Independently toggleable, identical for A2A and MCP.

| Control | What to set | Note |
| --- | --- | --- |
| **Timeouts** | Overall request, connect, idle | A slow backend and a dead one fail differently |
| **Retry** | Max attempts, initial and max backoff, multiplier, retriable codes | Typically 502/503/504. Retrying a 4xx retries a request the backend understood |
| **Circuit breaker** | Consecutive-failure threshold, open duration | Wraps retry. Closed → Open → Half-Open |
| **Rate limiting** | Requests per second, burst size | Token bucket, per surface. Rejects with 429 and `Retry-After` |
| **Traffic mirroring** | Mirror URL, percentage, wait-or-forget, timeout | Adds `X-Mirrored-Request` so the shadow can tell test traffic apart |

## 5. Validation, injection and capture

- **Extension validation** (A2A) — require named extension URIs and mandatory
  fields with expected types. Failures name the missing or malformed fields.
- **Custom metadata injection** — merge a payload object into every outgoing
  request's extension metadata (A2A) or `_meta` (MCP): tenant IDs, feature flags,
  routing hints.
- **Header metadata mapping** — map inbound HTTP headers into message metadata.
  Required alongside the Entra identity source on an A2A proxy.
- **Secrets resolution** — `$secret:…` placeholders resolved at request time, so
  no secret is stored in the surface. Backed by local encrypted storage or AWS
  Secrets Manager.
- **URL rewriting** — agent card URLs are rewritten to point at the gateway, so
  discovery works without the caller knowing the gateway is there.
- **Payload capture** — per surface, four stages: inbound request, outbound
  request (post-transformation), inbound response, outbound response. The fastest
  way to see what the gateway actually sent.

## 6. Observability, for a surface

Every request gets a trace ID, returned as `X-Gateway-Trace-Id` and present in
every log line for it. Quote it with a timestamp when asking an operator for
help.

Connection tracking records timestamp, surface, source, destination, status,
latency, direction, variant alias and identity hash. **Monitoring → Metrics**
presents it as surface → source → caller identity → destination; **Monitoring →
Audit** is the policy-evaluation log, each entry expandable to the full
evaluation context. The dashboard truncates on time and size settings — export to
Prometheus, CloudWatch or an OTEL collector for anything you need later.
