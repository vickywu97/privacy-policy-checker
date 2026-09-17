import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from privacy_policy_checker import cli  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestFailOn(unittest.TestCase):
    def test_fail_on_high_triggers(self):
        path = os.path.join(ROOT, "demo", "sample_privacy_policy_bad.txt")
        self.assertEqual(cli.main(["--file", path, "--fail-on", "high"]), 1)

    def test_fail_on_high_passes_good(self):
        path = os.path.join(ROOT, "demo", "sample_privacy_policy.txt")
        self.assertEqual(cli.main(["--file", path, "--fail-on", "high"]), 0)

    def test_default_no_fail(self):
        path = os.path.join(ROOT, "demo", "sample_privacy_policy_bad.txt")
        self.assertEqual(cli.main(["--file", path]), 0)


if __name__ == "__main__":
    unittest.main()
