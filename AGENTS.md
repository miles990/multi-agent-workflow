# Repository Guidelines

## Project Structure & Module Organization

This repository is a Python CLI and Claude Code plugin for a multi-agent workflow. Core CLI code lives in `cli/`, with subpackages for configuration, orchestration, prompts, plugin tooling, I/O, and validation. Workflow skills are under `skills/`, shared reusable framework assets are under `shared/`, and Claude subagent definitions live in `agents/`. Shell and release helpers are in `scripts/`, plugin metadata is in `plugin.json` and `.claude-plugin/`, and tests are grouped under `tests/` by area such as `tests/plugin/`, `tests/integration/`, and `tests/context_freshness/`.

## Build, Test, and Development Commands

- `pip install -e ".[dev]"`: install the package locally with pytest and coverage tools.
- `maw --help`: verify the installed CLI entry point from `pyproject.toml`.
- `python -m pytest tests/`: run the full test suite.
- `python -m pytest tests/plugin/`: run plugin-specific tests while iterating on release or cache tooling.
- `./scripts/validate-skills.sh`: validate skill files after editing anything under `skills/` or shared skill resources.

## Coding Style & Naming Conventions

Use Python 3.10+ and keep code type-friendly with clear function names and small modules. Follow existing naming: Python files and test files use `snake_case`, test classes use `Test*`, and test functions use `test_*`. Keep Markdown skill content concise and structured with actionable headings. Prefer existing helpers in `cli/`, `shared/`, and `scripts/` before adding new abstractions.

## Testing Guidelines

Pytest is configured in `pyproject.toml` with `tests` as the test root, `test_*.py` file discovery, and verbose short tracebacks. Add focused tests near the affected area. For async behavior, use the configured `pytest-asyncio` support. Run `python -m pytest tests/` before submitting changes; run `./scripts/validate-skills.sh` for skill changes.

## Commit & Pull Request Guidelines

Recent history uses Conventional Commit style, such as `feat(research): ...`, `fix(workflow): ...`, `tidy(skills): ...`, and `chore(gitignore): ...`. Keep commits scoped and imperative. Pull requests should include a concise summary, affected commands or skills, tests run, and any relevant issue links. Include screenshots only for UI-facing documentation or plugin marketplace changes.

## Agent-Specific Instructions

Respect `CLAUDE.md` as the primary project memory. When editing workflow behavior, check related files in `skills/`, `_shared` copies, and `shared/` so portable skill bundles stay consistent.
