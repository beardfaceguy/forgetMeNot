import unittest

from monitor import application_tree_totals


class ApplicationTreeTests(unittest.TestCase):
    def test_separate_editors_include_nested_helpers_and_game_has_its_own_total(self):
        # Independent fixture: RSS and swap values use KiB.
        processes = [
            (110, 100, "1", "zed-editor", 100, 10, "desktop"),
            (220, 101, "100", "codex", 200, 20, "desktop"),
            (330, 102, "101", "repowise", 300, 30, "desktop"),
            (440, 200, "1", "zed-editor", 400, 40, "desktop"),
            (550, 300, "1", "steam", 500, 50, "desktop"),
            (660, 301, "300", "Outbound.exe", 600, 60, "desktop"),
            (770, 302, "301", "game-helper", 700, 70, "desktop"),
            (880, 400, "999", "orphan-helper", 800, 80, "desktop"),
        ]
        self.assertEqual(
            application_tree_totals(processes),
            {
                (100, "zed-editor"): [3, 600, 60],
                (200, "zed-editor"): [1, 400, 40],
                (300, "steam"): [1, 500, 50],
                (301, "Outbound.exe"): [2, 1300, 130],
            },
        )


if __name__ == "__main__":
    unittest.main()
