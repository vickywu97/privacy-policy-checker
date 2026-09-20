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

    def test_future_not_false_negation(self):
        # 「我们会在未来为您删除…」中的「未来」不得被裸「未」误判为否定语境
        # （与 token-classifier 抽取器一致性修复：排除「未来/未知/未必」等复合词）。
        text = "我们会在未来为您删除账户数据。"
        self.assertEqual(self._status(text, "CSL-43"), "satisfied")

    def test_genuine_wei_denial_still_negated(self):
        # 真正的「未提供」否定语气仍应判 missing（回归护栏，确保排除集不误伤真否定）。
        text = "我们暂不提供删除渠道，也未提供删除功能。"
        self.assertEqual(self._status(text, "CSL-43"), "missing")


class TestFinding1TopicTerms(unittest.TestCase):
    """Finding 1 (P0) 验证：aux 命中但同句无主题词 → 降级 missing；有主题词 → 保留 partial。

    被证实的 4 个 aux 过度宽泛错配检查项（CSL-21 / DSL-21a / DSL-21b / DSL-29a），
    修复后应全部由 partial 转为 missing。注意 DSL-29a 的 risk_if_missing=medium，
    故转为 missing(medium) 而非 high（审计报告此处曾误写为 high）。
    """

    def _status(self, text, cp_id):
        cps = load_checklists(_DATA, ["PIPL", "GDPR", "CSL", "DSL"])
        cp = next(c for c in cps if c["id"] == cp_id)
        return match_all([cp], text)[0][1]["status"]

    def test_csl21_downgraded_to_missing(self):
        # 「安全」仅命中在跨境「安全评估」句，无等保主题词 → 降级 missing（high）
        text = "如您身处境外，我们可能向境外接收方提供数据，并已通过国家网信部门组织的安全评估。"
        self.assertEqual(self._status(text, "CSL-21"), "missing")

    def test_dsl21a_downgraded_to_missing(self):
        # 「制度」仅命中在「访问管理制度」句，无分类分级主题词 → 降级 missing（high）
        text = "我们处理您的个人数据，并采取了加密、去标识化等安全技术措施及访问管理制度，保障个人信息安全。"
        self.assertEqual(self._status(text, "DSL-21a"), "missing")

    def test_dsl21b_downgraded_to_missing(self):
        # 「管理」仅命中在「访问管理制度」句，无数据安全负责人主题词 → 降级 missing（high）
        text = "我们处理个人数据，已建立访问管理制度以保障安全。"
        self.assertEqual(self._status(text, "DSL-21b"), "missing")

    def test_dsl29a_downgraded_to_missing_medium(self):
        # 「安全」仅命中在跨境「安全评估」句，无风险监测主题词 → 降级 missing（medium，非 high）
        text = "如您身处境外，我们可能向境外接收方提供数据，并已通过国家网信部门组织的安全评估。"
        self.assertEqual(self._status(text, "DSL-29a"), "missing")

    def test_topic_present_retains_partial(self):
        # 同句含主题词「等保」→ 保留 partial（不降级）
        cp = {
            "id": "T-TOPIC", "law": "PIPL", "article": "X", "category": "c",
            "checkpoint": "落实等保", "criteria": "c",
            "required_patterns": ["xyz_nonexistent_core"],
            "context_patterns": ["安全"],
            "topic_terms": ["等保", "等级保护"],
            "conditional_keywords": [],
            "risk_if_missing": "high",
        }
        text = "我们按照网络安全等级保护制度做好了安全防护工作".lower()
        m = match(cp, text, [text])
        self.assertEqual(m["status"], "partial")

    def test_topic_absent_downgrades_to_missing(self):
        # 同句无主题词「等保」→ 降级 missing
        cp = {
            "id": "T-NO", "law": "PIPL", "article": "X", "category": "c",
            "checkpoint": "落实等保", "criteria": "c",
            "required_patterns": ["xyz_nonexistent_core"],
            "context_patterns": ["安全"],
            "topic_terms": ["等保", "等级保护"],
            "conditional_keywords": [],
            "risk_if_missing": "high",
        }
        text = "我们已通过国家网信部门组织的安全评估".lower()
        m = match(cp, text, [text])
        self.assertEqual(m["status"], "missing")

    def test_no_topic_terms_backward_compatible(self):
        # 无 topic_terms 字段 → 维持原 partial 行为，不降级
        cp = dict(_CP, required_patterns=["xyz_nonexistent_xyz"])
        m = match(cp, "如有问题可联系客服".lower(), ["如有问题可联系客服".lower()])
        self.assertEqual(m["status"], "partial")


if __name__ == "__main__":
    unittest.main()
