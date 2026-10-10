# -*- coding: utf-8 -*-
import os
import unittest

os.environ.setdefault("AI_CANVAS_NO_REVEAL", "1")

from editor_app import CanvasAPI, BASE_DIR

class TestCanvasAPIDslIO(unittest.TestCase):
    def setUp(self):
        self.api = CanvasAPI()

    def test_save_dsl(self):
        sample_dsl = "clear\ncard: test [title=\"テスト思考\"]\n"
        res = self.api.save_dsl(sample_dsl)
        self.assertTrue(res.startswith("保存完了:"))
        
        # 保存されたファイルの存在確認
        filename = res.split("保存完了:")[1].strip()
        filepath = os.path.join(BASE_DIR, filename)
        self.assertTrue(os.path.exists(filepath))
        
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, sample_dsl)
        
        # テスト後クリーンアップ
        try:
            os.remove(filepath)
        except OSError:
            pass

    def test_open_dsl_file_method_exists(self):
        self.assertTrue(hasattr(self.api, "open_dsl_file"))

if __name__ == "__main__":
    unittest.main()
