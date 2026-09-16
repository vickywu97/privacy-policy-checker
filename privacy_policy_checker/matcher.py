"""检查项匹配器：在隐私政策文本中检索某条检查项的证据。

设计原则（与 oss-license-checker 一致）：
- 零依赖、可复现：只用子串/关键词匹配，不做 LLM 判定，避免编造与漂移。
- 四态输出：satisfied / partial / missing / not_applicable。
- 不适用判定：带 conditional_keywords 的检查项，若全文均未出现相关语境词，
  判为 not_applicable（例如「跨境传输」对纯境内产品不适用），避免误报缺失。
"""

EVIDENCE_MAX_LEN = 160


def _snippet(text_lower, paragraphs_lower):
    """返回包含 text_lower 的第一个段落片段（截断）。"""
    for para in paragraphs_lower:
        if text_lower in para:
            snippet = para
            if len(snippet) > EVIDENCE_MAX_LEN:
                snippet = snippet[:EVIDENCE_MAX_LEN] + "…"
            return snippet
    return None


def match(checkpoint, text_lower, paragraphs_lower):
    """对单条检查项做匹配，返回判定结果 dict。"""
    conditional = checkpoint.get("conditional_keywords") or []
    if conditional:
        if not any(k.lower() in text_lower for k in conditional):
            return {
                "status": "not_applicable",
                "evidence": None,
                "matched_pattern": None,
                "reason": "全文未出现相关语境（%s），该项不适用" % " / ".join(conditional[:3]),
            }

    required = checkpoint.get("required_patterns") or []
    for pat in required:
        pl = pat.lower()
        if pl in text_lower:
            return {
                "status": "satisfied",
                "evidence": _snippet(pl, paragraphs_lower),
                "matched_pattern": pat,
                "reason": None,
            }

    context = checkpoint.get("context_patterns") or []
    for pat in context:
        pl = pat.lower()
        if pl in text_lower:
            return {
                "status": "partial",
                "evidence": _snippet(pl, paragraphs_lower),
                "matched_pattern": pat,
                "reason": "仅命中辅助词，未找到明确满足证据",
            }

    return {
        "status": "missing",
        "evidence": None,
        "matched_pattern": None,
        "reason": "未找到任何满足证据",
    }


def match_all(checkpoints, text):
    """对检查项列表批量匹配。text 为原始文本。"""
    text_lower = text.lower()
    paragraphs_lower = [p.lower() for p in text.split("\n")]
    results = []
    for cp in checkpoints:
        m = match(cp, text_lower, paragraphs_lower)
        results.append((cp, m))
    return results
