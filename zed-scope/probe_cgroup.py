#!/usr/bin/env python3
"""Verify nested helper membership inside a disposable delegated user scope.

Context: ../CONTEXT.md, isolated Zed launch. This probe never targets an editor.
"""
import json
import subprocess
import uuid
from pathlib import Path


def membership(pid: str) -> str:
    lines = (Path("/proc") / pid / "cgroup").read_text().splitlines()
    return next(line.split("::", 1)[1] for line in lines if line.startswith("0::"))


def main() -> None:
    parent = membership("self")
    directory = Path("/sys/fs/cgroup") / parent.lstrip("/")
    if not directory.name.startswith("app-forgetmenot-probe-"):
        raise SystemExit("Run this probe only inside a disposable app-forgetmenot-probe- scope")
    nested = directory / f"helper-{uuid.uuid4().hex}"
    nested.mkdir()
    helper = None
    try:
        helper = subprocess.Popen(["/usr/bin/sleep", "30"])
        inherited = membership(str(helper.pid))
        if inherited != parent:
            raise RuntimeError("The helper did not inherit the application scope")
        (nested / "cgroup.procs").write_text(str(helper.pid))
        migrated = membership(str(helper.pid))
        if migrated != f"{parent}/{nested.name}":
            raise RuntimeError("The helper did not enter the nested cgroup")
        limits = {name: (directory / name).read_text().strip() for name in ("memory.high", "memory.max", "memory.swap.max")}
        print(json.dumps({"parent": parent, "inherited": inherited, "nested": migrated, "limits": limits, "passed": True}))
    finally:
        if helper is not None:
            helper.terminate()
            helper.wait(timeout=5)
        nested.rmdir()


if __name__ == "__main__":
    main()
