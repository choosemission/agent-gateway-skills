# affinidi-agent-surfaces

A Claude skill for configuring and debugging **Agent Surfaces** on an Affinidi
Trust Fabric **Agent Gateway** — the object model, the two agent protocols the
gateway speaks, source authentication, agent identity and DIDs, OPA policy,
credential delegation, and how to put your own MCP server or A2A agent behind a
surface without leaving an ungoverned path to it.

Built and maintained by [MISSION](https://choosemission.com) for the
Enterprise-Builder Lab. Neutral ground: it documents observed behaviour, and
says so wherever a claim came from a running gateway rather than the vendor's
guide.

## Install

Extract the archive into your skills directory:

```bash
unzip affinidi-agent-surfaces.zip -d ~/.claude/skills/
```

Or, in a project, into `.claude/skills/`. Claude picks it up on the next
session; you do not need to invoke it by name.

## What is in the box

```
SKILL.md                        the entry point — loaded whenever the skill fires
references/
  configuration.md              the governed path: targets, source auth, policy,
                                the target credential, credential delegation
  identity-and-controls.md      what you add to a working surface: agent identity,
                                transit points, variants, traffic, capture
  dashboard.md                  the console: navigation, canvas, build order
  troubleshooting.md            response-to-cause table
  securing-the-resource.md      closing the ungoverned path
  patterns.md                   worked end-to-end examples
  glossary.md                   one-line definitions, and which ATF appliance owns what
```

Only `SKILL.md` loads automatically. The references are read on demand, so a
lookup costs one file, not the set.

## Development

```
CLAIMS.md            every factual claim, where it came from, when last checked
trigger-queries.md   what the skill is for and what it isn't, as questions
CHANGELOG.md         what changed, and against which gateway version
```

`CLAIMS.md` is the one that matters. It marks each claim **G** (Affinidi's
reference guide), **O** (observed on a running gateway, with a date) or **A**
(told to us directly). The O rows are field experience; the G rows are a summary
of a document participants can read themselves. Knowing which is which is what
tells you how far to trust any given line.

Validation is the pilot cohort, not a test suite. If the skill does not fire, or
fires and misleads, that shows up in what participants ask — faster and cheaper
than simulating it.

To build the archive participants install:

```bash
cd .. && zip -r affinidi-agent-surfaces.zip \
  affinidi-agent-surfaces/{SKILL.md,CHANGELOG.md,references} -x '*/.*'
```

## Contributing

Corrections from the field are the point. If the gateway does something this
skill says it does not, open an issue with the trace ID
(`X-Gateway-Trace-Id`), the gateway version and the date — that is enough to fix
the claim and date it properly.

Three things in `CLAIMS.md` §1 are unresolved because Affinidi's own
documentation disagrees with itself: the policy package name, the OPA input
shape, and the delegation callback path. The skill presents the alternatives
rather than picking one. If you can settle any of them against a live gateway,
that is the highest-value contribution available.
