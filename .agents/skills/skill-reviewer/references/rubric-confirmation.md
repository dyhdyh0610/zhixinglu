# R6 — Confirmation Nodes (确认节点)

## Intent

Any skill that *generates*, *modifies*, or *deletes* should pause before the
point of no return and confirm with the user. Autonomous-end-to-end pipelines
fail loudly: if step 3 of 9 was wrong, the user finds out only at step 9.

## Concrete questions to ask

- Does the skill perform any irreversible action (file write, deletion,
  external API call, deployment, commit)?
- For each irreversible action, is there a confirmation step before it,
  using either `AskUserQuestion` or a `⛔ BLOCKING` / `⚠️ REQUIRED` marker?
- Is the confirmation **structured** (a question with options), not a vague
  "let me know if this looks good"?
- Is there a documented escape hatch (e.g. `--quick`, `--yes`) for users who
  want to skip confirmations?

## Anti-patterns (instant fail)

- A skill that writes files end-to-end with no user gate.
- "I will now generate the report" followed by direct edits — no
  confirmation.
- Confirmation phrased as an open question ("anything you want to change?")
  with no enumerated options.

## Severity guide

- **P1** — Skill modifies the user's repo without any confirmation node.
- **P2** — Confirmation exists but is open-ended, not structured.
- **P3** — Confirmation exists, structured, but lacks a `--quick`-style
  escape for repeat users.

## Suggested fix pattern

```markdown
## Step 4 — Confirm scope ⚠️ REQUIRED

Ask the user:

- Apply all suggested fixes
- Apply only P0 and P1
- Apply specific findings (paste IDs)
- Report only — do not modify any file

Do **not** edit any file in the target skill before receiving this answer.
```
