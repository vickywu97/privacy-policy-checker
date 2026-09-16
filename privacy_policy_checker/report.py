"""报告生成器：法务版（Markdown）+ 工程版（JSON）。"""

import json
from datetime import datetime, timezone

DISCLAIMER = (
    "本报告由隐私政策体检器自动生成，仅用于合规自查与缺口梳理，"
    "不构成法律意见。最终合规判断请咨询执业律师。"
)

_RISK_ICON = {"high": "🔴", "medium": "🟡", "low": "🟢", "none": "⚪"}
_STATUS_CN = {
    "satisfied": "✅ 满足",
    "partial": "⚠️ 部分满足",
    "missing": "❌ 缺失",
    "not_applicable": "— 不适用",
}


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def to_markdown(analysis, meta):
    s = analysis["summary"]
    lines = []
    lines.append("# 隐私政策合规体检报告")
    lines.append("")
    lines.append("**被检查文件**：%s" % meta.get("file", "-"))
    lines.append("**适用法规**：%s" % " + ".join(meta.get("laws", [])))
    lines.append("**扫描时间**：%s" % meta.get("scanned_at", _now()))
    lines.append(
        "**检查项总数**：%d（满足 %d · 部分 %d · 缺失 %d · 不适用 %d）"
        % (
            s["total"],
            s["status"]["satisfied"],
            s["status"]["partial"],
            s["status"]["missing"],
            s["status"]["not_applicable"],
        )
    )
    lines.append(
        "**有效风险统计**：%s 高 %d · %s 中 %d · %s 低 %d"
        % (
            _RISK_ICON["high"], s["effective_risk"]["high"],
            _RISK_ICON["medium"], s["effective_risk"]["medium"],
            _RISK_ICON["low"], s["effective_risk"]["low"],
        )
    )
    lines.append("**整体风险等级**：%s" % _RISK_ICON[s["overall_risk"]])
    lines.append("")

    for risk in ("high", "medium", "low"):
        items = [r for r in analysis["results"] if r["effective_risk"] == risk]
        if not items:
            continue
        label = {"high": "高风险缺口（需立即处理）", "medium": "中风险缺口（需评估）", "low": "低风险提示"}[risk]
        lines.append("## %s" % label)
        lines.append("")
        for r in items:
            lines.append("### %s %s" % (_RISK_ICON[risk], r["checkpoint"]))
            lines.append("- **检查项编号**：%s（%s 第 %s 条）" % (r["id"], r["law"], r["article"]))
            lines.append("- **判定**：%s" % _STATUS_CN[r["status"]])
            if r["evidence"]:
                lines.append("- **命中证据**：%s" % r["evidence"])
            else:
                lines.append("- **命中证据**：未找到")
            if r["gap_description"]:
                lines.append("- **整改建议**：%s" % r["gap_description"])
            lines.append("- **法条依据**：%s" % r["law_text"])
            if r["source_url"]:
                lines.append("- **来源**：%s（核验于 %s）" % (r["source_url"], r["source_accessed_at"]))
            lines.append("")

    lines.append("## 已满足 / 不适用项（%d 项）" % (s["status"]["satisfied"] + s["status"]["not_applicable"]))
    lines.append("")
    for r in analysis["results"]:
        if r["effective_risk"] == "none":
            lines.append("- %s %s（%s）" % (_STATUS_CN[r["status"]], r["checkpoint"], r["id"]))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 免责声明")
    lines.append("")
    lines.append(DISCLAIMER)
    return "\n".join(lines)


def to_json(analysis, meta):
    return json.dumps(
        {
            "file": meta.get("file", "-"),
            "laws": meta.get("laws", []),
            "scanned_at": meta.get("scanned_at", _now()),
            "summary": analysis["summary"],
            "checkpoints": analysis["results"],
            "disclaimer": DISCLAIMER,
        },
        ensure_ascii=False,
        indent=2,
    )
