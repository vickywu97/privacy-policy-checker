import os
import unittest

from privacy_policy_checker.engine import analyze, load_checklists

_DATA = os.path.join(os.path.dirname(__file__), "..", "privacy_policy_checker", "data")
_DEMO = os.path.join(os.path.dirname(__file__), "..", "demo", "sample_privacy_policy.txt")

_GOOD = open(_DEMO, encoding="utf-8").read()

_BAD = "我们使用您的手机号来推广告。"


class TestEngine(unittest.TestCase):
    def test_load_both(self):
        cps = load_checklists(_DATA, ["PIPL", "GDPR"])
        self.assertGreaterEqual(len(cps), 70)

    def test_good_most_satisfied(self):
        cps = load_checklists(_DATA, ["PIPL", "GDPR"])
        res = analyze(_GOOD, cps)
        self.assertGreater(res["summary"]["status"]["satisfied"], 20)
        # 合规版不应有高风险缺口（允许 medium 项如"公平透明原则"存在）
        self.assertEqual(res["summary"]["effective_risk"]["high"], 0)

    def test_bad_has_high_gaps(self):
        cps = load_checklists(_DATA, ["PIPL", "GDPR"])
        res = analyze(_BAD, cps)
        self.assertGreater(res["summary"]["effective_risk"]["high"], 0)
        self.assertNotEqual(res["summary"]["overall_risk"], "none")

    def test_partial_downgrades_risk(self):
        # 用一段只命中辅助词的文本，验证 partial 使 high->medium
        cp = {
            "id": "X", "law": "PIPL", "article": "17", "category": "c",
            "checkpoint": "c", "criteria": "c",
            "required_patterns": ["不存在的关键词"], "context_patterns": ["手机号"],
            "conditional_keywords": [], "risk_if_missing": "high",
        }
        res = analyze("我们使用您的手机号来推广告。", [cp])
        self.assertEqual(res["results"][0]["status"], "partial")
        self.assertEqual(res["results"][0]["effective_risk"], "medium")


if __name__ == "__main__":
    unittest.main()
