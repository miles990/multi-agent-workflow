#!/usr/bin/env python3
"""Validate CT claims registry files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    'id',
    'statement',
    'evidence_type',
    'confidence',
    'risk',
    'ct_layer',
}

ENUMS = {
    'evidence_type': {'source', 'reasoning', 'hypothesis', 'experiment'},
    'confidence': {'high', 'medium', 'low'},
    'risk': {'low', 'medium', 'high'},
    'ct_layer': {'evidence', 'risk', 'experiment', 'output'},
}


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate CT claims registry files')
    parser.add_argument('--claims-dir', required=True, help='Directory containing *.claims.yaml')
    args = parser.parse_args()

    claims_dir = Path(args.claims_dir)
    errors = validate_claims_dir(claims_dir)

    if errors:
        for error in errors:
            print(f'ERROR: {error}', file=sys.stderr)
        return 1

    print(f'Claims registry OK: {claims_dir}')
    return 0


def validate_claims_dir(claims_dir: Path) -> list[str]:
    errors: list[str] = []
    if not claims_dir.exists():
        return [f'claims directory does not exist: {claims_dir}']

    files = sorted(claims_dir.glob('*.claims.yaml')) + sorted(claims_dir.glob('*.claims.yml'))
    if not files:
        return [f'no *.claims.yaml files found in {claims_dir}']

    seen_ids: set[str] = set()
    for path in files:
        data = _load_yaml(path, errors)
        if data is None:
            continue
        claims = data.get('claims')
        if not isinstance(claims, list):
            errors.append(f'{path}: top-level claims must be a list')
            continue
        for index, claim in enumerate(claims):
            if not isinstance(claim, dict):
                errors.append(f'{path}: claim[{index}] must be a mapping')
                continue
            claim_id = str(claim.get('id', '')).strip()
            location = f'{path}: claim[{claim_id or index}]'
            missing = sorted(field for field in REQUIRED_FIELDS if not claim.get(field))
            if missing:
                errors.append(f'{location} missing required fields: {", ".join(missing)}')
            if claim_id:
                if claim_id in seen_ids:
                    errors.append(f'{location} duplicates claim id {claim_id}')
                seen_ids.add(claim_id)
            for field, allowed in ENUMS.items():
                value = claim.get(field)
                if value and value not in allowed:
                    errors.append(
                        f'{location} invalid {field}={value!r}; expected one of {sorted(allowed)}'
                    )
            if claim.get('evidence_type') in {'source', 'experiment'} and not claim.get('source_ref'):
                errors.append(f'{location} requires source_ref for {claim.get("evidence_type")}')

    return errors


def _load_yaml(path: Path, errors: list[str]) -> Any:
    try:
        import yaml
    except ImportError:
        errors.append('PyYAML is required to validate claims registry files')
        return None

    try:
        with path.open('r', encoding='utf-8') as handle:
            return yaml.safe_load(handle) or {}
    except Exception as exc:  # pragma: no cover - defensive error formatting
        errors.append(f'{path}: failed to parse YAML: {exc}')
        return None


if __name__ == '__main__':
    raise SystemExit(main())

