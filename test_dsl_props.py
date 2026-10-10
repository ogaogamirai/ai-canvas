# -*- coding: utf-8 -*-
"""DSL プロパティ編集ヘルパー（setQuotedProp / setLineProp）の回帰テスト。node があれば実行。"""
import os
import shutil
import subprocess
import unittest

BASE = os.path.dirname(os.path.abspath(__file__))


class TestDslProps(unittest.TestCase):
    def test_prop_helpers(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node not available")
        script = os.path.join(BASE, "tools", "check_dsl_props.mjs")
        r = subprocess.run([node, script], capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0, (r.stdout or "") + (r.stderr or ""))


if __name__ == "__main__":
    unittest.main()
