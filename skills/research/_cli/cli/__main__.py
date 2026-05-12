"""
支援 python -m cli 執行
"""

from cli.dependencies import CLI_DEPENDENCIES, ensure_python_dependencies

ensure_python_dependencies(CLI_DEPENDENCIES)

from cli.main import app

if __name__ == "__main__":
    app()
