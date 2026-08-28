# Agent Gateway Skills

> ## ⚠️ Experimental
>
> This skill is derived from Affinidi's own documentation together with hands-on
> developer experience building on the Agent Gateway. It is **under-tested and
> experimental** — but it contains genuinely useful information for navigating
> the Agent Gateway, which is why it is published.
>
> Where sources conflict, the skill presents every candidate rather than guessing.
> Verify specifics against your running gateway, and
> [open an issue](https://github.com/choosemission/agent-gateway-skills/issues)
> if something here is wrong — a corrected claim is the most useful contribution
> this repository can receive.
>
> Not affiliated with, endorsed by, or supported by Affinidi.

Operational knowledge for running agents behind an Affinidi Agent Gateway,
written as an [agent skill](https://skills.sh) — your coding agent loads it when
the task calls for it, instead of you reading it first.

**`affinidi-agent-surfaces`** covers understanding, configuring and debugging an
Agent Surface on an Affinidi Trust Fabric (ATF) Agent Gateway: the surface
object model, the two agent protocols the gateway speaks, source authentication,
agent identity and DIDs, OPA policy, credential delegation, and putting your own
MCP server or A2A agent behind a surface — what credential the gateway injects,
and how to close the ungoverned path to the resource.

It is written to earn its place on the errors you will actually hit —
`No route configured`, a permissive-looking policy that still returns 403,
`consent_required` that looks fatal but is not.

## Install

Works with Claude Code, Codex, Amp, opencode, Gemini CLI, GitHub Copilot and
Kimi CLI:

```bash
npx skills add choosemission/agent-gateway-skills
```

Target particular agents, or install user-wide rather than per-project:

```bash
npx skills add choosemission/agent-gateway-skills --agent claude-code codex
npx skills add choosemission/agent-gateway-skills -g
```

Keep it current with `npx skills update`.

### Try it without installing

```bash
npx skills use choosemission/agent-gateway-skills@affinidi-agent-surfaces | claude
```

### Claude Code plugin

Claude Code users can install as a plugin instead, which puts updates on
`/plugin update`:

```
/plugin marketplace add choosemission/agent-gateway-skills
/plugin install agent-gateway-skills@agent-gateway-skills
```

## How this is written

Gateway behaviour changes, vendor documentation lags, and a claim you cannot
date is a claim you cannot trust. So every falsifiable statement the skill makes
is recorded in [`CLAIMS.md`](./skills/affinidi-agent-surfaces/CLAIMS.md) with its
source and the date it was last checked — including a section of **unresolved
contradictions**, where sources disagree and the skill deliberately presents
every candidate rather than guessing between them.

Read that file before trusting anything here, and prefer the running gateway
over any document, this one included.

Contributions are expected to maintain it — see [CONTRIBUTING.md](./CONTRIBUTING.md).

## Licence

Apache License 2.0 — see [LICENSE](./LICENSE) and [NOTICE](./NOTICE).

Affinidi and Affinidi Trust Fabric are trademarks of their respective owner.
This repository is not affiliated with or endorsed by Affinidi, and the licence
grants no rights in anyone's trademarks.
