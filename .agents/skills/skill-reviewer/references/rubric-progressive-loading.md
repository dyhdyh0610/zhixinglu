# R1 — Progressive Disclosure (渐进式加载)

## Intent

The model's context window is a shared resource. A SKILL.md that dumps every
detail up front starves the rest of the conversation. Detail belongs in
`references/`, loaded only at the step that needs it.

## Concrete questions to ask of the target SKILL.md

- How many lines is SKILL.md? Anything over ~500 means detail should be moved
  out.
- Do any sections contain reference data (tables of options, long
  enumerations, API docs, snippets) that are not needed before a specific
  step?
- For each `references/<file>.md`, is it explicitly loaded from SKILL.md *only
  at the step that needs it*, or is the SKILL.md telling the model to read
  everything up front?
- Are there long fenced code blocks (> 30 lines) embedded in SKILL.md that
  should live as a separate script or reference file?

## Anti-patterns (instant fail)

- A SKILL.md > 1000 lines with all detail inlined.
- "Read every file in `references/` before starting." (defeats the point).
- API tables / configuration matrices duplicated inside SKILL.md when they
  already exist in references.

## Severity guide

- **P1** — SKILL.md > 500 lines, OR reference material is loaded eagerly.
- **P2** — SKILL.md between 350–500 lines, OR inline code blocks > 30 lines.
- **P3** — Style: section ordering puts heavy detail before the workflow.

## Suggested fix pattern

```markdown
## Step 3 — Pick a palette

Load `references/palettes/<chosen>.md` (only the one selected by the user).
```

Instead of:

```markdown
## Palettes

(2,000 lines of inlined palette specs)
```
