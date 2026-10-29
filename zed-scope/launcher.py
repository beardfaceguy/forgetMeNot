#!/usr/bin/env python3
"""Launch an independent Zed development instance in a systemd user scope.

Context: ../CONTEXT.md, isolated Zed launch. No local ADR governs this launcher.
"""
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path


def option_arguments(arguments: list[str]) -> list[str]:
    return arguments[:arguments.index("--")] if "--" in arguments else arguments


def scope_command(cli: Path, arguments: list[str], unit: str) -> list[str]:
    foreground = [] if "--foreground" in option_arguments(arguments) else ["--foreground"]
    return [
        "systemd-run", "--user", "--scope", "--collect", "--quiet",
        "--slice=app.slice", f"--unit={unit}",
        # The fork creates helper cgroups beneath its current application scope.
        "--property=MemoryAccounting=yes", "--property=Delegate=yes",
        # These temporary budgets follow user approval, not a measured peak guarantee.
        "--property=MemoryHigh=6G", "--property=MemoryMax=8G",
        "--property=MemorySwapMax=4G", "--",
        str(cli), *foreground, *arguments,
    ]


def launch_detached(command: list[str], unit: str) -> int:
    directory = Path.home() / ".local/state/forgetmenot/zed-scopes"
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    log_path = directory / f"{unit}.log"
    descriptor = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(descriptor, "a") as log:
        child = subprocess.Popen(
            command, stdin=subprocess.DEVNULL, stdout=log,
            stderr=subprocess.STDOUT, start_new_session=True,
        )
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if child.poll() is not None:
            print(f"zed-isolated did not remain running. See {log_path}", file=sys.stderr)
            return 1
        state = subprocess.run(
            ["systemctl", "--user", "show", unit, "-p", "ActiveState", "--value"],
            capture_output=True, text=True, timeout=2, check=False,
        )
        if state.returncode == 0 and state.stdout.strip() == "active":
            print(f"Zed scope: {unit}")
            return 0
        time.sleep(0.1)
    print(f"zed-isolated could not confirm startup. See {log_path}", file=sys.stderr)
    return 1


def main(arguments=None) -> int:
    arguments = list(sys.argv[1:] if arguments is None else arguments)
    cli = Path.home() / ".local/zed-dev.app/bin/zed"
    options = option_arguments(arguments)
    try:
        if any(flag in options for flag in ("--help", "-h", "--version", "-v", "--completions")):
            return subprocess.run([str(cli), *arguments], check=False).returncode
        if any(flag == "--zed" or flag.startswith("--zed=") for flag in options):
            print("zed-isolated does not support --zed overrides", file=sys.stderr)
            return 1
        version = subprocess.run(
            [str(cli), "--version"], capture_output=True, text=True, timeout=5, check=False,
        )
        # This inspected development build bypasses Zed's single-instance check.
        # Stable builds can exit or reuse another editor, outside the new scope.
        if version.returncode or not version.stdout.startswith("Zed dev "):
            print("zed-isolated requires the inspected Zed development build", file=sys.stderr)
            return 1
        unit = f"app-forgetmenot-zed-{uuid.uuid4().hex}.scope"
        command = scope_command(cli, arguments, unit)
        if any(flag in options for flag in ("--foreground", "--wait", "-w")):
            return subprocess.run(command, check=False).returncode
        return launch_detached(command, unit)
    except (OSError, subprocess.TimeoutExpired) as error:
        print(f"zed-isolated: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
