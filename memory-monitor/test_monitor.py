import unittest

from monitor import application_tree_totals, top_applications


class ApplicationTreeTests(unittest.TestCase):
    def test_top_applications_merge_instances_and_their_helpers(self):
        processes = [
            (100, 10, "1", "zed-editor", 100, 0, "desktop"),
            (300, 11, "10", "language-server", 300, 0, "desktop"),
            (200, 20, "1", "zed-editor", 200, 0, "desktop"),
            (500, 30, "1", "chrome", 500, 0, "desktop"),
            (400, 31, "30", "renderer", 400, 0, "desktop"),
            (800, 40, "1", "Outbound.exe", 800, 0, "desktop"),
        ]
        self.assertEqual(top_applications(processes), [("Chrome", 900), ("Outbound", 800), ("Zed", 600)])

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
