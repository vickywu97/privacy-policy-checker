# 匹配器精度修复报告（v2）

> 日期：2026-09-16 ｜ 范围：`privacy_policy_checker/matcher.py` + GDPR-17/49、PIPL-47 检查项
> 原则：零依赖、离线、可复现；不做 LLM 判定；每个 fix 都有回归测试锁定。

## 一、根因

v1 匹配器是「纯关键词 + 单段证据」：

- `required_patterns` 任意命中 → satisfied，`context_patterns` 命中 → partial；
- 证据取自**第一个**含该词的段落，且 `context_patterns` 的**泛化词**（如 `删除`、`transfer`）会跨语义命中。

这导致两类误判：

1. **证据归因错**：删除权检查项命中「保存期限…到期后我们将**删除**…」段（自动删除），而非数据主体「**请求删除**」段。
2. **泛化词跨语义误匹配**：减损条款（Art 49）因 `transfer` 命中了跨境传输段里的「SCC 保障措施」句（实为 Art 46）。

## 二、匹配器改进（五点对应）

| # | 要求 | 实现 |
|---|------|------|
| 1 | 上下文/证据归因 | 证据取自**真正含核心词的段落**；core 优先于 aux；`_find` 返回首个非否定命中的段落 |
| 2 | 核心词 / 辅助词分离 | 新增 `core_patterns`（命中→satisfied）、`aux_patterns`（仅命中→partial）；缺省分别回退 `required_patterns` / `context_patterns` |
| 3 | 否定语境检测 | 命中词前 12 字符内出现否定标记（不/不会/not/without 等）则该次命中作废，继续寻找其他出现；全否定视为未命中 |
| 4 | 避免重复段落命中 | 见「说明」——不做状态级去重（见下），改为强化证据归因 |
| 5 | conditional 前置检查 | 保留并沿用：`conditional_keywords` 全文未出现 → `not_applicable`，不进入关键词匹配 |

**关于 #4（重复段落命中）的说明**：good-demo 第 38 行是一句英文「权利总述」（access, rectify, erase, restrict, port…），它**确实**同时断言了多项 GDPR 权利，因此被多个检查项引用是**正确**的——严格去重反而会造成漏判（false negative）。故 v2 不做状态级去重，而是用 #1 的「证据归因」确保每条检查项指向**最贴切**的段落。如确需统计「证据集中度」，可在报告层另加，不影响判定。

## 三、修复前后对照表（good-demo）

| 检查项 | 修复前判定 | 修复后判定 | 变化原因 |
|--------|-----------|-----------|----------|
| **GDPR-17 删除权** | partial（line 11 保存期限「删除」） | **satisfied**（line 26「有权请求删除」） | 核心词改为主动权利表述；移除泛化「删除」辅助词，不再命中自动删除段 |
| **GDPR-49 减损条款** | partial（line 37 SCC 保障句） | **missing** | 移除泛化「transfer/传输」辅助词；样例援引 SCC（Art 46）而非 Art 49 减损 → 缺失（合法审计点） |
| **PIPL-47 删除权** | satisfied（line 11 保存期限「删除」） | satisfied（line 26「有权请求删除」） | 证据归因修正（状态本对，但**证据段落错了**） |
| GDPR-20 数据可携带权 | satisfied（line 37「port your data」） | satisfied（line 37） | 核对证据相关，**非误判**，保持 |
| GDPR-18 限制处理权 | satisfied（line 26「限制处理」） | satisfied（line 26） | 证据相关，非误判 |
| GDPR-15 访问权 | satisfied（line 37「right to access」） | satisfied（line 26「查阅」） | 证据现归到中文权利段（更贴切），状态不变 |
| GDPR-13-2b 数据主体权利 | satisfied（line 37） | satisfied（line 37） | 总述项，证据相关，不变 |
| GDPR-45 充分性认定传输 | missing | missing | 样例有跨境语境但援引 SCC 而非充分性决定 → 缺失正确 |
| GDPR-13-2e 提供数据法定义务 | missing | missing | 低风险项未覆盖 → 缺失正确 |
| PIPL-57 泄露通知 | not_applicable | not_applicable | 样例无「泄露/安全事件」语境 → 设计上判不适用（保留，可后续讨论是否改缺失） |

## 四、验证

- 全量测试：13 项（原 11 + 新增 3 条回归）全绿。
- good-demo 修复后统计：总数 71｜satisfied 56｜partial 0｜missing 6｜not_applicable 9；有效风险 high 0 / medium 2 / low 4。
- high 风险始终为 0（修复未引入任何高风险缺口，GDPR-17 由 partial→satisfied，GDPR-49 由 partial→missing 仍属 low）。
- 未修改 good-demo 样例文本；未删除/跳过任何检查项。
