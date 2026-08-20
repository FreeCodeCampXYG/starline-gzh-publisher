import json
import tempfile
import unittest
from pathlib import Path

from build_site import build


class BuildSiteTests(unittest.TestCase):
    def test_builds_catalog_and_views(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content = root / "content"
            content.mkdir()
            (content / "one.md").write_text(
                "---\ntitle: One\nslug: one\ntype: study-note\ntags: a,b\nsummary: test\n---\n# One\n\n## Core\n\nHello.",
                encoding="utf-8",
            )
            out = root / "site"
            build(type("Args", (), {"content": str(content), "output": str(out)})())
            records = json.loads((out / "index.json").read_text(encoding="utf-8"))
            self.assertEqual(records[0]["type"], "study-note")
            self.assertEqual(records[0]["tags"], ["a", "b"])
            index = (out / "index.html").read_text(encoding="utf-8")
            self.assertIn("Source / 编辑源文", index)
            self.assertIn("复制公众号 HTML", index)
            self.assertIn("实时预览", index)
            self.assertTrue((out / "articles" / "one" / "wechat.html").exists())


if __name__ == "__main__":
    unittest.main()
