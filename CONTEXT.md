# Context

## Glossary

### Stage artifact manifest

The stage artifact manifest is the workflow module that names the canonical
artifact paths for each stage. It currently defines perspective artifact paths,
structured synthesis paths, Markdown synthesis paths, and each stage's intended
primary output. It is the first step toward a deeper stage artifact contract.

### Stage artifact consumer

A stage artifact consumer is any hook, tool, or helper that interprets workflow
artifact names after they are written. Examples include checkpoint commit hooks,
stage detection, status rendering, and quality gates. Consumers should derive
stage artifact names from the stage artifact manifest instead of hard-coding
their own filename lists.
