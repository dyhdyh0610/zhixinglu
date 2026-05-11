# R7 — Pre-Delivery Checklist (交付前最后一道防线)

## Intent

Before returning to the user, the model should self-verify a list of
*concrete, checkable* statements. This catches the embarrassing class of
errors where the skill claims to have done X but actually didn't.

## Concrete questions to ask

- Does the SKILL.md include a "Pre-Delivery" or equivalent checklist at the
  end of the workflow?
- Are the items in that checklist concrete (verifiable against the artefact)
  rather than aspirational?
- Are there severity categories (P0–P3, or `must` / `should` / `nice`) so the
  model knows what to gate on vs merely report?
- Does the skill *re-run* its scripts where applicable to verify state after
  edits (e.g. lint script re-run after applying fixes)?

## Anti-patterns (instant fail)

- "Make sure everything is good before delivering." (vague, no items).
- A pre-delivery section that just repeats the workflow steps.
- A skill that applies fixes but never re-verifies them.

## Severity guide

- **P3** — Pre-delivery checklist absent in an output-producing skill.
- **P2** — Checklist exists but items are aspirational / not checkable.
- **P1** — Skill modifies state and never re-verifies after edits.

## Suggested fix pattern

```markdown
## Step N — Pre-delivery self-check

- [ ] Every required tool call from earlier steps was actually performed.
- [ ] All findings reference a real rule / file / line range.
- [ ] No file was modified without the user's Step 4 consent.
- [ ] If fixes were applied, the lint script was re-run and the new
      verdict is included in the report.
```
