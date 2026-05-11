# R10 — CLI Tool + Skill = MCP Alternative

## Intent

A CLI tool + a Skill that teaches the model how to use it is often a cheaper
and safer alternative to spinning up an MCP server. The CLI hides
implementation; the skill teaches usage. Context cost drops dramatically.

## Concrete questions to ask

- Does the skill rely on MCP tools or external services that could be
  replaced by a CLI invocation?
- If the skill *is* a CLI wrapper, does it document the CLI surface
  succinctly (a short reference, not a man page)?
- Does it bind the agent's tool access (e.g. `allowed-tools: Bash(my-cli:*)`)
  so the skill can only run its own commands?
- Are CLI examples short, copy-pasteable, and free of cargo-cult flags?

## Anti-patterns (instant fail)

- A skill that re-implements an MCP server's logic inline instead of calling
  out to a stable CLI.
- A skill that documents *all* CLI flags (man-page style) when only 5 are
  used in the workflow.
- `allowed-tools` allowing unrestricted Bash when the skill only needs one
  binary.

## Severity guide

- **P2** — Skill drives a CLI but doesn't pin `allowed-tools` to that CLI.
- **P3** — CLI documentation is verbose when it could be a small table.

## Suggested fix pattern

```yaml
---
name: agent-browser
description: "Browser automation skill via the agent-browser CLI. …"
allowed-tools: "Bash(agent-browser:*)"
---
```

```markdown
## Quick reference

| Command                              | Purpose                |
| ------------------------------------ | ---------------------- |
| `agent-browser open <url>`           | Open a URL             |
| `agent-browser snapshot -i`          | Snapshot interactives  |
| `agent-browser click @<element-id>`  | Click an element       |
| `agent-browser fill @<id> "<text>"`  | Type into an input     |
```
