# R5 — Concrete Questions vs Vague Directives (该问的问题)

## Intent

Models are great at "answer this specific question" and bad at "ensure
quality". Turn every vague instruction into a concrete question the model can
literally answer against the artefact.

## Concrete questions to ask of the SKILL.md

- For each instruction the SKILL.md gives the model, can it be rephrased as a
  yes/no or count question?
- Are there abstract phrases like "ensure quality", "make sure code is clean",
  "be careful about security" that have no specific check behind them?
- For analysis steps, does the skill prompt the model with the *question*
  (e.g. "How many distinct reasons would this class change for?") rather than
  the *answer* ("Check SRP")?

## Anti-patterns (instant fail)

- "Make sure the code is good." (no operationalisation).
- "Check for SOLID violations." (without telling the model how).
- "Be careful with concurrency." (no concrete probe).

## Severity guide

- **P3** — One or two vague directives in an otherwise specific document.
- **P2** — Most checks are abstract; little of value can be derived.
- **P1** — The entire skill is vague directives — the model has no anchor.

## Translation table

| Vague                              | Concrete                                                                                  |
| ---------------------------------- | ----------------------------------------------------------------------------------------- |
| Check SRP                          | "How many distinct reasons would this module change for?"                                 |
| Watch for race conditions          | "If two requests hit this code simultaneously, what shared state can they corrupt?"       |
| Validate inputs                    | "If `x` is `null` / `0` / `[]` / `""`, what does this function return or throw?"          |
| Avoid TOCTOU                       | "Between the permission check and the action, can the state being checked be mutated?"    |
| Ensure accessibility               | "Does every `<img>` have an `alt`? Does every form input have a `<label for=…>`?"         |
