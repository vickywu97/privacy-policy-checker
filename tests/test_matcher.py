import unittest

from privacy_policy_checker.matcher import match

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


if __name__ == "__main__":
    unittest.main()
