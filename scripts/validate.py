#!/usr/bin/env python3
"""Validate the marketplace manifests and every skill in skills/.

Fails the build on anything that would only surface at install time on a
participant's machine: a manifest pointing at a missing skill, unparseable
frontmatter, a name that does not match its directory, or a missing description.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
errors = []


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        return None
    block, fields, key = match.group(1), {}, None
    for line in block.split("\n"):
        m = re.match(r"^([a-zA-Z_-]+):\s*(.*)$", line)
        if m:
            key = m.group(1)
            fields[key] = m.group(2).strip()
        elif key and line.strip():
            fields[key] = (fields[key] + " " + line.strip()).strip()
    return fields


skill_dirs = sorted(p for p in (ROOT / "skills").iterdir() if p.is_dir())
if not skill_dirs:
    errors.append("skills/ contains no skill directories")

for d in skill_dirs:
    sk = d / "SKILL.md"
    if not sk.exists():
        errors.append(f"{d.name}: no SKILL.md")
        continue
    fm = frontmatter(sk)
    if fm is None:
        errors.append(f"{d.name}: SKILL.md has no YAML frontmatter")
        continue
    name = fm.get("name", "").strip()
    if name != d.name:
        errors.append(f"{d.name}: frontmatter name {name!r} does not match directory")
    desc = fm.get("description", "").lstrip(">-").strip()
    if not desc:
        errors.append(f"{d.name}: frontmatter has no description")
    elif len(desc) < 40:
        errors.append(f"{d.name}: description is too short to trigger reliably")

    for ref in re.findall(r"\]\((\./[^)\s]+|references/[^)\s]+|scripts/[^)\s]+)\)", sk.read_text()):
        target = (d / ref.lstrip("./")).resolve()
        if not target.exists():
            errors.append(f"{d.name}: SKILL.md links to missing {ref}")

plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())

for entry in plugin.get("skills", []):
    if not (ROOT / entry.lstrip("./")).is_dir():
        errors.append(f"plugin.json lists missing skill path {entry}")

listed = {pathlib.Path(e).name for e in plugin.get("skills", [])}
present = {d.name for d in skill_dirs}
for missing in present - listed:
    errors.append(f"skills/{missing} exists but is not listed in plugin.json")

names = {p["name"] for p in market.get("plugins", [])}
if plugin["name"] not in names:
    errors.append(f"plugin.json name {plugin['name']!r} is not offered by marketplace.json")
if plugin["version"] != market["plugins"][0]["version"]:
    errors.append("plugin.json and marketplace.json versions disagree")

for e in errors:
    print(f"FAIL  {e}", file=sys.stderr)
print(f"\nChecked {len(skill_dirs)} skills — {len(errors)} problem(s).")
sys.exit(1 if errors else 0)
