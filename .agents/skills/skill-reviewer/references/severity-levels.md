# Severity Levels

Every finding (from the lint script or from a rubric review) carries one of
four severities. Use this file to decide ranking and to set the report
verdict.

| Level | Meaning                                                                                  | Action                                                                       |
| ----- | ---------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| P0    | The skill is broken or unsafe to ship. The model will misbehave or the skill won't load. | Must fix. Verdict → `BLOCKED`. Do not publish.                               |
| P1    | High risk of bad output, missed triggers, or context bloat. Will visibly hurt UX.        | Should fix before publishing. Verdict → at worst `NEEDS_WORK`.               |
| P2    | Clear improvement opportunity. Output quality / maintainability suffers without it.      | Recommend. Verdict → at worst `OK_WITH_NOTES`.                               |
| P3    | Style or small polish. No functional impact.                                             | Optional. Doesn't change the verdict.                                        |

## Verdict mapping

```text
P0 > 0           → BLOCKED
P0 == 0 && P1>0  → NEEDS_WORK
P0+P1 == 0 && P2>0 → OK_WITH_NOTES
P0+P1+P2 == 0    → GOOD   (P3 may still be present)
```

## Boundaries between levels

- **P0 vs P1** — P0 means the skill literally cannot perform its claimed
  function (no frontmatter, no description, broken cross-link to a file the
  workflow needs). P1 means the function will fire but produce noticeably
  worse output (description too short, SKILL.md too long, no confirmation
  before mutating files).
- **P1 vs P2** — P1 will *bite the user*. P2 might be invisible to the user
  but will hurt long-term maintenance or the next model upgrade.
- **P2 vs P3** — P2 is something you would mention in a code review. P3 is
  bikeshed-grade.

## Tie-breaking

If a finding could plausibly sit at two levels, prefer the **lower** severity
unless the finding is about *user-visible* behaviour (then prefer the higher
severity). Skill quality reviews should err on the side of "be specific about
what hurts the user".
