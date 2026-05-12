#!/usr/bin/env python3
"""Validate CT mode, gate, and self-upgrade contracts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate CT contracts')
    parser.add_argument('--root', default='.', help='Repository root')
    args = parser.parse_args()

    root = Path(args.root)
    errors: list[str] = []
    mode_runtime = _load_yaml(root / 'shared/ct/mode-runtime.yaml', errors)
    gates = _load_yaml(root / 'shared/quality/gates.yaml', errors)
    policy = _load_yaml(root / 'shared/ct/self-upgrade-policy.yaml', errors)

    if mode_runtime:
        errors.extend(_validate_mode_runtime(mode_runtime))
    if gates:
        errors.extend(_validate_ct_gates(gates))
    if policy:
        errors.extend(_validate_self_upgrade_policy(policy))

    if errors:
        for error in errors:
            print(f'ERROR: {error}', file=sys.stderr)
        return 1

    print('CT contracts OK')
    return 0


def _validate_mode_runtime(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    modes = data.get('modes', {})
    for mode in ['off', 'lite', 'strict', 'experiment']:
        if mode not in modes:
            errors.append(f'mode-runtime missing mode: {mode}')

    lite = modes.get('lite', {})
    lite_run = set(lite.get('run', []))
    lite_skip = set(lite.get('skip', []))
    forbidden_lite = {'ct_stack', 'ct_compliance', 'ct_compliance_report', 'experiment_harness', 'autonomous_upgrade'}
    overlap = lite_run & forbidden_lite
    if overlap:
        errors.append(f'lite mode must not run heavy CT phases: {sorted(overlap)}')
    missing_skip = {'ct_stack', 'experiment_harness', 'autonomous_upgrade'} - lite_skip
    if missing_skip:
        errors.append(f'lite mode should explicitly skip: {sorted(missing_skip)}')
    if lite.get('mode_budget', {}).get('experiment_harness') is not False:
        errors.append('lite mode budget must disable experiment_harness')
    if lite.get('mode_budget', {}).get('autonomous_upgrade') is not False:
        errors.append('lite mode budget must disable autonomous_upgrade')

    strict = modes.get('strict', {})
    if strict.get('mode_budget', {}).get('autonomous_upgrade') != 'proposal_only':
        errors.append('strict autonomous_upgrade must be proposal_only')

    experiment = modes.get('experiment', {})
    required_experiment = {'hypotheses', 'experiment_plan', 'eval_rubric', 'failure_modes', 'experiment_harness'}
    missing_experiment = required_experiment - set(experiment.get('run', []))
    if missing_experiment:
        errors.append(f'experiment mode missing phases: {sorted(missing_experiment)}')

    return errors


def _validate_ct_gates(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    gates = data.get('gates', {})
    for gate in ['CT_LITE', 'CT_STRICT', 'CT_EXPERIMENT']:
        if gate not in gates:
            errors.append(f'gates missing {gate}')
        elif 'applies_when' not in gates[gate]:
            errors.append(f'{gate} missing applies_when')

    lite_ids = _mandatory_ids(gates.get('CT_LITE', {}))
    strict_ids = _mandatory_ids(gates.get('CT_STRICT', {}))
    experiment_ids = _mandatory_ids(gates.get('CT_EXPERIMENT', {}))

    if 'ct_stack_exists' in lite_ids:
        errors.append('CT_LITE must not require ct_stack_exists')
    if 'hypothesis_testability' in lite_ids:
        errors.append('CT_LITE must not require hypothesis_testability')
    if 'hypothesis_testability' in strict_ids:
        errors.append('CT_STRICT must not require hypothesis_testability')
    for required in ['ct_stack_exists', 'ct_compliance_exists', 'no_high_ct_violation', 'evidence_coverage']:
        if required not in strict_ids:
            errors.append(f'CT_STRICT missing {required}')
    for required in ['hypotheses_exist', 'hypothesis_testability', 'experiment_plan_exists', 'experiment_readiness']:
        if required not in experiment_ids:
            errors.append(f'CT_EXPERIMENT missing {required}')

    return errors


def _validate_self_upgrade_policy(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    levels = data.get('automation_levels', {})
    l4a = levels.get('L4a', {})
    l4b = levels.get('L4b', {})
    l4c = levels.get('L4c', {})
    if l4a.get('requires_human_approval') is not False:
        errors.append('L4a should not require human approval')
    for level_name, level in [('L4b', l4b), ('L4c', l4c)]:
        if level.get('requires_human_approval') is not True:
            errors.append(f'{level_name} must require human approval')
    l4a_allowed = ' '.join(l4a.get('allowed', []))
    if 'quality gate' in l4a_allowed or 'workflow script' in l4a_allowed:
        errors.append('L4a must not allow quality gate or workflow script changes')
    hard_stops = ' '.join(data.get('hard_stops', []))
    for phrase in ['lowers a threshold', 'removes a mandatory criterion', 'workflow scripts or quality gates']:
        if phrase not in hard_stops:
            errors.append(f'hard_stops missing phrase: {phrase}')
    return errors


def _mandatory_ids(gate: dict[str, Any]) -> set[str]:
    return {
        item.get('id')
        for item in gate.get('pass_criteria', {}).get('mandatory', [])
        if isinstance(item, dict)
    }


def _load_yaml(path: Path, errors: list[str]) -> Any:
    try:
        import yaml
    except ImportError:
        errors.append('PyYAML is required to validate CT contracts')
        return None
    try:
        with path.open('r', encoding='utf-8') as handle:
            return yaml.safe_load(handle) or {}
    except Exception as exc:  # pragma: no cover - defensive error formatting
        errors.append(f'{path}: failed to parse YAML: {exc}')
        return None


if __name__ == '__main__':
    raise SystemExit(main())
