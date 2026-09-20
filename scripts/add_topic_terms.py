"""一次性脚本：为四个检查项库每条检查项补充 `topic_terms` 字段。

设计（对应诚实性审计 Finding 1 / P0）：
- 对 4 个被证实 aux 过度宽泛错配的检查项（CSL-21 / DSL-21a / DSL-21b / DSL-29a），
  写入**收窄到本检查项主题域**的 topic_terms：aux 命中必须出现在含这些主题词的同一句中，
  才保留 partial；否则降级为 missing。
- 其余条目：topic_terms 默认取自身 context_patterns（即 aux ⊆ context，
  aux 命中的句子必然含 context 词 = topic，因此不会触发降级，行为向后兼容）。

脚本以「在 `{"id": "X",` 之后插入一个字段」的方式做手术式改写，diff 仅新增一行字段，
不改动其余内容，便于审阅。

仅依赖标准库。
"""

import json
import os
import re

# 收窄到各检查项主题域的主题词（不含触发错配的泛型 aux 词本身）。
CURATED = {
    "CSL-21": ["等级保护", "等保", "网络安全等级保护", "网络安全防护", "安全保护义务"],
    "DSL-21a": ["分类分级", "数据分类", "分级保护", "重要数据", "分类", "分级"],
    "DSL-21b": ["重要数据", "数据安全负责人", "管理机构", "数据安全责任", "数据安全"],
    "DSL-29a": ["风险监测", "监测预警", "安全隐患", "监测机制", "风险", "监测"],
}

_FILES = [
    "checklist_pipl.jsonl",
    "checklist_gdpr.jsonl",
    "checklist_csl.jsonl",
    "checklist_dsl.jsonl",
]


def process_file(path):
    out = []
    n_curated = 0
    n_default = 0
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.strip():
            out.append(line)
            continue
        obj = json.loads(line)
        tid = obj["id"]
        if tid in CURATED:
            topic = CURATED[tid]
            n_curated += 1
        else:
            topic = obj.get("context_patterns") or []
            n_default += 1
        inj = '"topic_terms": %s, ' % json.dumps(topic, ensure_ascii=False)
        m = re.search(r'(\{"id": "[^"]+",)', line)
        if not m:
            raise RuntimeError("无法定位 id 字段: %s" % line[:40])
        newline = line[: m.end()] + " " + inj + line[m.end():]
        out.append(newline)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    return n_curated, n_default


def main():
    base = os.path.join(os.path.dirname(__file__), "..", "privacy_policy_checker", "data")
    base = os.path.abspath(base)
    for fn in _FILES:
        p = os.path.join(base, fn)
        cur, dflt = process_file(p)
        print("%s: curated=%d default=%d" % (fn, cur, dflt))


if __name__ == "__main__":
    main()
