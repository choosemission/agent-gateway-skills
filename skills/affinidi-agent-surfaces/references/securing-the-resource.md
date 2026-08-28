# Securing the resource behind a surface

`SKILL.md` makes the claim: a surface is a second door, and your governance is as
real as the lock on the first one. This file is how to fit the lock.

The failure it prevents produces **no error**. Everything works through the
governed path while the ungoverned path sits open beside it, so nothing in your
logs, policy evaluations or audit trail will tell you. You have to go looking.

**The threat model, in one line:** anyone who can reach the resource URL gets
everything the surface was protecting, without appearing in any of its records.

The common case is not an attacker. It is a user who noticed the real URL in an
error message or a config file, or your own client code six months later, pointed
at the direct URL by someone who found it simpler and did not know the surface
was load-bearing. Governance that is optional gets skipped by well-meaning people
long before it gets attacked.

## Closing the direct path

In rough order of strength. Pick the weakest one that actually holds, then verify
it — an unverified control is not a control.

**1. Shared secret in a header (the standard path).** The resource requires
`Authorization: Bearer …` or `x-api-key: …` and rejects anything without it. The
gateway holds that secret and injects it, so callers on the governed path never
see it. This is what the target-credential binding is built for, and for most
targets it is the right answer. It is a bearer secret: possession is
authorisation, it does not expire on its own, and anywhere it leaks is a full
bypass.

Make the rejection **unconditional and early** — before routing, before per-tool
logic, before anything with its own exemptions. The common defect is a check that
runs on `/mcp` but not on a health endpoint that turns out to be just as useful.

**2. Network allowlist.** The resource accepts connections only from the
gateway's egress addresses. Stronger — a leaked secret alone no longer buys
access — but it needs a stable egress range from whoever operates the gateway. It
composes with (1) rather than replacing it. Development tunnels usually make it
impossible: the provider terminates the connection, so the origin sees the tunnel
rather than the gateway. On a tunnel you are relying on (1) whether or not you
meant to.

**3. mTLS.** Strongest, highest friction. Whether the gateway's outbound leg can
present a client certificate is a question for Affinidi rather than an
assumption.

## Handing the credential to the gateway

Steps are in `configuration.md` §4. Two things worth repeating:

**The key is one you invent.** Nothing issues it, and there is no step where the
gateway generates one. You mint a random string and install it in two places: the
resource, which requires it, and the gateway, which sends it.

**Two things must match, not one** — the header name the resource reads, and the
secret value it expects. Either mismatch produces the identical symptom: the
resource's own 401 arriving through a surface that is otherwise working
perfectly. That reads like the gateway is not injecting, and sends people
inspecting gateway configuration instead of comparing two strings.

Confirm injection is live by calling the **access point** URL with no credential
of your own and expecting a `200`. That single result proves both halves — the
gateway is injecting, and you did not need to hold the secret.

## Rotation

One value deliberately duplicated across two systems is exactly the shape of
thing that drifts, so sequence the change:

1. Resource accepts **both** old and new.
2. Update the gateway's secret to the new one.
3. Verify through the surface.
4. Resource drops the old one.
5. Verify the direct path still returns 401.

Step 5 is not paranoia. Rotation is the most likely moment for the chokepoint to
quietly disappear, because it is the only routine operation that touches the
enforcement code — and an over-enthusiastic cleanup at step 4 sometimes removes
the check rather than the key.

## Dual-leg targets — the deliberate second door

Sometimes you *want* a resource reachable both ways: through the gateway, and
directly by a client that authenticates for itself. That is not a bypass provided
both doors are locked, and it is the practical arrangement today where a client
must complete OAuth against the resource by itself.

| | Gateway leg | Direct leg |
| --- | --- | --- |
| Credential | API key, injected by the gateway | The caller's own IdP token |
| What is proven | That the caller **is the gateway** | **Who the caller is** |
| Identity established | Before the request arrives | Here |
| Policy enforced by | The surface's policy | The resource itself |

