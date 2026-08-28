# Trigger queries

What this skill is for, and what it isn't — written as questions.

Not a test suite. When you change the `description` in SKILL.md's frontmatter,
paste two or three of these into a normal Claude Code session (from a directory
where the skill is installed) and see whether it loads. That is the whole check.

## Should reach for this skill

- My ATF surface returns 403 for every caller even though the Rego looks permissive. Where do I start?
- I've got an MCP server running on a tunnel and I need to put it behind the Affinidi gateway so callers can't reach it directly.
- Walk me through setting up credential delegation so the agent never sees the user's GitHub token.
- What's the difference between an access point and a transit point?
- The gateway is returning 502 builder error for url proxy://something when I curl the route. Is it broken?
- I need agent A in our org to call agent B in a partner org, with identity that survives the boundary. How do I wire that up?
- Every user seems to be sharing the same upstream credential through the gateway. What did I misconfigure?
- How do I expose our legacy REST API to agents as MCP tools without writing any code?
- I want to change the rate limit on a surface that's serving production traffic without breaking it.
- Can you help me route agent traffic to Claude through the Affinidi gateway?

## Should not — these are the near-misses

Each shares vocabulary with the skill but belongs somewhere else: Agent Stream,
generic MCP or OAuth work, or infrastructure that merely sits next to a gateway.

- How do I configure content moderation and jailbreak detection on Agent Stream?
- Set up an MCP server in my Claude Code config so I can call it locally over stdio.
- My MCP server needs OAuth so users sign in with Keycloak instead of pasting an API key.
- What's the right Rego package name for an OPA sidecar in front of our Kubernetes ingress?
- Add a new client and redirect URI to the mission-agent-lab realm in Keycloak.
- Write me an A2A agent card for a service I'm building.
- We're comparing API gateways for our agent platform — Kong versus Apigee versus building our own. Thoughts?
- Explain how did:webvh differs from did:web and when I'd pick each.
- Our x402 payment settlement is failing on-chain. Can you debug the transaction?
- Add a new recipe to the lab catalog and make sure validation passes.
