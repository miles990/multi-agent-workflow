"""Best-effort runtime dependency bootstrap for portable CLI copies."""

from __future__ import annotations

import importlib
import os
import site
import subprocess
import sys
import sysconfig
import venv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class PythonDependency:
    import_name: str
    package_name: str


CLI_DEPENDENCIES = [
    PythonDependency('typer', 'typer[all]>=0.9.0'),
    PythonDependency('rich', 'rich>=13.0.0'),
    PythonDependency('pydantic', 'pydantic>=2.0.0'),
    PythonDependency('yaml', 'PyYAML>=6.0'),
]


def ensure_python_dependencies(dependencies: Iterable[PythonDependency]) -> None:
    missing = [dep for dep in dependencies if not _can_import(dep.import_name)]
    if not missing:
        return

    if os.environ.get('MAW_DISABLE_AUTO_INSTALL') == '1':
        names = ', '.join(dep.package_name for dep in missing)
        raise RuntimeError(f'Missing Python dependencies: {names}')

    packages = [dep.package_name for dep in missing]
    install_commands = [
        [sys.executable, '-m', 'pip', 'install', '--quiet', *packages],
        [sys.executable, '-m', 'pip', 'install', '--quiet', '--user', *packages],
    ]

    installed = False
    for command in install_commands:
        try:
            subprocess.run(
                command,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=180,
            )
            installed = True
            break
        except Exception:
            continue

    if not installed:
        installed = _install_into_managed_venv(packages)

    still_missing = [dep.package_name for dep in missing if not _can_import(dep.import_name)]
    if still_missing:
        joined = ', '.join(still_missing)
        if installed:
            raise RuntimeError(f'Installed dependencies, but imports still failed: {joined}')
        raise RuntimeError(f'Unable to install Python dependencies: {joined}')


def _can_import(import_name: str) -> bool:
    try:
        importlib.import_module(import_name)
        return True
    except ImportError:
        return False


def _install_into_managed_venv(packages: list[str]) -> bool:
    """Install dependencies into a managed user venv for PEP 668 systems."""
    venv_dir = Path(
        os.environ.get(
            'MAW_PYTHON_ENV',
            str(Path.home() / '.cache' / 'multi-agent-workflow' / 'python-env'),
        )
    )

    try:
        if not venv_dir.exists():
            venv.EnvBuilder(with_pip=True, clear=False).create(venv_dir)

        python = venv_dir / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        subprocess.run(
            [str(python), '-m', 'pip', 'install', '--quiet', *packages],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=240,
        )

        purelib = subprocess.check_output(
            [
                str(python),
                '-c',
                'import sysconfig; print(sysconfig.get_paths()["purelib"])',
            ],
            text=True,
        ).strip()
        platlib = subprocess.check_output(
            [
                str(python),
                '-c',
                'import sysconfig; print(sysconfig.get_paths()["platlib"])',
            ],
            text=True,
        ).strip()

        for path in [purelib, platlib, *site.getsitepackages(), sysconfig.get_paths().get('purelib', '')]:
            if path and path not in sys.path:
                sys.path.insert(0, path)
        return True
    except Exception:
        return False
