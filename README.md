# privacy-policy-checker

[![CI](https://github.com/vickywu97/privacy-policy-checker/actions/workflows/ci.yml/badge.svg)](https://github.com/vickywu97/privacy-policy-checker/actions/workflows/ci.yml)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **语言支持状态（英文）**：当前检查项库以中文关键词为主。英文覆盖统计（共 87 条检查项）：含英文 `required_patterns` 的有 **45 条（51.7%）**，但分布极不均——**GDPR 40/40 已系统性含英文同义词**，**PIPL 仅 5/31、CSL 0/8、DSL 0/8 几乎无英文**。因此**纯英文隐私政策易产生假阴性**：PIPL / CSL / DSL 相关合规章节可能被误判为 `not_applicable` 或 `missing`（属「能力缺口」，非保守克制）。完整英文支持（补齐中文法条的英文同义词）列入 **Phase 2 路线图**。可复现验证见 `demo/sample_privacy_policy_en.txt` 与 `docs/HONESTY_AUDIT.md §4（英文隐私政策能力缺口）`。

**离线隐私政策合规体检器** —— 输入一段隐私政策文本，对照 PIPL（个人信息保护法）、GDPR、网络安全法（CSL）、数据安全法（DSL）的检查项库逐条核验，输出缺口清单 + 风险分级 + 条文级证据。

> 一句话定位：律师与合规团队之间的「隐私政策翻译器」。通用 AI 会编造法条（已被 `legal-hallucination-bench` 证明不可靠），这个工具只用确定的关键词匹配 + 法条原文，零 LLM 依赖、离线、可复现。

---

## 为什么需要它

每个 App / 网站 / SaaS 都必须有隐私政策，但绝大多数存在合规缺口：

- **告知义务不全**：未告知处理者身份、目的、保存期限、权利行使方式
- **单独同意缺失**：敏感个人信息、跨境传输、第三方共享未单独同意
- **用户权利缺失**：未告知查阅、复制、更正、删除、可携带权
- **跨境传输未说明**：未披露境外接收方与保障措施

后果：PIPL 罚款可达上年营收 5%，GDPR 可达全球营收 4% 或 2000 万欧元，并可能下架 / 融资受阻。

---

## 安装与使用

零第三方依赖，仅用 Python 标准库。需 Python 3.8+。

```
# 直接以模块方式运行
python -m privacy_policy_checker --file path/to/privacy_policy.txt

# 仅查 PIPL
python -m privacy_policy_checker --file policy.txt --laws PIPL

# 中国数据三法 + 欧盟 GDPR 全面体检（含网络安全法 / 数据安全法）
python -m privacy_policy_checker --file policy.txt --laws PIPL GDPR CSL DSL

# 输出工程版 JSON
python -m privacy_policy_checker --file policy.txt --format json -o report.json
```

参数说明：

| 参数 | 说明 |
|------|------|
| `--file` / `-f` | 隐私政策文本路径（必填） |
| `--laws` | 法规库，默认 `PIPL GDPR`；可追加 `CSL`（网络安全法）/ `DSL`（数据安全法）做更全面的数据合规体检 |
| `--format` | `md`（法务版 Markdown，默认）或 `json`（工程版） |
| `--project-name` | 报告中的项目名展示 |
| `-o` / `--output` | 输出到文件，否则打印到 stdout |

---

## 判定模型

每个检查项返回四态之一：

- **satisfied（满足）**：找到明确证据关键词
- **partial（部分满足）**：仅命中辅助词，未找到明确证据
- **missing（缺失）**：未找到任何证据
- **not_applicable（不适用）**：带语境条件的检查项（如「跨境传输」）在全文无相关语境时自动判为不适用，避免误报

风险分级：检查项的 `risk_if_missing` 为「缺失时风险」，partial 自动降一级（high→medium），satisfied / NA 不计入风险。

---

## 检查项库

| 法规 | 检查项数 | 覆盖 |
|------|---------|------|
| PIPL | 31 | 告知义务（第17条）、第三方共享（23）、自动化决策（24）、敏感个人信息（29-30）、未成年人（31）、跨境（38-39）、个人权利（44-50）、安全措施（51）、影响评估（55）、泄露通知（57）、定期审计（54）、法律责任（66） |
| GDPR | 40 | 处理原则（5）、合法性基础（6-7,9）、透明义务（12-14）、告知义务（13-14）、数据主体权利（15-22）、安全（32）、泄露（33-34）、DPIA（35）、DPO（37）、跨境（44-49）、投诉与罚款（77,83） |
| 网络安全法 CSL | 8 | 网络实名制（24）、等级保护（21）、收集使用合法正当必要（41）、信息保护义务与泄露补救（42）、境内存储/数据本地化（37）、查询更正删除权（43）、应急预案（25）、公开规则（22） |
| 数据安全法 DSL | 8 | 数据分类分级（21）、重要数据管理责任（21/27）、风险监测（29）、数据安全事件应急（29）、重要数据出境安全评估（31）、收集合法性（32）、数据交易中介义务（33）、政务数据受托监督（38-40） |

> CSL / DSL 多涉及**组织级安全义务**（如等级保护、分类分级、数据交易），通常需对照企业安全合规台账（而非仅隐私政策文本）核验；默认 `--laws` 不含二者，按需用 `--laws CSL DSL` 开启。

每条检查项均附 **法条原文 + 来源 URL + 核验日期**，可追溯、可审计。

---

## 法律边界

本报告为自动化合规检查工具输出，用于自查与缺口梳理，**不构成法律意见**。最终合规判断请咨询执业律师。

---

## 已知缺口（Known Gaps）

本工具为求职作品集，非商用产品。诚实性审计记录于 [`docs/HONESTY_AUDIT.md`](docs/HONESTY_AUDIT.md)：共 **5 项**缺口记录；另有 **2 类**经逐条核验确认为**真克制**（不是缺口）。

**第 1 项（项目级局限）**：**当前无真实案例回归** —— 审计使用的两份样例政策（`demo/sample_privacy_policy.txt`、`demo/sample_privacy_policy_en.txt`）**均为构造性文本**（后者为刻意构造的「完全合规」英文政策）。构造性验证只能证明「代码在特定输入下行为正确」，**不能**证明在真实世界政策下正确。

**状态三分**：

| 状态 | 数量 | 说明 |
|------|------|------|
| ✅ 已修复 | **2 项** | ① `partial` 证据错配 4 例（CSL-21 / DSL-21a / 21b / 29a）；② section-aware 修复 C1 / C1b / C2 假阴性回归 |
| 🔒 已测试锁定（`expectedFailure`） | **0 项** | 本仓未用 xFail 锁定缺口；缺口由 `scripts/honesty_audit.py` 复现 |
| 📝 仅记录（无测试） | **3 项** | ① 英文同义词缺口（P0）；② 21 条含泛型原子的检查项（Phase 2 backlog）；③ `conditional` 门禁与 core 一致性 |

> 另有 2 类经逐条核验确认为**真克制**（非缺口）：中文政策 11 条 `not_applicable`（`conditional_keywords` 确无命中）、DSL-29b `missing(high)`（政策确未提及应急预案）。

**修复路线图**：

| 优先级 | 项 | 时间承诺 |
|--------|-----|---------|
| **Phase 1（高）** | 英文同义词缺口 —— 为 87 条检查项补齐英文 `conditional_keywords` / `required_patterns`（当前一份**完全合规**的英文政策被判出 12 个 high） | 下个 release 前 |
| **Phase 2（中）** | 21 条含泛型原子（「安全」「管理」「同意」「收集」等）的检查项逐条收窄 | 后续 |
| **Phase 3（设计复核）** | `conditional` 门禁与 core 一致性；为中国法专有条目增加 `applicability_hint` | 长期 |
| **不承诺修复** | 11 条中文 `not_applicable`、DSL-29b —— 经核验为真克制，非缺口 | 记录即可 |

> ⚠️ **范围澄清（本项目任何文档不得误述）**：Step 1 的 `topic_terms` 修复是**针对性修补**，仅覆盖已逐条确认的 4 个错配案例，**不是**系统性修复 aux 过度宽泛问题；其余 83 条（其中 21 条含泛型原子）的同类风险仍在 Phase 2 排查。

**我们选择公开这些缺口，而非掩盖** —— 合规工具的可信度来自「知道自己哪里不可靠」，而不是「声称自己完美」。

---

## 作品集关系

| 项目 | 合规领域 | 判定性质 |
|------|----------|----------|
| [oss-license-checker](https://github.com/vickywu97/oss-license-checker) | 知产 / 开源法务 | 硬规则（兼容矩阵） |
| [token-classifier](https://github.com/vickywu97/token-classifier) | Web3 / 加密法务 | 软规则（Howey 四要素） |
| **privacy-policy-checker** | 数据 / 隐私法务 | 半硬规则（检查项） |

三者共同构成「法律 + 工程」完整作品集，均由律师 + 税务师 + 专利代理师 + 代码能力交集构建。

---

## 路线图

- [ ] 英文隐私政策专项检查项（同义词扩展）
- [ ] URL 抓取模式（用户主动提供确切 URL，单次 GET，遵守 robots.txt）
- [ ] 行业模板（金融 / 医疗 / 儿童数据）
- [ ] GitHub Pages 在线 demo
- [x] `--fail-on high` 参数（CI 集成）

---

## 许可证

MIT —— 作者为律师 / 税务师 / 专利代理师，本项目作为求职作品集开源。
