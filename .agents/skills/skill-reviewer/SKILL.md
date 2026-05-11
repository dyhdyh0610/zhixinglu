---
name: skill-reviewer
description: "Skill 质量审查与规范脚手架。审查 Claude/Cursor Agent Skill 是否符合高质量规范（渐进式加载、description 关键词、工作流 checklist、确认节点、脚本封装、参数系统、references 组织、Pre-Delivery、CLI+Skill 模式、反 Slop），并按 P0–P3 分级输出报告；也能 --template 生成符合规范的 Skill 骨架。Use when the user says 'review this skill' / 'audit my skill' / 'lint SKILL.md' / 'check skill quality' / 'skill scaffold' / 'skill template' / '帮我检查 skill' / '审查 skill' / '看看这个 skill 写得怎么样' / '生成 skill 模板' / '这个 skill 是不是 slop'. Trigger keywords: review skill, audit skill, check skill, lint skill, skill rubric, skill quality, SKILL.md, progressive disclosure, slop, skill template, skill scaffold, anti-slop."
argument-hint: "[<path-to-skill-or-SKILL.md>] [--quick] [--rules id1,id2] [--template <name>] [--json]"
allowed-tools: "Read, Write, StrReplace, Glob, Grep, ReadLints, Shell(node:*), AskQuestion"
---

# skill-reviewer

A Skill that reviews other Agent Skills against a 10-rule rubric, distilled from
the article *"高质量 Skill 的十个套路"*. It can also scaffold a new Skill that
respects the rubric from day one.

Two operating modes:

| Mode | Trigger | Output |
| ---- | ------- | ------ |
| **Review** | path is supplied, no `--template` | P0–P3 report (and optional fix plan) |
| **Template** | `--template <name>` | New skill folder under `.cursor/skills/<name>/` |

The rubric files live in `references/`. **Do not load them all up front.** Load
each one only when you reach the step that needs it — that is rule #1 of the
rubric, and this skill must walk the talk.

---

## Argument parsing

Parse `$ARGUMENTS` (if provided by a slash command) or the user's free-text
request into:

- `target` — absolute or workspace path to a skill directory or to a
  `SKILL.md` file. Required in review mode.
- `--quick` — skip soft rubric review, run only the lint script.
- `--rules <ids>` — comma-separated rubric IDs to focus on
  (`R1` … `R10`, see *Rubric index* below).
- `--template <name>` — switch to template mode and create
  `.cursor/skills/<name>/`.
- `--json` — emit machine-readable report instead of prose.

If the user invoked you without a clear path, ask them first (see Step 0).

---

## Workflow checklist (copy and tick as you go)

```text
Review mode:
- [ ] Step 0  Confirm mode & target           ⚠️ REQUIRED
- [ ] Step 1  Run lint-skill.mjs              (hard facts)
- [ ] Step 2  Soft review per rubric          (per-step reference load)
- [ ] Step 3  Aggregate findings by P0–P3
- [ ] Step 4  Ask user how to proceed         ⚠️ REQUIRED
- [ ] Step 5  Deliver report / apply fixes
- [ ] Step 6  Pre-delivery self-check

Template mode:
- [ ] Step T0 Gather skill intent             ⚠️ REQUIRED
- [ ] Step T1 Generate scaffold from template-skeleton.md
- [ ] Step T2 Run lint on the new scaffold    (self-verify)
- [ ] Step T3 Report scaffold + lint result
```

---

## Step 0 — Confirm mode & target ⚠️ REQUIRED

Before running anything, confirm with the user using `AskQuestion`:

1. **Mode**: Review existing skill / Generate new skill template / Both
   (review then patch).
2. **Target path** (review only): absolute path or workspace-relative path.
   Accept either a skill directory or a `SKILL.md` file.
3. **Scope** (review only): full rubric or only specific rule IDs.

Skip this step **only** if `--quick` is set *and* `target` was supplied
explicitly — in that case proceed directly to Step 1.

---

## Step 1 — Run the hard-fact lint

Use the Shell tool to run the bundled linter. It is zero-dependency Node:

```bash
node .cursor/skills/skill-reviewer/scripts/lint-skill.mjs <target> --json
```

The script returns JSON with:

- `summary.counts` — P0/P1/P2/P3 counts.
- `summary.verdict` — `BLOCKED | NEEDS_WORK | OK_WITH_NOTES | GOOD`.
- `facts` — line count, frontmatter, references files, orphan refs, etc.
- `findings` — every hard-rule violation with `id`, `severity`, `rule`,
  `message`, optional `evidence`.

Treat every finding from the script as **authoritative** — do not soften or
re-rank them. The script is the deterministic floor; the rubric review on top
only **adds** findings.

If `--quick` is set, skip Step 2 and jump to Step 3.

---

## Step 2 — Soft review per rubric (load on demand)

For each rule the user did not exclude via `--rules`, perform this loop:

