# skill-reviewer

> 给 Agent Skill 做 code review 的 Skill。
> 用 **10 条 rubric + 1 个零依赖 lint 脚本** 检测一个 Skill 是否符合高质量规范，按 **P0–P3 分级** 输出报告；也能 `--template` 生成符合规范的新 Skill 骨架。

核心理念：**这个 Skill 必须遵守它自己要检查的每一条规则**——不然就是用 Slop 检测 Slop。

---

## 它能做什么

| 场景 | 用法 | 输出 |
| ---- | ---- | ---- |
| **审查现有 Skill** | `/skill-reviewer <path>` | P0–P3 分级报告 + 可选的修复 |
| **生成新 Skill 骨架** | `/skill-reviewer --template <name>` | 已经过 lint 自检的新 Skill 目录 |
| **CI / 命令行 lint** | `node scripts/lint-skill.mjs <path>` | JSON，含 `summary.verdict` |
| **聚焦特定规则** | `/skill-reviewer <path> --rules R1,R3` | 只跑指定 rubric |
| **快速 lint（跳过软评）** | `/skill-reviewer <path> --quick` | 只跑脚本硬指标 |

它检查的不是「文字写得好不好」，而是 10 条**可检测的工程规范**：渐进式加载、description 关键词密度、工作流 checklist、确认节点、脚本封装、参数系统、references 组织、Pre-Delivery、CLI+Skill 模式、反 Slop。

---

## Install（安装）

**一行安装**：

```bash
npx skills add Liu-PenPen/skill-review
```

常用选项：

| 选项 | 含义 |
| ---- | ---- |
| `--list` | 只列出本仓库里可被识别的 skill，不安装 |
| `-a cursor` | 只安装到 Cursor（若你只用 Cursor，可加上） |
| `-g` | 安装到用户目录，所有项目共用（默认多为「当前项目」范围，视 CLI 提示为准） |
| `-y` | 跳过确认，适合脚本/CI |

安装完成后，会在对应的 skills 目录下出现本 skill（`SKILL.md` 里 `name` 为 `skill-reviewer`，目录名一般与该 id 一致）。之后在聊天里用 `/skill-reviewer` 或自然语言触发即可；命令行 lint 路径见下文「直接调用 lint 脚本」，把路径换成你机器上实际安装目录下的 `scripts/lint-skill.mjs`。

---

## 三种使用方式

### 1. 斜杠命令（最常用）

在 Cursor 聊天框里输入：

```text
/skill-reviewer 
/skill-reviewer xxx --quick
/skill-reviewer xxx --rules R1,R3,R7
/skill-reviewer --template my-new-skill
```

### 2. 自然语言触发

description 里有关键词网，下面任意一种说法都能自动触发：

- "帮我 review 一下 `.cursor/skills/superdesign`"
- "审查这个 skill 写得怎么样：`<path>`"
- "看看 `<path>` 这个 skill 是不是 slop"
- "audit my skill at `<path>`"
- "check the SKILL.md at `<path>`"
- "生成一个叫 `xxx` 的 skill 模板"

### 3. 直接调用 lint 脚本

CI、git hook、命令行调试都用这个：

```bash
node .cursor/skills/skill-reviewer/scripts/lint-skill.mjs .cursor/skills/my-skill --json
```

