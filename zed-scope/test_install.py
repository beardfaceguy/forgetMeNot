"""Install behavior against synthetic home directories only."""
import tempfile
import unittest
from pathlib import Path

import install


class InstallTests(unittest.TestCase):
    def test_install_preserves_backups_and_routes_terminal_and_desktop_launches(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            cli = home / ".local/zed-dev.app/bin/zed"
            cli.parent.mkdir(parents=True)
            cli.touch()
            link = home / ".local/bin/zed"
            link.parent.mkdir(parents=True)
            link.symlink_to(cli)
            desktop = home / ".local/share/applications/dev.zed.Zed-Dev.desktop"
            desktop.parent.mkdir(parents=True)
            original = f"[Desktop Entry]\nTryExec={cli}\nExec={cli} %U\n\n[Desktop Action NewWorkspace]\nExec={cli} --new %U\n"
            desktop.write_text(original)
            install.install(home)
            wrapper = home / ".local/bin/zed-isolated"
            self.assertEqual(link.resolve(), wrapper)
            self.assertTrue(wrapper.stat().st_mode & 0o111)
            self.assertEqual(desktop.read_text(), original.replace(str(cli), str(wrapper)))
            backup = home / ".local/state/forgetmenot/zed-launch-backup"
            self.assertEqual((backup / "zed").readlink(), cli)
            self.assertEqual((backup / desktop.name).read_text(), original)
            install.install(home)
            self.assertEqual((backup / desktop.name).read_text(), original)

    def test_restore_returns_terminal_and_desktop_launches_to_the_original_bundle(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            cli = home / ".local/zed-dev.app/bin/zed"
            cli.parent.mkdir(parents=True)
            cli.touch()
            link = home / ".local/bin/zed"
            link.parent.mkdir(parents=True)
            link.symlink_to(cli)
            desktop = home / ".local/share/applications/dev.zed.Zed-Dev.desktop"
            desktop.parent.mkdir(parents=True)
            original = f"[Desktop Entry]\nTryExec={cli}\nExec={cli} %U\n"
            desktop.write_text(original)
            install.install(home)
            install.restore(home)
            self.assertEqual(link.readlink(), cli)
            self.assertEqual(desktop.read_text(), original)


if __name__ == "__main__":
    unittest.main()
