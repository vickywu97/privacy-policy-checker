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

    def test_gdpr17_request_deletion_satisfied(self):
        # 回归：GDPR-17 应命中"有权请求删除"段，而非保存期限段的自动删除
        cps = load_checklists(_DATA, ["GDPR"])
        res = analyze(_GOOD, cps)
        r = [x for x in res["results"] if x["id"] == "GDPR-17"][0]
        self.assertEqual(r["status"], "satisfied")
        self.assertIn("请求删除", r["evidence"])

    def test_gdpr49_no_derogations_missing(self):
        # 回归：样例援引 SCC（Art 46）而非 Art 49 减损条款 → 应缺失，不应误判 partial
        cps = load_checklists(_DATA, ["GDPR"])
        res = analyze(_GOOD, cps)
        r = [x for x in res["results"] if x["id"] == "GDPR-49"][0]
        self.assertEqual(r["status"], "missing")

    def test_auto_deletion_not_erasure_right(self):
        # 仅含"保存期限到期后删除"的自动删除、不含主动删除权 → GDPR-17 不得判 satisfied
        text = "我们对个人信息的保存期限为 3 年，到期后我们将删除或匿名化处理。"
        cps = load_checklists(_DATA, ["GDPR"])
        res = analyze(text, cps)
        r = [x for x in res["results"] if x["id"] == "GDPR-17"][0]
        self.assertNotEqual(r["status"], "satisfied")

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