详见 [lint-skill.mjs CLI 参考](#lint-skillmjs-cli-参考)。

---

## Review 模式

### 工作流（来自 `SKILL.md`）

```text
- [ ] Step 0  Confirm mode & target           ⚠️ REQUIRED
- [ ] Step 1  Run lint-skill.mjs              (hard facts)
- [ ] Step 2  Soft review per rubric          (per-step reference load)
- [ ] Step 3  Aggregate findings by P0–P3
- [ ] Step 4  Ask user how to proceed         ⚠️ REQUIRED
- [ ] Step 5  Deliver report / apply fixes
- [ ] Step 6  Pre-delivery self-check
```
---

## Template 模式

### 工作流

```text
- [ ] Step T0 Gather skill intent             ⚠️ REQUIRED
- [ ] Step T1 Generate scaffold from template-skeleton.md
- [ ] Step T2 Run lint on the new scaffold    (self-verify)
- [ ] Step T3 Report scaffold + lint result
```

### 使用

```text
/skill-reviewer --template code-reviewer
```

会被问到：

1. Skill 名（kebab-case）
2. 一句话用途
3. 5–10 个真实用户会说的触发短语
4. 是否需要脚本 / 是否产生输出 / 是否需要确认节点

然后生成：

```text
.cursor/skills/<name>/
├── SKILL.md           # 已经填好 frontmatter、工作流、Pre-Delivery、Options 表
├── scripts/           # 只在你说"需要脚本"时创建
│   └── .gitkeep
└── references/
    └── .gitkeep
```

最后 **自动跑 lint** 验证骨架本身合格（verdict ≥ `OK_WITH_NOTES`），不合格就当场修。

---

## 10 条 Rubric

| ID  | 名称                | 关键检查项                                                       | 详细文档 |
| --- | ------------------- | ---------------------------------------------------------------- | -------- |
| R1  | Progressive Loading | SKILL.md 行数、长代码块、references 是否按需加载                 | [rubric-progressive-loading.md](references/rubric-progressive-loading.md) |
| R2  | Description         | 关键词密度、触发短语、长度（≥ 120 字符）                         | [rubric-description.md](references/rubric-description.md) |
| R3  | Workflow Checklist  | `- [ ]` 步骤、`⚠️ REQUIRED` / `⛔ BLOCKING` 标记、宏观→微观顺序 | [rubric-workflow-checklist.md](references/rubric-workflow-checklist.md) |
| R4  | Scripts Pattern     | 确定性操作是否封装、长内嵌代码是否提取                           | [rubric-scripts-pattern.md](references/rubric-scripts-pattern.md) |
| R5  | Good Questions      | 用具体可回答的问题代替"注意质量"这种空指令                       | [rubric-good-questions.md](references/rubric-good-questions.md) |
| R6  | Confirmation        | 不可逆操作前是否有结构化确认节点                                 | [rubric-confirmation.md](references/rubric-confirmation.md) |
| R7  | Pre-Delivery        | 交付前是否有可验证的自检 checklist                               | [rubric-pre-delivery.md](references/rubric-pre-delivery.md) |
| R8  | Arguments           | `$ARGUMENTS` 解析、`argument-hint`、Options 表、部分运行 flag    | [rubric-arguments.md](references/rubric-arguments.md) |
| R9  | References Org      | 按领域分组、无 orphan、无 broken link、嵌套 ≤ 1 层               | [rubric-references-org.md](references/rubric-references-org.md) |
| R10 | CLI + Skill         | `allowed-tools` 收紧、CLI 文档简洁、不重复造 MCP                 | [rubric-cli-pattern.md](references/rubric-cli-pattern.md) |

聚焦特定 rubric：

```text
/skill-reviewer <path> --rules R1,R2,R7
```

---


## lint-skill.mjs CLI 参考

### 命令格式

```bash
node .cursor/skills/skill-reviewer/scripts/lint-skill.mjs <target> [--json] [--quiet]
```

- `<target>` — Skill 目录（推荐），或者直接指向 `SKILL.md` 文件。
- `--json`（默认开启）— stdout 输出 JSON。
- `--quiet` — 抑制非 JSON 输出。

### 输出 JSON 结构

```jsonc
{
  "summary": {
    "counts": { "P0": 0, "P1": 0, "P2": 2, "P3": 1 },
    "verdict": "OK_WITH_NOTES"          // BLOCKED | NEEDS_WORK | OK_WITH_NOTES | GOOD
  },
  "facts": {
    "skillMdPath": "...",
    "lineCount": 248,
    "hasFrontmatter": true,
    "frontmatter": { "name": "...", "description": "...", "argument-hint": "...", ... },
    "hasReferencesDir": true,
    "hasScriptsDir": true,
    "referencesFiles": [ "rubric-...md", ... ],
    "scriptsFiles":   [ "lint-skill.mjs" ],
    "mentionedRefs":  [ "rubric-...md", ... ],   // SKILL.md 里引用的
    "orphanRefs":     [],                         // 存在但未被引用
    "missingRefs":    [],                         // 被引用但不存在
    "maxReferencesDepth": 0,
    "checklistItems": 17,
    "blockingMarkers": 15,
    "asksUser": true,
    "hasPreDelivery": true,
    "longCodeBlocks": 0
  },
  "findings": [
    {
      "id": "F1",
      "severity": "P2",
      "rule": "argument-hint-missing",
      "message": "SKILL.md references CLI-style options but frontmatter has no `argument-hint`...",
      "evidence": null
    }
  ]
}
```

### 退出码

| 码 | 含义                                                        |
| -- | ----------------------------------------------------------- |
| 0  | 脚本正常运行（包括有 finding 的情况，**verdict 在 JSON 里**） |
| 2  | 命令行参数错误（没传 target）                               |

> **注意**：脚本不会用退出码区分 verdict。CI 里需要用 `jq` 或类似工具读 `summary.verdict`，见下面 [CI 章节](#在-ci-里使用)。

### 检测项一览（脚本侧）

| Rule ID                       | 触发条件                                          | Severity |
| ----------------------------- | ------------------------------------------------- | -------- |
| `skill-md-missing`            | SKILL.md 不存在                                   | P0       |
| `frontmatter-missing`         | 没有 `---` 包围的 frontmatter                     | P0       |
| `description-missing`         | frontmatter 缺 description                        | P0       |
| `description-too-short`       | description < 80 字符                             | P1       |
| `description-no-trigger-cue`  | description 没有"use when / 触发 / when user"     | P1       |
| `frontmatter-no-name`         | 缺 name                                           | P2       |
| `argument-hint-missing`       | 用了 CLI flag 但没声明 argument-hint              | P2       |
| `allowed-tools-unset`         | 跑 shell 但没声明 allowed-tools                   | P3       |
| `skill-md-too-long`           | SKILL.md > 500 行                                 | P1       |
| `skill-md-getting-long`       | SKILL.md 350–500 行                               | P2       |
| `references-nested-too-deep`  | references 嵌套超过 1 层                          | P2       |
| `references-orphan`           | references 文件未被 SKILL.md 引用                 | P2       |
| `references-broken-link`      | SKILL.md 引用了不存在的 reference                 | P1       |
| `workflow-checklist-missing`  | `- [ ]` checklist 项少于 3 个                     | P2       |
| `no-confirmation-node`        | 没有 `AskUserQuestion` / `⚠️ REQUIRED` / `⛔ BLOCKING` | P2       |
| `no-pre-delivery-checklist`   | 没有 Pre-Delivery / quality gate                  | P3       |
| `long-inline-code`            | SKILL.md 内嵌代码块超过 30 行                     | P2       |
| `vague-directives`            | 出现 ≥ 2 处"注意质量"这种空指令                   | P3       |

---

## 示例：完整 Review 流程

```text
You:  /skill-reviewer .cursor/skills/superdesign

Skill: (Step 0)
       请确认审查范围：
       1) 全量 rubric
       2) 只跑 lint（--quick）
       3) 指定 rule IDs
       请选择并确认目标路径。

You:  全量

Skill: (Step 1) 运行 lint-skill.mjs ...
       Hard facts:
       - lineCount: 50
       - hasReferencesDir: false
       - checklistItems: 0
       - hasPreDelivery: false
       Findings (硬): F1 (P2), F2 (P2), F3 (P3)

       (Step 2) 加载 R1, R2, R3, R6, R7 ...
       软评新增 finding：R3 工作流没有 `⚠️ REQUIRED` 标记 → P2

       (Step 3) 汇总：P0=0 P1=0 P2=3 P3=1
       Verdict: OK_WITH_NOTES

       (Step 4)
       要怎么处理？
       1) 修全部
       2) 修 P0+P1（这次没有）
       3) 指定 ID 修
       4) 只看不改（默认）

You:  只看不改

Skill: (Step 5) 输出报告 ...
       (Step 6) Pre-delivery 自检通过 ✓
```

---

## 在 CI 里使用

### npm script

```jsonc
// package.json
{
  "scripts": {
    "lint:skill": "node .cursor/skills/skill-reviewer/scripts/lint-skill.mjs",
    "lint:skills:all": "node .cursor/skills/skill-reviewer/scripts/lint-skill.mjs .cursor/skills/skill-reviewer"
  }
}
```

### GitHub Actions（按 verdict 做闸门）

```yaml
- name: Lint all skills
  shell: bash
  run: |
    set -e
    for d in .cursor/skills/*/; do
      echo "::group::lint $d"
      out=$(node .cursor/skills/skill-reviewer/scripts/lint-skill.mjs "$d" --json)
      verdict=$(echo "$out" | jq -r .summary.verdict)
      echo "$out" | jq .
      echo "::endgroup::"
      case "$verdict" in
        BLOCKED|NEEDS_WORK) echo "❌ $d -> $verdict"; exit 1 ;;
        *) echo "✅ $d -> $verdict" ;;
      esac
    done
```

### pre-commit hook

```bash
#!/usr/bin/env bash
# .git/hooks/pre-commit
changed=$(git diff --cached --name-only | grep -E '\.cursor/skills/[^/]+/SKILL\.md$' || true)
for f in $changed; do
  dir=$(dirname "$f")
  v=$(node .cursor/skills/skill-reviewer/scripts/lint-skill.mjs "$dir" --json | jq -r .summary.verdict)
  [ "$v" = "BLOCKED" ] && { echo "Skill $dir is BLOCKED, fix before commit."; exit 1; }
done
```

---


## FAQ

**Q1：脚本会修改我的 Skill 文件吗？**
不会。`lint-skill.mjs` 是纯只读的，只输出 JSON。修改只发生在 Skill 工作流 Step 5，且必须经过 Step 4 你明确同意。

**Q2：检测器自己是 `GOOD` 还是带 finding？**
当前是 `GOOD`，0 finding。每次改完 `SKILL.md` 或加新 rubric，都应该重新跑一次自检：

```bash
node .cursor/skills/skill-reviewer/scripts/lint-skill.mjs .cursor/skills/skill-reviewer
```

**Q3：怎么验证 lint 脚本不是"全 GOOD 一刀切"？**
拿同仓库的 `.cursor/skills/superdesign` 跑一下，应该报出 3 个真实问题（`argument-hint-missing`、`workflow-checklist-missing`、`no-pre-delivery-checklist`），verdict `OK_WITH_NOTES`。

**Q4：能用来约束 AI 生成 Skill 的过程吗？**
两种用法：
- **事后审查**：AI 写完后跑 `/skill-reviewer <path>`，按报告改。
- **事前约束**：让 AI 生成新 Skill 时 `/skill-reviewer --template <name>`，由本 Skill 套着模板生成，最后自动 lint 自检。

**Q5：脚本依赖什么 Node 版本？**
Node 18+。只用了 `node:fs` / `node:path` 内置模块，零外部依赖。

**Q6：能在 Windows / WSL / macOS / Linux 都跑吗？**
能。脚本里所有路径都用 `node:path` 拼接，跨平台 OK。

**Q7：如果我的 Skill 是放在 `~/.agents/skills/` 用户级目录下，怎么 lint？**
直接传绝对路径：

```bash
node .cursor/skills/skill-reviewer/scripts/lint-skill.mjs "$HOME/.agents/skills/code-reviewer" --json
```

**Q8：能针对一个 PR 里改过的 Skill 增量 lint 吗？**
能，配合 `git diff --name-only origin/main...HEAD`：

```bash
git diff --name-only origin/main...HEAD | grep -E '\.cursor/skills/[^/]+/' \
  | sed -E 's|(.cursor/skills/[^/]+/).*|\1|' | sort -u \
  | xargs -I{} node .cursor/skills/skill-reviewer/scripts/lint-skill.mjs {} --json
```

**Q9：rubric 是终版了吗？**
不是。这 10 条是总结的核心套路。

---