On the direct leg the resource is a full OAuth 2.1 resource server: RFC 9728
protected-resource metadata, a `WWW-Authenticate: Bearer resource_metadata="…"`
challenge, JWT verified against the issuer's JWKS. Clients discover the IdP,
register dynamically, run authorization code with PKCE, and retry. (Built and
verified end to end for the Lab's catalog server — `docs/catalog-mcp.md`.)

The teaching value is real: the same client, re-pointed from one URL to the
other, gets the same tools with a policy decision and an injected credential in
front of them. The governed path is indistinguishable from the agent's side.

What makes it two locked doors rather than one is that **neither leg falls back
to open**. A request with no credential fails on both. If the direct leg treats a
missing token as anonymous-but-allowed, you have rebuilt the bypass with extra
steps.

## What the resource can and cannot trust from the gateway

The gateway forwards caller telemetry:

```
x-caller-did: anonymous
x-caller-identity-source: gateway-computed
```

The injected credential proves the request **came from the gateway**. It proves
nothing about which human is behind it. So:

- **Trust** that you are on the governed path — the key established that.
- **Treat `x-caller-did` as telemetry**: log it, attribute with it, do not gate on
  it. Re-verifying caller identity means two systems enforcing one rule in two
  places, and they will drift.
- **Log `anonymous` distinctly.** It means the surface has no caller context
  configured, not that a user named "anonymous" called.

The distinction, easy to blur: *do not re-verify who the caller is; do verify
that the caller is the gateway.* Only the second is the resource's job, and only
the second closes the bypass.

## Verification checklist

Run after standing a target up, and after any redeploy, tunnel restart or secret
rotation.

```bash
# 1. Direct path is closed — the one that matters most.
curl -s -o /dev/null -w 'direct:  %{http_code}\n' "$RESOURCE_URL"
#    want 401/403. A 200 means the surface is not a chokepoint.

# 2. Direct path with a wrong key is still closed.
curl -s -o /dev/null -w 'badkey:  %{http_code}\n' \
  -H "x-api-key: definitely-not-the-key" "$RESOURCE_URL"

# 3. Governed path works with no credential of your own —
#    proves the gateway is injecting.
curl -s -X POST "$ACCESS_POINT_URL" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"probe","version":"1"}}}' \
  | sed 's/^data: //'

# 4. Enumerate what else the origin exposes — enforcement is per-route,
#    and health/metrics/docs endpoints are the usual leak.
for p in / health healthz metrics docs openapi.json .well-known/oauth-protected-resource; do
  printf '%-40s %s\n' "/$p" "$(curl -s -o /dev/null -w '%{http_code}' "$RESOURCE_ORIGIN/$p")"
done
```

Check 4 is the one people skip. Enforcement usually gets applied to the MCP route
and forgotten on everything else the framework mounted.

## Failure modes

| Symptom | Cause | Fix |
| --- | --- | --- |
| The target's own URL returns `200` with no credential | No enforcement, or enforcement on some routes only | Reject unconditionally, before routing. Re-run check 4. |
| The resource's own `401` when called **through** the surface | The gateway is not injecting; or the header name is wrong; or the stored secret is not the value expected | Check the target credential binding — `configuration.md` §4. Compare **both** header name and secret value; either alone produces this. |
| Works through the surface, `401` direct — but only because the resource is down | You are reading a failure as a control | Confirm the resource is up and the `401` is the auth path, not a generic error. |
| Bypass reappears after a deploy | Enforcement lives in configuration the deploy resets, or the tunnel hostname changed | Move enforcement into code, not environment. Add check 1 to the deploy. |
| Two users appear to share one upstream credential | Static injection is per-target, not per-user, by design | If you need per-user, that is three-legged delegation — `configuration.md` §5. |
| Everything works, nothing appears in the audit trail | Callers are using the direct URL | The audit gap *is* the signal. Check 1. |

That last row is worth internalising. An audit trail quieter than your traffic is
not a logging problem.
