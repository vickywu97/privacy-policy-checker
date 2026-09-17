"""命令行入口：隐私政策体检器。"""

import argparse
import os
import sys

from .engine import analyze, load_checklists
from .parsers.text import read_file
from .report import to_json, to_markdown


def build_parser():
    p = argparse.ArgumentParser(
        prog="privacy-policy-checker",
        description="离线隐私政策合规体检器：对照 PIPL / GDPR 逐条核验，输出缺口清单 + 风险分级 + 条文级证据。",
    )
    p.add_argument("--file", "-f", required=True, help="隐私政策文本文件路径（.txt/.md）")
    p.add_argument(
        "--laws",
        nargs="+",
        default=["PIPL", "GDPR"],
        choices=["PIPL", "GDPR"],
        help="适用的法规库，默认 PIPL GDPR",
    )
    p.add_argument(
        "--format",
        choices=["md", "json"],
        default="md",
        help="输出格式：md（法务版）或 json（工程版），默认 md",
    )
    p.add_argument("--project-name", default=None, help="项目名称（仅用于报告展示）")
    p.add_argument("-o", "--output", default=None, help="输出到文件（否则打印到 stdout）")
    p.add_argument("--fail-on", choices=["high", "medium", "low"], default=None,
                   help="CI 门禁：若存在有效风险等级>=该级别的检查项，以非零码退出（high/medium/low）")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    data_dir = os.path.join(os.path.dirname(__file__), "data")

    try:
        checkpoints = load_checklists(data_dir, args.laws)
    except FileNotFoundError as e:
        print("错误：%s" % e, file=sys.stderr)
        return 2

    text, err = read_file(args.file)
    if err:
        print("错误：无法读取文件 %s：%s" % (args.file, err), file=sys.stderr)
        return 2

    analysis = analyze(text, checkpoints)
    from datetime import datetime, timezone

    scanned_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    meta = {
        "file": args.project_name or os.path.basename(args.file),
        "laws": args.laws,
        "scanned_at": scanned_at,
    }

    out = to_markdown(analysis, meta) if args.format == "md" else to_json(analysis, meta)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
        print("报告已写入：%s" % args.output, file=sys.stderr)
    else:
        print(out)

    if args.fail_on:
        order = {"none": 0, "low": 1, "medium": 2, "high": 3}
        hits = [r for r in analysis["results"]
                if order.get(r["effective_risk"], 0) >= order[args.fail_on]]
        if hits:
            print("❌ CI 门禁未通过：%d 个检查项有效风险等级达到或超过 --fail-on=%s"
                  % (len(hits), args.fail_on), file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
