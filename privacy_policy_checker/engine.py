"""判定引擎：装载检查项、运行匹配、计算风险分级与汇总。

风险模型（四态 → 有效风险等级）：
- satisfied / not_applicable  → none
- missing                    → 取该检查项 risk_if_missing
- partial                    → 降一级（high→medium, medium→low, low→low）
"""

import json
import os

from .matcher import match_all

_RISK_ORDER = {"low": 1, "medium": 2, "high": 3, "none": 0}


def _downgrade(risk):
    return {"high": "medium", "medium": "low", "low": "low", "none": "none"}.get(risk, "none")


def _effective_risk(status, risk_if_missing):
    if status in ("satisfied", "not_applicable"):
        return "none"
    if status == "partial":
        return _downgrade(risk_if_missing)
    # missing
    return risk_if_missing


def _gap_description(cp, status):
    base = "【%s】%s" % (cp["law"], cp["article"])
    if status == "missing":
        return "%s 缺失：%s。要求：%s。" % (base, cp["checkpoint"], cp["criteria"])
    if status == "partial":
        return "%s 部分满足：%s。但要求：%s。" % (base, cp["checkpoint"], cp["criteria"])
    return None


def load_checklists(data_dir, laws):
    """装载指定法规的检查项库（JSONL），返回检查项 dict 列表。"""
    checkpoints = []
    for law in laws:
        fname = "checklist_%s.jsonl" % law.lower()
        path = os.path.join(data_dir, fname)
        if not os.path.exists(path):
            raise FileNotFoundError("检查项库不存在: %s（支持: PIPL, GDPR）" % path)
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                checkpoints.append(json.loads(line))
    return checkpoints


def analyze(text, checkpoints):
    """对隐私政策文本运行全部检查项，返回结构化结果。"""
    matched = match_all(checkpoints, text)
    results = []
    for cp, m in matched:
        risk = _effective_risk(m["status"], cp.get("risk_if_missing", "low"))
        results.append(
            {
                "id": cp["id"],
                "law": cp["law"],
                "article": cp["article"],
                "category": cp["category"],
                "checkpoint": cp["checkpoint"],
                "status": m["status"],
                "effective_risk": risk,
                "evidence": m["evidence"],
                "matched_pattern": m["matched_pattern"],
                "gap_description": _gap_description(cp, m["status"]),
                "law_text": cp.get("law_text", ""),
                "source_url": cp.get("source_url", ""),
                "source_accessed_at": cp.get("source_accessed_at", ""),
            }
        )
    summary = _summarize(results)
    return {"results": results, "summary": summary}


def _summarize(results):
    counts = {
        "satisfied": 0,
        "partial": 0,
        "missing": 0,
        "not_applicable": 0,
    }
    risk_counts = {"high": 0, "medium": 0, "low": 0, "none": 0}
    worst = "none"
    for r in results:
        counts[r["status"]] += 1
        risk_counts[r["effective_risk"]] += 1
        if _RISK_ORDER[r["effective_risk"]] > _RISK_ORDER[worst]:
            worst = r["effective_risk"]
    return {
        "total": len(results),
        "status": counts,
        "effective_risk": risk_counts,
        "overall_risk": worst,
    }
