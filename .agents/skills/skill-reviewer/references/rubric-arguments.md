# R8 — Parameter System (参数系统)

## Intent

A good skill is a Swiss-army knife, not a hammer. Parameters let users
combine concerns (`--quick`, `--rules`, `--regenerate 3`, `--ref file.png`)
instead of running the whole pipeline every time.

## Concrete questions to ask

- Does the SKILL.md parse `$ARGUMENTS` or document explicit flag parsing?
- For each flag, is it documented in an `## Options` table with name,
  description, default?
- Is there at least one "partial-run" flag (e.g. `--outline-only`,
  `--regenerate <n>`, `--quick`) for users who don't want the full pipeline?
- Is the frontmatter `argument-hint` set so slash-command UI shows the user
  what arguments are available?

## Anti-patterns (instant fail)

- A skill with multiple distinct modes (review / template / fix) but no
  flags to select among them.
- Flags described in prose only, not in a table — easy for the model to
  miss.
- `argument-hint` missing in frontmatter when CLI-style flags are clearly in
  use.

## Severity guide

- **P2** — `argument-hint` is missing while CLI-style flags exist in the
  body.
- **P2** — No partial-run flag in a multi-step pipeline.
- **P3** — Flags exist but aren't tabulated.

## Suggested fix pattern

```yaml
argument-hint: "[<target>] [--quick] [--rules R1,R3] [--template <name>]"
```

```markdown
## Options

| Flag                | Description                                        | Default |
| ------------------- | -------------------------------------------------- | ------- |
| `<target>`          | Path to the skill or `SKILL.md` to review.         | —       |
| `--quick`           | Skip soft rubric review; run only the lint script. | `false` |
| `--rules <ids>`     | Only evaluate the listed rubric IDs (`R1`…`R10`).  | all     |
| `--template <name>` | Generate a new skill scaffold instead of review.   | —       |
```
