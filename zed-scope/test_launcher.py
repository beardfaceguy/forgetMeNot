"""Tests for the public Zed launch command. No real editor starts here."""
import contextlib
import io
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import launcher

from launcher import scope_command


class ScopeCommandTests(unittest.TestCase):
    def test_launch_uses_a_user_scope_and_forces_an_independent_editor(self):
        command = scope_command(Path("/opt/zed-dev/bin/zed"), ["--new", "/work/a project"], "app-forgetmenot-zed-example.scope")
        self.assertEqual(command, [
            "systemd-run", "--user", "--scope", "--collect", "--quiet",
            "--slice=app.slice", "--unit=app-forgetmenot-zed-example.scope",
            "--property=MemoryAccounting=yes", "--property=Delegate=yes",
            "--property=MemoryHigh=6G", "--property=MemoryMax=8G",
            "--property=MemorySwapMax=4G", "--",
            "/opt/zed-dev/bin/zed", "--foreground", "--new", "/work/a project",
        ])

    def test_existing_foreground_option_does_not_duplicate_the_flag(self):
        command = scope_command(Path("/opt/zed-dev/bin/zed"), ["--foreground", "--new"], "app-forgetmenot-zed-example.scope")
        self.assertEqual(command.count("--foreground"), 1)


class LauncherTests(unittest.TestCase):
    def test_version_passes_through_without_starting_a_scope(self):
        with mock.patch("subprocess.run", return_value=subprocess.CompletedProcess([], 0)) as run:
            self.assertEqual(launcher.main(["--version"]), 0)
        self.assertEqual(run.call_args.args[0], [str(Path.home() / ".local/zed-dev.app/bin/zed"), "--version"])

    def test_non_development_build_is_rejected_instead_of_reusing_an_editor(self):
        version = subprocess.CompletedProcess([], 0, stdout="Zed 1.0.0", stderr="")
        errors = io.StringIO()
        with mock.patch("subprocess.run", return_value=version), contextlib.redirect_stderr(errors):
            self.assertEqual(launcher.main(["/work/project"]), 1)
        self.assertIn("development build", errors.getvalue())

    def test_normal_launch_detaches_in_a_unique_scope_and_confirms_startup(self):
        version = subprocess.CompletedProcess([], 0, stdout="Zed dev test", stderr="")
        active = subprocess.CompletedProcess([], 0, stdout="active\n", stderr="")
        with tempfile.TemporaryDirectory() as home, \
                mock.patch("launcher.Path.home", return_value=Path(home)), \
                mock.patch("subprocess.run", side_effect=[version, active]) as run, \
                mock.patch("subprocess.Popen") as start, \
                contextlib.redirect_stdout(io.StringIO()):
            start.return_value.poll.return_value = None
            self.assertEqual(launcher.main(["--new", "/work/a project"]), 0)
            start.assert_called_once()
            command = start.call_args.args[0]
            self.assertIn("--scope", command)
            self.assertIn("--foreground", command)
            self.assertEqual(command[-2:], ["--new", "/work/a project"])
            unit = next(part.split("=", 1)[1] for part in command if part.startswith("--unit="))
            self.assertRegex(unit, r"^app-forgetmenot-zed-[0-9a-f]{32}\.scope$")
            self.assertEqual(run.call_args.args[0], ["systemctl", "--user", "show", unit, "-p", "ActiveState", "--value"])
            self.assertTrue(start.call_args.kwargs["start_new_session"])
            log = next((Path(home) / ".local/state/forgetmenot/zed-scopes").glob("*.log"))
            self.assertEqual(log.stat().st_mode & 0o777, 0o600)

    def test_editor_override_is_rejected_before_any_process_starts(self):
        for override in (["--zed", "/opt/other-zed"], ["--zed=/opt/other-zed"]):
            with self.subTest(override=override), tempfile.TemporaryDirectory() as home, \
                    mock.patch("launcher.Path.home", return_value=Path(home)), \
                    mock.patch("subprocess.run", return_value=subprocess.CompletedProcess([], 0, stdout="Zed dev test")) as run, \
                    mock.patch("subprocess.Popen") as start, \
                    contextlib.redirect_stderr(io.StringIO()):
                start.return_value.poll.return_value = 0
                self.assertEqual(launcher.main(override), 1)
                start.assert_not_called()
                run.assert_not_called()

    def test_failed_scope_start_never_falls_back_to_an_unscoped_editor(self):
        version = subprocess.CompletedProcess([], 0, stdout="Zed dev test", stderr="")
        with tempfile.TemporaryDirectory() as home, \
                mock.patch("launcher.Path.home", return_value=Path(home)), \
                mock.patch("subprocess.run", return_value=version) as run, \
                mock.patch("subprocess.Popen") as start, \
                contextlib.redirect_stderr(io.StringIO()):
            start.return_value.poll.return_value = 1
            self.assertEqual(launcher.main(["--new"]), 1)
            self.assertEqual(run.call_count, 1)
            start.assert_called_once()

    def test_wait_keeps_the_scoped_editor_attached_to_the_caller(self):
        version = subprocess.CompletedProcess([], 0, stdout="Zed dev test", stderr="")
        with mock.patch("subprocess.run", side_effect=[version, subprocess.CompletedProcess([], 0)]) as run, \
                mock.patch("subprocess.Popen") as start:
            self.assertEqual(launcher.main(["--wait", "/work/project"]), 0)
            start.assert_not_called()
            self.assertIn("--scope", run.call_args.args[0])
            self.assertEqual(run.call_args.args[0][-2:], ["--wait", "/work/project"])

    def test_missing_systemd_run_reports_failure_without_starting_an_unscoped_editor(self):
        version = subprocess.CompletedProcess([], 0, stdout="Zed dev test", stderr="")
        with tempfile.TemporaryDirectory() as home, \
                mock.patch("launcher.Path.home", return_value=Path(home)), \
                mock.patch("subprocess.run", return_value=version) as run, \
                mock.patch("subprocess.Popen", side_effect=FileNotFoundError("systemd-run")), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(launcher.main([]), 1)
            self.assertEqual(run.call_count, 1)


if __name__ == "__main__":
    unittest.main()
