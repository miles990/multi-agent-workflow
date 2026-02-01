# Changelog

All notable changes to this project will be documented in this file.

## [2.4.1] - 2026-02-01

### 🐛 Bug Fixes

- **skills**: remove readonly agent restriction and add Task tool requirement (ddb9eb4)
- **hooks**: add fallback logging and workflow init requirement (d802251)
- move agents to plugin root directory (97b16f4)
- simplify subagent YAML frontmatter format (ed20041)
- convert subagent configs from JSON to Markdown format (f088a62)
- enforce perspective reports and unify directory structure (7e73323)
- improve REDUCE strategy to ensure completeness and quality (32930cd)
- handle large file token limit in REDUCE phase (1e0e97f)
- remove unrecognized keys from plugin.json (6f79509)
- ensure perspective reports are saved to files (b806a84)
- remove invalid skills field from plugin.json (5cf4dea)
- **research**: 修正 usage.md 共用模組連結 (2692551)
- Change repository field from object to string (228254e)
- Correct plugin source path for skill discovery (ed03c70)

### ✨ Features

- **hooks**: add checkpoint commit for workflow stages (19edffb)
- **plugin-dev**: add /plugin-dev skill for dogfooding (7abd61e)
- **tasks**: complete plugin dev workflow (d1690f2)
- **plans**: complete plugin dev workflow (6eddb17)
- **plans**: complete plugin dev workflow (2636f1e)
- **plans**: complete plugin workflow (018a553)
- **plugin-workflow**: add complete plugin development workflow system (48d562f)
- **git**: implement unified git_lib module (22accf8)
- **structure**: implement plugin optimization v2.3.0 (a811425)
- **skills**: add workflow enforcement mechanism (7dd83b0)
- **orchestrate**: implement File-Based Handoff Protocol v3.3 (1634f90)
- **orchestrate**: add intelligent parallel execution and context limit handling (a6d6eff)
- **hooks**: add auto git commit on Task completion (e63ff6d)
- upgrade all Skills to Claude Code latest features (824c67f)
- add execution profiles and context freshness mechanism (87cf946)
- integrate Claude Code workflows (6ff4b33)
- **hooks**: use SubagentStop for git commit timing (3a83663)
- **hooks**: add automated logging, state tracking, and git commit (fb4f42c)
- add Python CLI for hybrid architecture orchestration (47d43c8)
- add action-level logging for debugging and tracing (301c2b2)
- add CP4 Task Commit protocol for persistent memory (8f2b8e7)
- add /status skill for workflow progress visualization (68e077a)
- unify output structure across all skills (bd85a67)
- preserve complete perspective reports + add summaries directory (5d4af5c)
- comprehensive multi-agent workflow optimization (47d99e2)
- add TASKS skill for task decomposition between PLAN and IMPLEMENT (77b27bc)
- add progress display and error handling (Phase 3) (24bd13a)
- add reporting system (Phase 2) (07c2d57)
- add metrics infrastructure (Phase 1) (93aa9aa)
- add health-check tool for plugin integrity validation (5395cfb)
- add Git Worktree Integration (M6) (a3aead6)
- **orchestrate**: 創建 orchestrate skill 完整結構 (a52ee6a)
- **implement**: 創建 implement skill 完整結構 (ff9935b)
- **verify**: 創建 verify skill 完整結構 (894dec3)
- **review**: 創建 quickstart、perspectives、config 和 templates (1051e15)
- **review**: 創建 review skill 主入口 SKILL.md (055c537)
- **plan**: 創建 config 和 templates (0c87b67)
- **plan**: 創建 quickstart 和 perspectives 文檔 (2558c60)
- **plan**: 創建 plan skill 主入口 SKILL.md (f4d4ede)
- **shared**: 完成共用模組提取 (a434cb6)
- Add marketplace configuration (d36e845)
- Initial release of Multi-Agent Research Skill v1.0.0 (7d80e60)

### 🔧 Chores

- **task**: 設計自動 commit 改進方案 (7fe2509)
- add Python build and test artifacts to .gitignore (0f6335a)
- add .gitignore and research synthesis (3b0a774)
- 更新 plugin.json 和 marketplace.json (4573c20)

### 📚 Documentation

- **research**: complete plugin dev workflow (93d635b)
- **CLAUDE.md**: add plugin development experience and techniques (a84d10e)
- **claude**: add development experiences from git_lib refactoring (af15b6d)
- **CLAUDE**: add development tools and best practices (9ed1c4d)
- **readme**: fix orchestrate command name (2746699)
- **plan**: update embedding provider to use local bge-m3 as default (9b08ee4)
- **plan**: update clawdbot MVP plan with full memory/session systems (6af4f5b)
- **plan**: complete clawdbot MVP implementation plan (bd88e92)
- **research**: complete clawdbot lightweight MVP research (9e90560)
- **research**: complete clawdbot componentization strategy research (9bfe335)
- **research**: complete clawdbot auto-reply system research (79af7d9)
- **research**: complete clawdbot auto reply system (4c5517b)
- **research**: complete clawdbot auto reply system (9a95937)
- **research**: complete clawdbot auto reply system (6abc274)
- **research**: complete clawdbot memory system research (90afc5b)
- add explicit parallel Task execution instructions to all skills (b67c625)
- add parallel task execution learning and checklist (6b050e2)
- add Claude Code new features integration guide (a8934ce)
- add CLAUDE.md aligned with plugin configuration (4983b36)
- **research**: complete claude code workflows (84496a3)
- **research**: complete claude code workflows (23cb354)
- **research**: complete claude code workflows (e9941fa)
- **research**: add Claude Code workflows research (c9e0e56)
- update README with new modules and changelog (67c363f)
- 更新 README 反映所有 skill 已完成 (ace0f4b)
- 更新 README.md 為 multi-agent-workflow (da6837a)
- Update README with correct skill invocation format (a2dad4b)
- Update README with badges and marketplace instructions (162d73e)

### 🧪 Tests

- add comprehensive test suite for context freshness mechanism (bd56aaf)

### ♻️ Refactoring

- simplify context freshness mechanism based on GSD design (7ce23e8)
- **research**: 更新引用共用模組 (c5dbe29)
- 重組專案為 multi-agent-workflow (7bbdd91)
