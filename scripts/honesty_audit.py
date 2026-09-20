#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""跨项目诚实性审计工具（privacy-policy-checker 专用）。

审计目标：对匹配器的每一处「不猜 / 不判」叙事（not_applicable / partial / missing），
区分「真克制」（输入确实缺信息）与「能力缺口」（输入有可读信息但代码没覆盖）。

方法（与 oss-license-checker 审计一致，核心纪律：**逐字打印原始输入**，不凭记忆判断）：
1. 逐条取出检查项与判定结果；
2. 对原始隐私政策文本做「反向核验」：
   - not_applicable：逐字打印 conditional_keywords，确认全文是否真的无任何相关语境词；
   - partial：打印命中的 aux 证据段落（逐字），并反向扫描全文是否存在 core 词（若有则是能力缺口）；
   - missing：反向扫描全文是否存在 core / aux 词（若有则是误判 = 能力缺口）；同时检查该检查项是否对样例产品真适用；
3. 输出可直接贴入 docs/HONESTY_AUDIT.md 的核查明文。

用法（stdio）：
    python3 scripts/honesty_audit.py --policy <file.txt> [--laws PIPL GDPR CSL DSL]

也可作为库导入：from scripts.honesty_audit import run_audit
"""

import os
import re
import sys
import argparse

# 允许以脚本方式直接运行（将仓库根加入 sys.path）
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from privacy_policy_checker.engine import analyze, load_checklists  # noqa: E402


def _contains_any(text_lower, patterns):
    hits = []
    for pat in patterns:
        p = pat.lower()
        idx = text_lower.find(p)
        if idx != -1:
            hits.append((pat, idx))
    return hits


def _first_sentence_window(text, idx, window=160):
    """取命中位置附近的原始句子窗口，用于逐字展示证据。"""
    start = max(0, idx - 20)
    end = min(len(text), idx + window)
    return text[start:end].replace("\n", "↵")


def run_audit(policy_text, laws, label="policy"):
    """对给定政策文本运行审计，返回结构化核查明文（list[dict]）。"""
    data_dir = os.path.join(ROOT, "privacy_policy_checker", "data")
    checkpoints = load_checklists(data_dir, laws)
    analysis = analyze(policy_text, checkpoints)
    text_lower = policy_text.lower()
    paragraphs_original = [p for p in policy_text.split("\n")]

    findings = []
    for r in analysis["results"]:
        if r["status"] == "satisfied":
            continue
        cp = next(c for c in checkpoints if c["id"] == r["id"])
        conditional = cp.get("conditional_keywords") or []
        core = cp.get("core_patterns") or cp.get("required_patterns") or []
        aux = cp.get("aux_patterns") or cp.get("context_patterns") or []

        rec = {
            "label": label,
            "id": r["id"],
            "law": r["law"],
            "article": r["article"],
            "category": cp.get("category", ""),
            "checkpoint": cp.get("checkpoint", ""),
            "criteria": cp.get("criteria", ""),
            "status": r["status"],
            "effective_risk": r["effective_risk"],
            "risk_if_missing": cp.get("risk_if_missing", ""),
            "conditional_keywords": conditional,
            "core_patterns": core,
            "aux_patterns": aux,
            "matched_pattern": r["matched_pattern"],
            "evidence": r["evidence"],
            "gap_description": r.get("gap_description"),
            "law_text": cp.get("law_text", ""),
        }

        # —— 反向核验：输入里到底有没有这些词 ——
        # not_applicable：conditional 是否真的全部缺席
        if r["status"] == "not_applicable":
            cond_present = _contains_any(text_lower, conditional)
            rec["cond_present"] = cond_present
            rec["cond_all_absent"] = (len(cond_present) == 0)
        # partial / missing：core 是否真的全文缺席（若出席却没判满足，则属能力缺口）
        if r["status"] in ("partial", "missing"):
            core_present = _contains_any(text_lower, core)
            aux_present = _contains_any(text_lower, aux)
            rec["core_present_anywhere"] = core_present
            rec["aux_present_anywhere"] = aux_present
            rec["core_truly_absent"] = (len(core_present) == 0)
        findings.append(rec)
    return findings, analysis["summary"]


def fmt_finding(f):
    """把一个判定渲染成可贴入 HONESTY_AUDIT.md 的 markdown 块。"""
    lines = []
    lines.append("### 场景：privacy-policy-checker - %s（%s %s）" % (f["id"], f["law"], f["article"]))
    lines.append("")
    lines.append("- **检查项**：%s" % f["checkpoint"])
    lines.append("- **判定**：`%s`（有效风险 `%s`，risk_if_missing `%s`）" % (
        f["status"], f["effective_risk"], f["risk_if_missing"]))
    lines.append("- **检查项 criteria**：%s" % f["criteria"])
    lines.append("")

    if f["status"] == "not_applicable":
        lines.append("**原始输入 — conditional_keywords（逐字）**：")
        lines.append("```")
        lines.append(repr(f["conditional_keywords"]))
        lines.append("```")
        if f.get("cond_present"):
            present = ", ".join("%s@%d" % (p, i) for p, i in f["cond_present"])
            lines.append("")
            lines.append("⚠️ 反向核验：全文**实际命中** conditional 词 → `not_applicable` 判定**有误**（能力缺口）：%s" % present)
        else:
            lines.append("")
            lines.append("✅ 反向核验：全文确实无任何 conditional 词 → `not_applicable` 为真克制。")
        lines.append("")

    elif f["status"] in ("partial", "missing"):
        lines.append("**原始输入 — 已命中的证据（逐字）**：")
        lines.append("```")
        lines.append((f["evidence"] or "（无）"))
        lines.append("```")
        lines.append("")
        lines.append("**core_patterns（逐字）**：")
        lines.append("```")
        lines.append(repr(f["core_patterns"]))
        lines.append("```")
        lines.append("")
        if f.get("core_present_anywhere"):
            hits = "; ".join("%s@%d" % (p, i) for p, i in f["core_present_anywhere"])
            lines.append("⚠️ 反向核验：全文**另有** core 词命中 → `%s` 判定**可能有误**（能力缺口/排序 bug）：%s" % (f["status"], hits))
        else:
            lines.append("✅ 反向核验：全文确实无任何 core 词。")
        lines.append("")

    lines.append("**代码路径**：`privacy_policy_checker/matcher.py::match()`")
    lines.append("")
    lines.append("**判断**：")
    lines.append("- [ ] 真克制：输入中确实缺少所需信息")
    lines.append("- [ ] 能力缺口：输入中有 X 字段/特征句，但代码没读")
    lines.append("")
    lines.append("**如果能力缺口，修复方案**：（待定，先完成审计统一排序）")
    lines.append("")
    lines.append("**修复后覆盖率/判定影响**：（待量化）")
    lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", required=True, help="隐私政策文本文件")
    ap.add_argument("--laws", nargs="+", default=["PIPL", "GDPR", "CSL", "DSL"])
    ap.add_argument("--label", default=None, help="场景标签（如 english-only / good-sample）")
    args = ap.parse_args()

    with open(args.policy, "r", encoding="utf-8") as fh:
        text = fh.read()
    label = args.label or os.path.basename(args.policy)
    findings, summary = run_audit(text, args.laws, label=label)

    print("# 诚实性审计 · 反向核验转储")
    print("")
    print("**场景标签**：%s" % label)
    print("**适用法规**：%s" % " ".join(args.laws))
    print("**汇总**：%s" % summary)
    print("")
    print("> 说明：本转储由 scripts/honesty_audit.py 自动生成，逐字打印原始输入，"
          "供人工判读「真克制 vs 能力缺口」。判定结论由人工在 HONESTY_AUDIT.md 填写。")
    print("")
    for f in findings:
        print(fmt_finding(f))


if __name__ == "__main__":
    main()
