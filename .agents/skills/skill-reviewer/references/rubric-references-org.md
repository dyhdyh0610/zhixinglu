# R9 — References Organisation (References 分类组织)

## Intent

Once a skill has > 5 reference files, *how* they are organised matters as
much as *what* they contain. Domain-specific organisation lets the model
load only the slice it needs.

## Concrete questions to ask

- Are reference files grouped by *domain* (palettes, renderings, frameworks,
  rubrics) when there are many of them?
- Is each reference file linked from SKILL.md at the step where it should be
  loaded?
- Are there orphan files in `references/` that SKILL.md never mentions?
- Is the directory structure flat (one level under `references/`) for
  simple skills, OR domain-organised (one folder per domain) for complex
  skills? Avoid 3+ levels of nesting.
- For each reference, does SKILL.md make it clear *when* (which step) the
  model should load it?

## Anti-patterns (instant fail)

- Orphan files: present in `references/` but never linked. The model never
  loads them — they are dead weight.
- Broken links: SKILL.md tells the model to load
  `references/foo.md`, but the file doesn't exist.
- A flat directory of 30+ files with no naming convention.

## Severity guide

- **P1** — Broken link (SKILL.md → missing reference file).
- **P2** — Orphan reference files (file exists, never linked).
- **P2** — References nested 2+ levels without an obvious domain reason.
- **P3** — Flat layout when domain grouping would help.

## Suggested fix pattern

```text
references/
├── palettes/        # one file per palette, loaded only when selected
│   ├── warm.md
│   ├── cool.md
│   └── monochrome.md
├── renderings/      # one file per rendering style
│   ├── flat-vector.md
│   └── hand-drawn.md
└── workflow/
    ├── confirm-options.md
    └── prompt-template.md
```

In SKILL.md:

```markdown
After the user picks a palette, load `references/palettes/<chosen>.md`
**and only that file**.
```
