# -*- coding: utf-8 -*-
"""autoLayout のサイクル安全（閉路でフリーズしない）検証。node があれば実行。"""
import os
import shutil
import subprocess
import unittest

BASE = os.path.dirname(os.path.abspath(__file__))


class TestAutoLayoutCycle(unittest.TestCase):
    def test_autolayout_is_cycle_safe(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node not available")
        script = os.path.join(BASE, "tools", "check_autolayout_cycle.mjs")
        r = subprocess.run([node, script], capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0, (r.stdout or "") + (r.stderr or ""))


if __name__ == "__main__":
    unittest.main()
