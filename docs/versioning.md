# Versioning

This repository has multiple distributable surfaces. Their versions are related
but not identical.

| Surface | Source of truth | Meaning |
|---|---|---|
| Plugin package | `plugin.json` | Claude Code plugin distribution version |
| Python CLI/tooling | `pyproject.toml` | Python package and maintainer tooling version |
| User-facing skills | `skills/*/SKILL.md` | Individual skill contract version |
| CT schema | `shared/ct/ct-schema.yaml` | Constraint Texture artifact schema version |
| README changelog | `README.md` / `CHANGELOG.md` | Released plugin-facing changes unless marked Unreleased |

Rules:

- `plugin.json` controls marketplace/plugin release semantics.
- `pyproject.toml` controls Python CLI/tooling packaging semantics.
- Skill versions may move independently when a skill contract changes without a
  plugin release.
- CT schema version changes when generated CT artifacts or metrics contracts
  change.
- README changelog entries that are not released must be labeled `Unreleased`.
