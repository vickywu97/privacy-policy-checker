"""检查项匹配器：在隐私政策文本中检索某条检查项的证据。

设计原则（与 oss-license-checker 一致）：
- 零依赖、可复现：只用子串/关键词匹配，不做 LLM 判定，避免编造与漂移。
- 四态输出：satisfied / partial / missing / not_applicable。
- 不适用判定：带 conditional_keywords 的检查项，若全文均未出现相关语境词，
  判为 not_applicable（例如「跨境传输」对纯境内产品不适用），避免误报缺失。

判分改进（v2，针对纯关键词误判）：
1. 语境前置检查：conditional_keywords 未命中 → not_applicable。
2. 核心词 / 辅助词分离：
   - core_patterns（缺省回退 required_patterns）命中 → satisfied；
     证据取自真正含该词的段落，避免把「保存期限自动删除」误归为「删除权」。
   - aux_patterns（缺省回退 context_patterns）仅命中 → partial（低置信，需人工复核）。
3. 否定语境检测：命中词紧邻否定词（不/不会/not/...）时该次命中作废，
   继续寻找其他非否定出现；全为否定则视为未命中（避免「我们不提供 X」被误判为满足）。
4. 段落证据归因：返回第一个含非否定命中的段落（core 优先于 aux）。
"""

EVIDENCE_MAX_LEN = 220

# 否定标记：命中词前 NEG_WINDOW 字符内出现任一标记，视为否定语境。
NEGATION_MARKERS = [
    "不", "不能", "无法", "不会", "不支持", "暂不", "没有", "无", "未",
    "not ", "no ", "cannot", "can't", "do not", "does not", "won't",
    "fails to", "without ",
]
NEG_WINDOW = 12


def _hit_in_paragraph(para_lower, patterns):
    """在单段中找第一个命中模式，返回 (pattern, negated)；无则返回 (None, False)。"""
    for pat in patterns:
        pl = pat.lower()
        idx = para_lower.find(pl)
        if idx == -1:
            continue
        window = para_lower[max(0, idx - NEG_WINDOW):idx]
        negated = any(m in window for m in NEGATION_MARKERS)
        return pat, negated
    return None, False


def _find(patterns, paragraphs_lower):
    """在段落列表中找第一个含非否定命中的段落，返回 (pattern, idx) 或 (None, None)。"""
    if not patterns:
        return None, None
    for i, para in enumerate(paragraphs_lower):
        pat, negated = _hit_in_paragraph(para, patterns)
        if pat is not None and not negated:
            return pat, i
        # 本段命中但被否定 → 继续看其他段落是否还有正向命中
    return None, None


def _evidence(original_para, lower_para):
    txt = original_para if original_para is not None else lower_para
    if len(txt) > EVIDENCE_MAX_LEN:
        txt = txt[:EVIDENCE_MAX_LEN] + "…"
    return txt


def match(checkpoint, text_lower, paragraphs_lower, paragraphs_original=None):
    """对单条检查项做匹配，返回判定结果 dict。

    paragraphs_original 为可选的原始大小写段落列表；提供时证据保留原文大小写，
    否则回退到小写段落（保持与旧调用方兼容）。
    """
    if paragraphs_original is None:
        paragraphs_original = paragraphs_lower

    # (1) 语境前置检查
    conditional = checkpoint.get("conditional_keywords") or []
    if conditional and not any(k.lower() in text_lower for k in conditional):
        return {
            "status": "not_applicable",
            "evidence": None,
            "matched_pattern": None,
            "reason": "全文未出现相关语境（%s），该项不适用" % " / ".join(conditional[:3]),
        }

    # (2)(3) 核心词 / 辅助词
    core = checkpoint.get("core_patterns") or checkpoint.get("required_patterns") or []
    if "aux_patterns" in checkpoint:
        aux = checkpoint.get("aux_patterns") or []
    else:
        aux = checkpoint.get("context_patterns") or []

    cp, cidx = _find(core, paragraphs_lower)
    if cp is not None:
        return {
            "status": "satisfied",
            "evidence": _evidence(paragraphs_original[cidx], paragraphs_lower[cidx]),
            "matched_pattern": cp,
            "reason": None,
        }

    ap, aidx = _find(aux, paragraphs_lower)
    if ap is not None:
        return {
            "status": "partial",
            "evidence": _evidence(paragraphs_original[aidx], paragraphs_lower[aidx]),
            "matched_pattern": ap,
            "reason": "仅命中辅助词，未找到明确满足证据（低置信，建议人工复核）",
        }

    return {
        "status": "missing",
        "evidence": None,
        "matched_pattern": None,
        "reason": "未找到任何满足证据",
    }


def match_all(checkpoints, text):
    """对检查项列表批量匹配。text 为原始文本。"""
    paragraphs_original = [p for p in text.split("\n")]
    paragraphs_lower = [p.lower() for p in paragraphs_original]
    text_lower = "\n".join(paragraphs_lower)
    results = []
    for cp in checkpoints:
        m = match(cp, text_lower, paragraphs_lower, paragraphs_original)
        results.append((cp, m))
    return results
