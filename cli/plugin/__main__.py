"""CLI entry point for plugin commands.

Usage:
    python -m cli.plugin <command> [options]

Commands:
    sync        Sync to Claude Code cache
    watch       Watch mode (hot-reload)
    validate    Validate plugin structure
    status      Show cache and version status
    version     Version management
    release     Full release workflow
"""

import argparse
import json
import sys
from pathlib import Path

from .cache import CacheManager
from .version import VersionManager, BumpLevel
from .dev import DevCommands
from .release import ReleaseCommands


def get_project_dir() -> Path:
    """Get the project directory."""
    return Path.cwd()


def cmd_sync(args: argparse.Namespace) -> int:
    """Execute sync command."""
    project_dir = get_project_dir()
    cache_manager = CacheManager(project_dir)
    dev = DevCommands(project_dir, cache_manager)

    try:
        result = dev.sync(force=args.force, dry_run=args.dry_run)

        if args.dry_run:
            print("Preview (dry-run):")
            for f in result.files_added:
                print(f"  + {f}")
            for f in result.files_modified:
                print(f"  ~ {f}")
            for f in result.files_deleted:
                print(f"  - {f}")
            return 0

        if result.success:
            print("Sync completed")
            print(f"  Added: {len(result.files_added)} files")
            print(f"  Modified: {len(result.files_modified)} files")
            print(f"  Deleted: {len(result.files_deleted)} files")
            print(f"  Duration: {result.duration_ms}ms")
            return 0
        else:
            print(f"Sync failed: {result.error}")
            return 1

    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_status(args: argparse.Namespace) -> int:
    """Execute status command."""
    project_dir = get_project_dir()
    cache_manager = CacheManager(project_dir)
    version_manager = VersionManager(project_dir)

    try:
        cache_status = cache_manager.status()
        current_version = version_manager.get_current_version()
        plugin_name = cache_manager.plugin_name

        if args.json:
            output = {
                "plugin": {
                    "name": plugin_name,
                    "version": current_version,
                },
                "cache": {
                    "path": str(cache_status.cache_path),
                    "exists": cache_status.exists,
                    "valid": cache_status.is_valid,
                    "file_count": cache_status.file_count,
                    "size_bytes": cache_status.size_bytes,
                    "last_sync": cache_status.last_sync.isoformat() if cache_status.last_sync else None,
                    "skills": cache_status.skills,
                },
            }
            print(json.dumps(output, indent=2))
        else:
            print(f"Plugin: {plugin_name}")
            print(f"Version: {current_version}")
            print()
            print("Cache Status:")
            print(f"  Path: {cache_status.cache_path}")
            print(f"  Exists: {'Yes' if cache_status.exists else 'No'}")
            print(f"  Valid: {'Yes' if cache_status.is_valid else 'No'}")
            if cache_status.exists:
                print(f"  Files: {cache_status.file_count}")
                print(f"  Size: {cache_status.size_human}")
                if cache_status.last_sync:
                    print(f"  Last Sync: {cache_status.last_sync}")
                if cache_status.skills:
                    print(f"  Skills: {', '.join(cache_status.skills)}")

        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_validate(args: argparse.Namespace) -> int:
    """Execute validate command."""
    project_dir = get_project_dir()
    release = ReleaseCommands(project_dir)

    try:
        result = release.validate()

        if result.passed:
            print("Validation passed")
            for check_name, check_passed in result.checks.items():
                status = "OK" if check_passed else "FAIL"
                print(f"  [{status}] {check_name}")
            return 0
        else:
            print("Validation failed")
            for error in result.errors:
                print(f"  {error}")
            for warning in result.warnings:
                print(f"  [WARN] {warning}")
            if args.fix:
                print("\nAttempting auto-fix...")
                # Auto-fix logic would go here
            return 1 if args.strict or not result.passed else 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_version(args: argparse.Namespace) -> int:
    """Execute version command."""
    project_dir = get_project_dir()
    version_manager = VersionManager(project_dir)

    try:
        if args.subcommand == "bump":
            level = BumpLevel(args.level)
            current = version_manager.get_current_version()
            new_version = version_manager.bump(level, dry_run=args.dry_run)
            if args.dry_run:
                print(f"Would bump: {current} -> {new_version}")
            else:
                print(f"Version bumped: {current} -> {new_version}")
            return 0

        elif args.subcommand == "check":
            versions = version_manager.get_all_versions()
            try:
                consistent = version_manager.check_version_consistency()
                print(f"Versions consistent: {list(versions.values())[0]}")
                return 0
            except Exception:
                print("Versions inconsistent:")
                for file, ver in versions.items():
                    print(f"  {file}: {ver}")
                return 1

        else:
            # Default: show current version
            print(version_manager.get_current_version())
            return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_release(args: argparse.Namespace) -> int:
    """Execute release command."""
    project_dir = get_project_dir()
    release = ReleaseCommands(project_dir)

    def on_step(step, message):
        print(f"  [{step.value}] {message}")

    try:
        level_str = args.level if hasattr(args, "level") and args.level else "patch"
        level = BumpLevel(level_str)

        if args.resume:
            result = release.resume()
        else:
            print(f"Starting release ({level_str})...")
            result = release.release(
                bump_level=level,
                dry_run=args.dry_run,
                skip_tests=args.skip_tests,
                on_step=on_step,
            )

        if args.dry_run:
            print("\nDry run completed - no changes made")
            return 0

        if result.success:
            print(f"\nRelease successful: v{result.new_version}")
            return 0
        else:
            print(f"\nRelease failed at {result.failed_step}: {result.error}")
            return 1

    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_watch(args: argparse.Namespace) -> int:
    """Execute watch command."""
    project_dir = get_project_dir()
    cache_manager = CacheManager(project_dir)
    dev = DevCommands(project_dir, cache_manager)

    try:
        print("Starting watch mode...")
        print("Press Ctrl+C to stop")
        print()

        dev.watch(
            debounce_ms=args.debounce,
            initial_sync=not args.no_initial,
            background=args.background,
        )

        return 0

    except KeyboardInterrupt:
        print("\nWatch mode stopped")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="python -m cli.plugin",
        description="Plugin development CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # sync
    sync_parser = subparsers.add_parser("sync", help="Sync to cache")
    sync_parser.add_argument("-f", "--force", action="store_true", help="Force full sync")
    sync_parser.add_argument("-n", "--dry-run", action="store_true", help="Preview changes")
    sync_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    # watch
    watch_parser = subparsers.add_parser("watch", help="Watch mode")
    watch_parser.add_argument("--debounce", type=int, default=500, help="Debounce ms")
    watch_parser.add_argument("--no-initial", action="store_true", help="Skip initial sync")
    watch_parser.add_argument("--background", action="store_true", help="Run in background")

    # validate
    validate_parser = subparsers.add_parser("validate", help="Validate structure")
    validate_parser.add_argument("--strict", action="store_true", help="Strict mode")
    validate_parser.add_argument("--fix", action="store_true", help="Auto-fix issues")

    # status
    status_parser = subparsers.add_parser("status", help="Show status")
    status_parser.add_argument("--json", action="store_true", help="JSON output")

    # version
    version_parser = subparsers.add_parser("version", help="Version management")
    version_subparsers = version_parser.add_subparsers(dest="subcommand")

    bump_parser = version_subparsers.add_parser("bump", help="Bump version")
    bump_parser.add_argument("level", choices=["patch", "minor", "major"])
    bump_parser.add_argument("--dry-run", action="store_true")

    version_subparsers.add_parser("check", help="Check consistency")

    # release
    release_parser = subparsers.add_parser("release", help="Release workflow")
    release_parser.add_argument("level", nargs="?", default="patch",
                                choices=["patch", "minor", "major"])
    release_parser.add_argument("--dry-run", action="store_true", help="Preview release")
    release_parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    release_parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")
    release_parser.add_argument("--skip-tests", action="store_true", help="Skip tests")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    commands = {
        "sync": cmd_sync,
        "watch": cmd_watch,
        "validate": cmd_validate,
        "status": cmd_status,
        "version": cmd_version,
        "release": cmd_release,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
