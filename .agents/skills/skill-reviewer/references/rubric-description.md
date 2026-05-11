# R2 — Description Keyword Density (description 关键词轰炸)

## Intent

`frontmatter.description` is the only field the model sees *before* the skill
is triggered. If it doesn't contain the phrases the user will actually say,
the skill never fires — no matter how good its body is.

## Concrete questions to ask

- Does the description contain at least one explicit "use when …" or "触发"
  phrase listing user-spoken trigger phrases?
- Does it enumerate concrete domain keywords (technologies, actions,
  project types, file extensions)?
- Is the description ≥ 120 characters? Very short descriptions almost always
  under-trigger.
- Does it mix English and Chinese trigger phrasing if the user works
  bilingually?
- Are the trigger phrases in the description **also** removed (or at least not
  duplicated) inside the SKILL.md body? Body content is only loaded after
  triggering, so "When to use this skill" written *only* in the body is dead
  weight.

## Anti-patterns (instant fail)

- Description == name of the skill, nothing more.
- Description is a marketing tagline with no triggers.
- "When to use this skill" lives only in the SKILL.md body, not in the
  description.

## Severity guide

- **P0** — Description missing entirely.
- **P1** — Description present but < 80 chars OR contains no trigger cue.
- **P2** — Description has triggers but misses major synonyms the user
  likely uses.

## Suggested fix pattern

```yaml
description: "Code review specialist. Use when the user says 'review this
PR', 'check this code', '帮我 review', '看看这段代码有没有问题', or
invokes /code-review. Covers SOLID, security (TOCTOU, race conditions,
input validation), code quality, removal plans. Triggers: review, audit,
inspect, pr, code review, security check, refactor."
```
