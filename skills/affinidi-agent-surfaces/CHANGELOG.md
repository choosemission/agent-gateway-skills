# Changelog

Each entry records what changed and **which gateway version it was checked
against**. A participant hitting a contradiction can then tell "stale" from
"wrong".

## 1.1.0 — 28 August 2026

Checked against a live gateway on **`agentgateway.affinidi.io`** (A2A surface,
Affinidi's `a2a/` sample from `affinidi-labs-tgw-get-started`). The first
observations from the current host; everything before this was seen on
`train-soap`, now deprovisioned.

**Corrected — agent identity is configured per leg.** The skill described managed
identity as a property configured independently of caller identity, which sent a
reader to the Managed Agent node, where no such setting exists. It is a **second
Identity element, dropped on the managed agent → access point response leg**. The
Managed Agent carries only the *Identity Binding VP* switch. `SKILL.md` gains
this as gotcha 6, with the warning that "outbound" on this gateway means Transit
Points and never the response leg — the canvas invites the other reading.

**Added — the `x-identity` marker.** A payload-extraction schema must mark each
contributing field `"x-identity": true`. A schema that describes the payload but
marks nothing is rejected with a 400 that does not name the marker. The skill had
"mark identity fields" as a UI step without saying what the mark is.

**Added — meta field and nesting.** Declared paths are relative to the meta field,
and the two ends of one exchange commonly nest differently: Affinidi's A2A client
sends `{"agentIdentity": {"name": …}}` while its server sends the fields flat. One
surface, two schemas.

**Added — what each leg puts on the wire**, with the observed shapes: inbound
`…/agent-identity-binding/v1` carrying `identityFields`; the response leg
`…/agent-identity-credential/v1` carrying a **`workloadBinding`** whose
`userIdentity.id` is the DID minted on the inbound leg. Whether the Identity
element alone produces that binding is recorded as unresolved (`CLAIMS.md` B15).

**Added — payload extraction is self-asserted.** The DID is a hash of what the
sender chose to send about itself: a stable pseudonymous identifier the gateway
signs, not proof of who anyone is. mTLS, API key and JWT claim are the modes
anchored in something the caller must possess.

**Troubleshooting** gains four rows: the `x-identity` 400, dotted
`identityFields` keys from a stray meta field, a DID that changes on redeploy
because `version` was marked, and a reply carrying no credential because identity
was configured on the inbound leg only.

**Claims** B12–B15 added; the staleness warning now distinguishes pre-28 Aug
`train-soap` observations from the current host.

## 1.0.0 — 27 August 2026

First release under this name. Reviewed against *Affinidi Trust Fabric — Agent
Gateway Reference Guide* **v0.3.10** (August 2026) and direct guidance from the
Affinidi team.

**Renamed** from `affinidi-trust-surfaces`. Affinidi's term is *Agent Surface*;
"trust surface" was our coinage.

**Corrected, on Affinidi's feedback**

- The appliance is **Agent Gateway**, not Agent Trust Gateway.
- **Removed all mention of HTTP and LLM targets.** The Gateway is
  protocol-enforcing and agent-to-agent; LLM and agent-to-dependency traffic
  belongs to Agent Stream. Now stated as a rule in SKILL.md, repeated as the
  first gotcha, and protected by eval 3.

**Corrected, on reading the reference guide**

- **Transit Points** added — the whole outbound governance model, including the
  transit token, was missing.
- **Inbound/outbound** were described as request/response. They are directions
  of traffic; the response is the MA→AP response leg.
- Added: identity slots, the five managed-identity modes, payload-extraction
  mechanics, workload binding, trust checks and recorder, issuers vs
  authorities, surface variants and `$alias`, the Paywall policy scope, the
  three consent modes.
- Noted that MCP tool policy **denies** unmatched tools without a wildcard, that
  a gateway-level deny is final, and that listener bindings are startup-only.
- Fixed the DID document path to `/.well-known/did.jsonl`.

**Removed**

- Pipes and `/llm/` routes — no such object exists in the current product.
- LLM safety (Prompt Guard / Judge / Jury), AWS Bedrock notes, and gateway
  operations detail. Parked in `docs/agent-gateway-terminology-review.md` in the
  affinidi-lab repo; the LLM-safety material is the seed of a future Agent
  Stream skill.
- The retired-terms table. This is a first release for participants, and a list
  of terms they should not use teaches the wrong vocabulary in order to retire
  it. The mapping lives in the affinidi-lab note instead.

**Structure**

- Split `configuration.md` in two along how each is reached: the governed path
  (~3,500 tokens) and `identity-and-controls.md` (~2,200). The common lookup
  dropped from 5,583 tokens to 3,515.
- Whole skill 118KB → 87KB. SKILL.md is ~3,990 tokens, paid on every trigger.

**Added**

- `CLAIMS.md` and `trigger-queries.md`.

**Known-unresolved** — see `CLAIMS.md` §1. The policy package name, the OPA
input shape, and the delegation callback path each have sources that disagree.
The skill presents the alternatives rather than picking one. Resolving these
with Affinidi would remove real cost from every user.

**Not yet re-verified:** every behavioural observation was made on
`train-soap.trustgateway.affinidi.io`, deprovisioned around 24–25 Aug 2026.
`CLAIMS.md` §3 lists them; `scripts/verify-claims.sh` re-checks what it can.