1. **Load only that one rubric file** from `references/`.
2. Re-read the relevant slice of the target skill in light of that rubric.
3. Append findings to the running list. Use the same `{severity, rule,
   message, evidence}` shape as the lint script.

Rubric index — load **only when you reach the corresponding step**:

| ID  | File                                    | Focus                                    |
| --- | --------------------------------------- | ---------------------------------------- |
| R1  | `references/rubric-progressive-loading.md` | Progressive Disclosure / file size    |
| R2  | `references/rubric-description.md`      | description keyword density & triggers   |
| R3  | `references/rubric-workflow-checklist.md` | Workflow checklist quality             |
| R4  | `references/rubric-scripts-pattern.md`  | Determinism via scripts/                 |
| R5  | `references/rubric-good-questions.md`   | Concrete questions vs vague directives   |
| R6  | `references/rubric-confirmation.md`     | Confirmation / BLOCKING nodes            |
| R7  | `references/rubric-pre-delivery.md`     | Pre-delivery quality gate                |
| R8  | `references/rubric-arguments.md`        | Parameter system & composability         |
| R9  | `references/rubric-references-org.md`   | references/ organisation                 |
| R10 | `references/rubric-cli-pattern.md`      | CLI + Skill replacing MCP                |

Stay disciplined: **never** read a rubric you are not currently evaluating.

---

## Step 3 — Aggregate findings

Merge `findings[]` from the lint script with the soft-review findings. Sort by
severity then by rule id. Compute totals per severity.

Severity definitions live in `references/severity-levels.md` — load that file
**once** here.

---

## Step 4 — Ask the user how to proceed ⚠️ REQUIRED

Use `AskQuestion` with options:

- Fix everything (P0 + P1 + P2 + P3).
- Fix only P0 and P1.
- Fix specific findings (let the user paste IDs).
- Report only — do not modify any file.

Never edit files in the target skill before getting this confirmation. This
mirrors the article's principle: *don't let the model take action you didn't
sign off on*.

---

## Step 5 — Deliver report / apply fixes

Use the format from `references/report-template.md` (load it here). The report
must contain, in order:

1. Verdict line (`GOOD | OK_WITH_NOTES | NEEDS_WORK | BLOCKED`).
2. Counts table.
3. Findings, grouped by severity, each with `[rule-id] message → evidence →
   suggested fix`.
4. If the user opted in to fixes: a list of files you modified plus a brief
   diff summary.

When applying fixes:

- Use the `StrReplace` tool, not free-form rewrites.
- Re-run the lint script after edits and include the new verdict in the report.
- Never delete files the user wrote without confirmation.

---

## Step 6 — Pre-delivery self-check

Before returning the report, verify each item below. Fail any of them → fix
before responding.

- [ ] Lint script was actually executed and its JSON output was consumed.
- [ ] Every rubric ID the user asked for was loaded **exactly once**.
- [ ] No rubric file was loaded that the user excluded with `--rules`.
- [ ] All findings reference a real `rule` (matches a lint `rule` or a `R1–R10`
      ID).
- [ ] Verdict matches the highest severity present.
- [ ] No file in the target skill was modified without the user's explicit
      consent in Step 4.

---

## Template mode (Step T0 – T3)

### Step T0 — Gather intent ⚠️ REQUIRED

Ask the user:

- Skill `name` (kebab-case).
- One-sentence purpose.
- 5–10 trigger phrases users would actually say.
- Will it run scripts? generate output? need confirmation nodes?

### Step T1 — Generate scaffold

Load `references/template-skeleton.md`. Create:

```
.cursor/skills/<name>/
├── SKILL.md
├── scripts/.gitkeep       # only if user said yes to scripts
└── references/
    └── .gitkeep
```

Apply each rubric while writing the scaffold:

- R1: keep SKILL.md < 250 lines, push detail into references.
- R2: pack the description with the user's trigger phrases.
- R3: include a workflow checklist with at least one `⚠️ REQUIRED` step.
- R6: add a confirmation step before any irreversible action.
- R7: include a pre-delivery checklist.
- R8: parse `$ARGUMENTS`, document each flag, set `argument-hint`.

### Step T2 — Self-verify

Run the lint script against the new scaffold. The verdict **must** be `GOOD`
or `OK_WITH_NOTES`. If not, patch the scaffold until it is.

### Step T3 — Report

Tell the user where the scaffold lives, what to fill in next, and what the
linter said.

---

## Anti-Slop reminders (do not skip)

- This skill must respect every rule it enforces. If you change `SKILL.md`
  here, re-run the linter on this folder.
- Prefer asking the user a concrete question over guessing the intent.
- Never invent rubric IDs. The set is fixed: `R1–R10` plus the hard rules
  emitted by `lint-skill.mjs`.
- Cite findings with their `rule` field so the user can trace them back to
  either the script (`scripts/lint-skill.mjs`) or a rubric file under
  `references/`.
