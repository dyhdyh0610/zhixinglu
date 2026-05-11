# Report Template

Use this exact structure when delivering the review. Keep it scannable —
verdict and counts first, details second.

````markdown
# Skill Review — `<skill name or path>`

**Verdict:** `GOOD | OK_WITH_NOTES | NEEDS_WORK | BLOCKED`
**Lint:** `<verdict from lint-skill.mjs>`
**Reviewed at:** `<ISO timestamp>`
**Scope:** `<full | R1,R3,R7 | --quick>`

## Counts

| Severity | Count |
| -------- | ----- |
| P0       | `<n>` |
| P1       | `<n>` |
| P2       | `<n>` |
| P3       | `<n>` |

## Findings

### P0 — Must fix

- **[rule-id]** `<one-line summary>`
  - **Evidence:** `<file:line or quoted snippet>`
  - **Why it matters:** `<one sentence>`
  - **Suggested fix:** `<one or two sentences, or a code snippet>`

### P1 — Should fix

- … (same shape)

### P2 — Recommended

- …

### P3 — Polish

- …

## Hard facts (from lint-skill.mjs)

- SKILL.md line count: `<n>`
- references/ files: `<n>` (orphans: `<n>`, broken links: `<n>`)
- scripts/ files: `<n>`
- Checklist items: `<n>`
- Confirmation markers: `<n>`
- Pre-delivery section detected: `<true | false>`

## Fixes applied (if any)

Only present if the user opted into Step 4 fixes.

| File | Change | Related findings |
| ---- | ------ | ---------------- |
| `SKILL.md` | Shortened by N lines; moved palette table to `references/palettes.md` | F3, F4 |

After applying fixes, re-run the lint and include the new verdict here:

```text
Re-lint verdict: <…>
```

## Next steps

- `<one or two specific recommendations the user should action>`
````

## Rules for filling in the template

- The verdict line **must** match the highest severity present. No softening.
- Every finding must cite either a `rule` from the lint output or a rubric
  ID (`R1`–`R10`). Never invent rule IDs.
- "Evidence" must be a real file path + line range, or a verbatim quote.
  Empty/hand-wavy evidence is a P0 against this report itself.
- Prefer one-line summaries; if you need a paragraph, put it under "Why it
  matters".
