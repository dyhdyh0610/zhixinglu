# R4 — Deterministic Operations via Scripts (脚本封装确定性操作)

## Intent

Anything deterministic — file format conversion, lookups in a fixed dataset,
repetitive transformations — should be a script the model calls, not freshly
generated code each turn. Scripts give you reliability, hide bulk from the
context window, and let the model focus on judgment.

## Concrete questions to ask

- Does the skill perform any operation that would benefit from
  reproducibility (file format conversion, lookup, batch processing,
  validation)?
- Are those operations implemented as scripts under `scripts/`, invoked from
  SKILL.md via shell, or are they pseudo-coded inline?
- Are long code blocks (> 30 lines) in SKILL.md candidates for extraction?
- Does the skill document each script's CLI (args, output, exit codes) so the
  model can invoke it without reading the script body?

## Anti-patterns (instant fail)

- The same data table (palettes, frameworks, prompts) duplicated inside
  SKILL.md instead of being a script-backed lookup.
- Long bash/Python embedded in SKILL.md that the model must re-emit every
  run.
- A `scripts/` folder that exists but is never called from SKILL.md.

## Severity guide

- **P2** — Long inline code blocks (> 30 lines) that look reusable.
- **P2** — Deterministic table lookup hard-coded into SKILL.md.
- **P3** — Scripts exist but their CLI is not documented in SKILL.md.

## Suggested fix pattern

```markdown
## Step 2 — Look up the palette

Run:

\`\`\`bash
node .cursor/skills/your-skill/scripts/lookup.mjs palette "<topic>"
\`\`\`

The script returns JSON; use `result.colors` for the final answer.
```
