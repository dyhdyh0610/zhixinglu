
import { readFileSync, readdirSync, statSync, existsSync } from "node:fs";
import { join, resolve, relative, basename, extname } from "node:path";

const args = process.argv.slice(2);
const opts = {
  target: null,
  json: true,
  quiet: false,
};
for (const arg of args) {
  if (arg === "--json") opts.json = true;
  else if (arg === "--quiet") opts.quiet = true;
  else if (!opts.target) opts.target = arg;
}

if (!opts.target) {
  console.error(
    "Usage: node lint-skill.mjs <path-to-skill-dir-or-SKILL.md> [--json] [--quiet]"
  );
  process.exit(2);
}

const targetPath = resolve(opts.target);
const skillDir = statSync(targetPath).isDirectory()
  ? targetPath
  : resolve(targetPath, "..");
const skillMdPath = statSync(targetPath).isDirectory()
  ? join(targetPath, "SKILL.md")
  : targetPath;

const findings = [];
let nextId = 1;
const addFinding = (severity, rule, message, evidence = null) =>
  findings.push({ id: `F${nextId++}`, severity, rule, message, evidence });

// ---------------------------------------------------------------------------
// 1. SKILL.md must exist
// ---------------------------------------------------------------------------
if (!existsSync(skillMdPath)) {
  addFinding(
    "P0",
    "skill-md-missing",
    "SKILL.md not found at the expected path.",
    { expected: skillMdPath }
  );
  emit({ targetPath, skillDir, skillMdPath }, findings, opts);
  process.exit(0);
}

const raw = readFileSync(skillMdPath, "utf8");
const lines = raw.split(/\r?\n/);
const lineCount = lines.length;

