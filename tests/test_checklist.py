import json
import os
import unittest

_DATA = os.path.join(os.path.dirname(__file__), "..", "privacy_policy_checker", "data")

_REQUIRED = {
    "id", "law", "article", "category", "checkpoint", "criteria",
    "required_patterns", "conditional_keywords", "risk_if_missing",
    "law_text", "source_url", "source_accessed_at",
}


class TestChecklistIntegrity(unittest.TestCase):
    def test_pipl_valid(self):
        path = os.path.join(_DATA, "checklist_pipl.jsonl")
        n = 0
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                self.assertTrue(_REQUIRED.issubset(obj.keys()), "缺字段: %s" % obj.get("id"))
                self.assertIn(obj["risk_if_missing"], ("high", "medium", "low"))
                n += 1
        self.assertGreaterEqual(n, 30)

    def test_gdpr_valid(self):
        path = os.path.join(_DATA, "checklist_gdpr.jsonl")
        n = 0
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                self.assertTrue(_REQUIRED.issubset(obj.keys()), "缺字段: %s" % obj.get("id"))
                self.assertIn(obj["risk_if_missing"], ("high", "medium", "low"))
                n += 1
        self.assertGreaterEqual(n, 40)

    def test_csl_valid(self):
        path = os.path.join(_DATA, "checklist_csl.jsonl")
        n = 0
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                self.assertTrue(_REQUIRED.issubset(obj.keys()), "缺字段: %s" % obj.get("id"))
                self.assertIn(obj["risk_if_missing"], ("high", "medium", "low"))
                n += 1
        self.assertGreaterEqual(n, 6)

    def test_dsl_valid(self):
        path = os.path.join(_DATA, "checklist_dsl.jsonl")
        n = 0
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                self.assertTrue(_REQUIRED.issubset(obj.keys()), "缺字段: %s" % obj.get("id"))
                self.assertIn(obj["risk_if_missing"], ("high", "medium", "low"))
                n += 1
        self.assertGreaterEqual(n, 6)

    def test_ids_unique(self):
        ids = []
        for fname in ("checklist_pipl.jsonl", "checklist_gdpr.jsonl",
                      "checklist_csl.jsonl", "checklist_dsl.jsonl"):
            with open(os.path.join(_DATA, fname), encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        ids.append(json.loads(line)["id"])
        self.assertEqual(len(ids), len(set(ids)), "检查项 id 存在重复")


if __name__ == "__main__":
    unittest.main()
