# Contributing

## The provenance rule

Every behavioural claim about a gateway, a console or an identity provider must
say where it came from. Gateway behaviour changes, vendor documentation lags,
and a claim you cannot date is a claim the next reader cannot trust.

[`skills/affinidi-agent-surfaces/CLAIMS.md`](./skills/affinidi-agent-surfaces/CLAIMS.md)
implements this rule and is the model to copy: every falsifiable statement in
the skill, with a provenance code, a source, and a date last checked. Any skill
added here that makes behavioural claims must carry one.

Mark each claim as one of:

- **Observed** — seen working, with the date and the system it was seen on.
  *"Observed on one hosted gateway, July 2026."*
- **Inferred** — reasoned from documentation or from adjacent behaviour, not
  witnessed. Say so in the sentence, not in a footnote.
- **Vendor guidance** — stated by the vendor, with the date you were told.

Where this repository and a vendor's documentation disagree, say so at that
point in the text and tell the reader to prefer the running system.

Claims with a shelf life — a live defect, a console layout, a product gap —
carry an explicit date so a reader can judge whether they have expired. Prefer
"as of August 2026, X" to a bare "X".

## Screenshots

Screenshots date faster than anything else here, and every install of this
repository downloads them. Before committing one:

- Resize to at most 1400px wide and save as JPEG at quality ~82. CI rejects
  anything in `skills/` over 300K.
- **Look at it.** Console screenshots leak hostnames, tenant identifiers,
  account names and tokens that a text search over the repository will never
  find. Crop or redact before committing.

## Before opening a pull request

```bash
python3 scripts/validate.py
```

If the skill carries a `CLAIMS.md`, update it in the same pull request as the
claim it covers, and move the **Last full review** date only when you have
actually re-checked the rows.

This checks that frontmatter parses, that each skill's `name` matches its
directory, that descriptions are substantial enough to trigger reliably, that
`SKILL.md` links resolve, and that the manifests and `skills/` agree.

## Writing a skill description

The `description` is the only part loaded into an agent's context at all times;
it is what decides whether the skill triggers. Write it for matching, not for
elegance: name the errors, the product terms, the file types and the phrasings
someone would actually use. `affinidi-agent-surfaces` is worth reading as an
example: it names products, error strings and hostnames a caller would type.

## Licensing of contributions

This repository is licensed under Apache 2.0. Under section 5 of that licence,
any contribution you deliberately submit for inclusion is licensed on the same
terms, with no separate agreement needed. Do not contribute material you are not
free to license this way — in particular vendor documentation, support-ticket
text, or screenshots containing another party's confidential information.