// ---------------------------------------------------------------------------
// 2. Frontmatter parsing (lightweight YAML — no dependency)
// ---------------------------------------------------------------------------
const frontmatter = {};
let frontmatterEndLine = 0;
let hasFrontmatter = false;
if (lines[0]?.trim() === "---") {
  hasFrontmatter = true;
  for (let i = 1; i < lines.length; i++) {
    if (lines[i].trim() === "---") {
      frontmatterEndLine = i;
      break;
    }
    const m = lines[i].match(/^([A-Za-z0-9_-]+)\s*:\s*(.*)$/);
    if (m) frontmatter[m[1]] = m[2].trim().replace(/^["']|["']$/g, "");
  }
}

if (!hasFrontmatter) {
  addFinding(
    "P0",
    "frontmatter-missing",
    "SKILL.md must start with a YAML frontmatter block delimited by '---'."
  );
}

// description checks
const description = frontmatter.description || "";
if (!description) {
  addFinding(
    "P0",
    "description-missing",
    "frontmatter.description is required — it controls when the model auto-triggers this skill."
  );
} else {
  if (description.length < 80) {
    addFinding(
      "P1",
      "description-too-short",
      `description is only ${description.length} chars — pack more trigger keywords (target >= 120 chars).`,
      { description }
    );
  }
  // trigger-intent hints: descriptions of good skills usually say "use when",
  // "triggers", "when user", "when X is needed", etc.
  const triggerCues = [
    /use when/i,
    /trigger/i,
    /when (?:user|the user|asked|asking)/i,
    /\u89e6\u53d1/, // 触发
    /\u4f7f\u7528/, // 使用
    /\u5f53.*\u8bf4/, // 当...说
    /\u5f53.*\u95ee/, // 当...问
    /invokes?/i,
  ];
  const hasTriggerCue = triggerCues.some((re) => re.test(description));
  if (!hasTriggerCue) {
    addFinding(
      "P1",
      "description-no-trigger-cue",
      "description lacks any 'when to use' / '触发' / 'use when' phrasing — model has nothing to match against."
    );
  }
}

// name field is recommended
if (hasFrontmatter && !frontmatter.name) {
  addFinding(
    "P2",
    "frontmatter-no-name",
    "frontmatter.name is recommended for human-readable identification."
  );
}

// argument-hint if the doc mentions parameters
const mentionsArguments = /\$ARGUMENTS|--[a-z][a-z0-9-]+/i.test(raw);
if (mentionsArguments && !frontmatter["argument-hint"]) {
  addFinding(
    "P2",
    "argument-hint-missing",
    "SKILL.md references CLI-style options but frontmatter has no `argument-hint` for slash-command UX."
  );
}

// allowed-tools — recommended if the skill drives Bash / scripts
const mentionsBash =
  /allowed-tools|run\s+the\s+script|`?bash`?|node\s+scripts\//i.test(raw);
if (mentionsBash && !frontmatter["allowed-tools"]) {
  addFinding(
    "P3",
    "allowed-tools-unset",
    "Skill runs shell commands; consider declaring `allowed-tools` in frontmatter to scope what the agent can execute."
  );
}

// ---------------------------------------------------------------------------
// 3. Line-count budget — Progressive Disclosure
// ---------------------------------------------------------------------------
if (lineCount > 500) {
  addFinding(
    "P1",
    "skill-md-too-long",
    `SKILL.md is ${lineCount} lines — over the 500-line budget. Move detail into references/.`
  );
} else if (lineCount > 350) {
  addFinding(
    "P2",
    "skill-md-getting-long",
    `SKILL.md is ${lineCount} lines — approaching the 500-line budget. Consider extracting reference material.`
  );
}

// ---------------------------------------------------------------------------
// 4. Directory layout
// ---------------------------------------------------------------------------
const referencesDir = join(skillDir, "references");
const scriptsDir = join(skillDir, "scripts");
const hasReferencesDir = existsSync(referencesDir) && statSync(referencesDir).isDirectory();
const hasScriptsDir = existsSync(scriptsDir) && statSync(scriptsDir).isDirectory();

function listFilesRecursive(dir, base = dir) {
  const out = [];
  if (!existsSync(dir)) return out;
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    const st = statSync(full);
    if (st.isDirectory()) out.push(...listFilesRecursive(full, base));
    else out.push(relative(base, full).replace(/\\/g, "/"));
  }
  return out;
}

const referencesFiles = hasReferencesDir ? listFilesRecursive(referencesDir) : [];
const scriptsFiles = hasScriptsDir ? listFilesRecursive(scriptsDir) : [];

// references nesting depth
const maxReferencesDepth = referencesFiles.reduce(
  (d, f) => Math.max(d, f.split("/").length - 1),
  0
);
if (maxReferencesDepth > 1) {
  addFinding(
    "P2",
    "references-nested-too-deep",
    `references/ has files nested ${maxReferencesDepth} levels deep — keep it to one level for discoverability.`,
    { sample: referencesFiles.filter((f) => f.includes("/")).slice(0, 5) }
  );
}

// ---------------------------------------------------------------------------
// 5. Cross-link integrity: references mentioned in SKILL.md
// ---------------------------------------------------------------------------
const refMentionRe = /references\/[A-Za-z0-9_./-]+\.md/g;
const mentionedRefs = new Set(
  (raw.match(refMentionRe) || []).map((s) => s.replace(/^.*?references\//, ""))
);
const orphanRefs = referencesFiles.filter((f) => !mentionedRefs.has(f));
const missingRefs = [...mentionedRefs].filter((f) => !referencesFiles.includes(f));

if (orphanRefs.length > 0) {
  addFinding(
    "P2",
    "references-orphan",
    `${orphanRefs.length} reference file(s) are never linked from SKILL.md — the model won't know to load them.`,
    { orphans: orphanRefs }
  );
}
if (missingRefs.length > 0) {
  addFinding(
    "P1",
    "references-broken-link",
    `SKILL.md references files that do not exist under references/.`,
    { missing: missingRefs }
  );
}

// ---------------------------------------------------------------------------
// 6. Workflow checklist & confirmation nodes
// ---------------------------------------------------------------------------
const checklistItems = (raw.match(/^[\t ]*-\s*\[\s?\]/gm) || []).length;
if (checklistItems < 3) {
  addFinding(
    "P2",
    "workflow-checklist-missing",
    `Found only ${checklistItems} '- [ ]' checklist item(s). High-quality skills give the model a step-by-step checklist to track.`
  );
}

const blockingMarkers = (raw.match(/\u26a0\ufe0f|\u26d4|REQUIRED|BLOCKING/g) || []).length;
const asksUser =
  /AskUserQuestion|ask the user|confirm with the user|stop and confirm|\u786e\u8ba4|\u8be2\u95ee\u7528\u6237/i.test(
    raw
  );
if (!asksUser && blockingMarkers === 0) {
  addFinding(
    "P2",
    "no-confirmation-node",
    "No confirmation node detected (no AskUserQuestion / ⚠️ REQUIRED / ⛔ BLOCKING / '确认' phrasing). Generation-style skills should pause before irreversible actions."
  );
}

// Pre-Delivery / quality gate
const hasPreDelivery = /pre-?delivery|before (?:you )?(?:deliver|finish|return)|quality (?:gate|check)|\u4ea4\u4ed8\u524d/i.test(
  raw
);
if (!hasPreDelivery) {
  addFinding(
    "P3",
    "no-pre-delivery-checklist",
    "No pre-delivery / quality-gate checklist detected. Output-producing skills benefit from a final verification list."
  );
}

// ---------------------------------------------------------------------------
// 7. Scripts pattern — flag inline scripts that should be extracted
// ---------------------------------------------------------------------------
const fencedBlockRe = /```([a-z]*)\n([\s\S]*?)```/g;
let fenceMatch;
let longCodeBlocks = 0;
while ((fenceMatch = fencedBlockRe.exec(raw))) {
  const blockLines = fenceMatch[2].split(/\r?\n/).length;
  if (blockLines > 30) longCodeBlocks++;
}
if (longCodeBlocks > 0) {
  addFinding(
    "P2",
    "long-inline-code",
    `SKILL.md contains ${longCodeBlocks} code block(s) longer than 30 lines — consider extracting them to scripts/ and invoking them.`
  );
}

// ---------------------------------------------------------------------------
// 8. Concrete-question heuristic — discourage vague directives
// ---------------------------------------------------------------------------
const vaguePhrases = [
  /\bmake sure (?:the |that )?(?:code |output )?is good\b/i,
  /\bensure quality\b/i,
  /\bcheck (?:for )?(?:problems|issues)\b/i,
  /\u6ce8\u610f\u8d28\u91cf/,
  /\u4fdd\u8bc1\u8d28\u91cf/,
];
const vagueHits = vaguePhrases.filter((re) => re.test(raw));
if (vagueHits.length >= 2) {
  addFinding(
    "P3",
    "vague-directives",
    "Multiple vague directives detected ('make sure quality is good' etc.). Replace with specific questions the model can answer concretely."
  );
}

// ---------------------------------------------------------------------------
// Emit
// ---------------------------------------------------------------------------
emit(
  {
    targetPath,
    skillDir,
    skillMdPath,
    lineCount,
    hasFrontmatter,
    frontmatter,
    hasReferencesDir,
    hasScriptsDir,
    referencesFiles,
    scriptsFiles,
    mentionedRefs: [...mentionedRefs],
    orphanRefs,
    missingRefs,
    maxReferencesDepth,
    checklistItems,
    blockingMarkers,
    asksUser,
    hasPreDelivery,
    longCodeBlocks,
  },
  findings,
  opts
);

function emit(facts, findings, opts) {
  const counts = findings.reduce(
    (acc, f) => ((acc[f.severity] = (acc[f.severity] || 0) + 1), acc),
    { P0: 0, P1: 0, P2: 0, P3: 0 }
  );
  const summary = {
    counts,
    verdict:
      counts.P0 > 0
        ? "BLOCKED"
        : counts.P1 > 0
        ? "NEEDS_WORK"
        : counts.P2 > 0
        ? "OK_WITH_NOTES"
        : "GOOD",
  };
  const payload = { summary, facts, findings };
  if (opts.json || !opts.quiet) process.stdout.write(JSON.stringify(payload, null, 2));
}
