# Template Skeleton

When template mode is requested, generate a new skill that already passes
the rubric. Use the structure below as the starting point and adapt it to the
user's intent gathered in Step T0.

## Directory layout

```text
.cursor/skills/<name>/
├── SKILL.md                       # the body below
├── scripts/                       # create only if user said yes to scripts
│   └── .gitkeep
└── references/
    ├── workflow.md                # optional: long workflow details
    └── .gitkeep
```

## `SKILL.md` body

```markdown
---
name: <name>
description: "<one-sentence purpose>. Use when the user says
'<trigger 1>', '<trigger 2>', '<trigger 3>', '<chinese trigger 1>',
'<chinese trigger 2>', or invokes /<name>. Covers <domain keyword 1>,
<domain keyword 2>, <domain keyword 3>. Triggers: <kw1>, <kw2>, <kw3>."
argument-hint: "[<positional>] [--quick] [--<flag> <value>]"
allowed-tools: "<scope, e.g. Bash(<name>:*), Read, Write, AskQuestion>"
---

# <name>

<2–3 line description of what this skill does and what it explicitly does
*not* do.>

## Workflow checklist (copy and tick as you go)

- [ ] Step 0  Confirm scope with user             ⚠️ REQUIRED
- [ ] Step 1  <first concrete step>
- [ ] Step 2  <second step>
- [ ] Step 3  Confirm before applying changes     ⚠️ REQUIRED
- [ ] Step 4  Apply / generate
- [ ] Step 5  Pre-delivery self-check

## Step 0 — Confirm scope ⚠️ REQUIRED

Ask the user (via `AskQuestion`):

- <structured question 1 with enumerated options>
- <structured question 2>

Do **not** proceed without an explicit answer unless `--quick` is set.

## Step 1 — <first concrete step>

Ask yourself:

- <a concrete, answerable question — not a vague directive>
- <another concrete question>

If detail is needed, load `references/<topic>.md` here — and only here.

## Step 2 — <second step>

…

## Step 3 — Confirm before applying changes ⚠️ REQUIRED

Use `AskQuestion` with options:

- Apply all proposed changes
- Apply a subset (list IDs)
- Report only — do not modify any file

## Step 4 — Apply / generate

- Use `StrReplace` for surgical edits.
- For deterministic operations, call `scripts/<your-script>.mjs`.

## Step 5 — Pre-delivery self-check

- [ ] Every required tool call was actually executed.
- [ ] No file was modified without the user's Step 3 consent.
- [ ] All findings / outputs cite a real file path or rule ID.
- [ ] If applicable, the verification script was re-run after edits.

## Options

| Flag             | Description                              | Default |
| ---------------- | ---------------------------------------- | ------- |
| `<positional>`   | <what the positional arg means>          | —       |
| `--quick`        | Skip confirmations.                      | `false` |
| `--<flag>`       | <what this flag does>                    | —       |
```

## Customisation rules for the generator

- If the user said the skill performs **deterministic operations**, create
  `scripts/` and add at least a stub Node ESM script. Document its CLI in
  the SKILL.md.
- If the skill is purely advisory (no file writes), the Step 3 confirmation
  can be a single "Report only — proceed?" question, but it should still be
  `⚠️ REQUIRED`.
- Initial SKILL.md length budget: **≤ 250 lines**. Anything heavier goes into
  `references/`.
- Include at least three trigger phrases in the description in each language
  the user works in (English / Chinese).
- After generating the scaffold, run `node lint-skill.mjs <new-skill-dir>` and
  iterate until the verdict is `GOOD` or `OK_WITH_NOTES`.
