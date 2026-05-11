# R3 — Workflow Checklist (工作流清单)

## Intent

Models drift. A literal `- [ ]` checklist gives the model a stable scaffold to
tick off as it goes, drastically improving consistency between runs. Critical
steps should carry visible BLOCKING markers.

## Concrete questions to ask

- Does the SKILL.md contain a top-level checklist of the workflow using
  `- [ ]` syntax (not just a numbered list)?
- Are critical / irreversible steps marked with `⚠️ REQUIRED`, `⛔ BLOCKING`,
  or equivalent?
- Are conditional steps labelled `(conditional)` or similar?
- Are sub-steps nested under their parents where complexity warrants it?
- Does the workflow progress from macro → micro (e.g. understand intent →
  high-level structure → details) rather than mixing concerns?

## Anti-patterns (instant fail)

- No explicit step-by-step structure at all.
- Steps that flatten unrelated concerns (e.g. "do security AND naming AND
  performance AND tests at once").
- Critical steps that look identical to optional ones — the model will skip
  them.

## Severity guide

- **P2** — No `- [ ]` checklist OR fewer than 3 checklist items in a
  non-trivial skill.
- **P2** — Critical steps lack any BLOCKING/REQUIRED marker.
- **P3** — Checklist order is illogical (micro before macro).

## Suggested fix pattern

```markdown
## Workflow checklist (copy and tick as you go)

- [ ] Step 0  Preferences check         ⛔ BLOCKING
  - [ ] Found  → load → continue
  - [ ] Missing → run first-time setup
- [ ] Step 1  Analyse content
- [ ] Step 2  Confirm with user         ⚠️ REQUIRED
- [ ] Step 3  Generate
- [ ] Step 4  Pre-delivery checks
```
