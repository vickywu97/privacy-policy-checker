import unittest

from privacy_policy_checker.engine import load_checklists
from privacy_policy_checker.matcher import match, match_all

_DATA = "privacy_policy_checker/data"

_CP = {
    "id": "T-1",
    "law": "PIPL",
    "article": "17",
    "category": "告知义务",
    "checkpoint": "告知处理者联系方式",
    "criteria": "提供联系方式",
    "required_patterns": ["联系方式", "邮箱", "电话"],
    "context_patterns": ["客服"],
    "conditional_keywords": [],
    "risk_if_missing": "high",
}


class TestMatcher(unittest.TestCase):
    def test_satisfied(self):
        m = match(_CP, "本政策提供联系方式：邮箱 a@b.com".lower(), ["本政策提供联系方式：邮箱 a@b.com".lower()])
        self.assertEqual(m["status"], "satisfied")
        self.assertIsNotNone(m["evidence"])

    def test_partial_from_context(self):
        cp = dict(_CP, required_patterns=["xyz_nonexistent_xyz"])
        m = match(cp, "如有问题可联系客服".lower(), ["如有问题可联系客服".lower()])
        self.assertEqual(m["status"], "partial")

    def test_missing(self):
        cp = dict(_CP, required_patterns=["xyz_nonexistent_xyz"], context_patterns=["zzz_none"])
        m = match(cp, "hello world".lower(), ["hello world".lower()])
        self.assertEqual(m["status"], "missing")

    def test_not_applicable(self):
        cp = dict(_CP, conditional_keywords=["跨境", "境外"])
        m = match(cp, "我们是纯境内服务".lower(), ["我们是纯境内服务".lower()])
        self.assertEqual(m["status"], "not_applicable")


class TestNegationContext(unittest.TestCase):
    """回归测试：明示否定（不提供 / 不构成）应判 missing，而非乐观 partial。"""

    def _status(self, text, cp_id):
        cps = load_checklists(_DATA, ["PIPL", "GDPR", "CSL", "DSL"])
        cp = next(c for c in cps if c["id"] == cp_id)
        return match_all([cp], text)[0][1]["status"]

    def test_explicit_denial_data_portability_missing(self):
        # 「我们不提供…数据可携带的工具」应判 missing，而非 partial（此前因否定词距命中词 >12 字漏判）
        text = "我们不提供个人信息副本或数据可携带的工具。"
        self.assertEqual(self._status(text, "GDPR-20"), "missing")

    def test_explicit_denial_access_right_missing(self):
        # 「我们不会删除…也不提供删除渠道」应判 missing
        text = "我们不会删除您的个人信息，也不提供删除渠道。"
        self.assertEqual(self._status(text, "CSL-43"), "missing")

    def test_explicit_denial_deletion_missing(self):
        text = "我们不会删除您的个人信息，也不提供删除渠道。"
        self.assertEqual(self._status(text, "PIPL-47"), "missing")

    def test_cross_sentence_negation_not_killed(self):
        # 前句「不会出售」、后句「但您可删除」——删除权属不同句，不应被前句否定误伤
        text = "我们不会出售您的个人信息，但您可随时查询、更正或删除您的账户数据。您有权申请删除，我们提供专门的删除渠道。"
        self.assertEqual(self._status(text, "CSL-43"), "satisfied")
        self.assertEqual(self._status(text, "GDPR-17"), "satisfied")


if __name__ == "__main__":
    unittest.main()
