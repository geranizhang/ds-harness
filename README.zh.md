# ds-harness

一个 Claude Code plugin：把一个数据分析命题从假设树走到可交付报告。主会话负责对话和四道人工门；三个 agent 分担跑数、对抗审查、写稿；能用代码判定对错的规则做成脚本；不可逆的错误由 hook 在环境层拦截。**一切与具体公司、平台、团队有关的东西放在 adapter 的八个接入点里**——填满接入点，通用框架就变成你们团队的工作流。

English: [README.md](README.md)

## 八个接入点

| 接入点 | 回答什么 | 必填 |
|---|---|---|
| `platform` | 这里怎么跑一条查询：机房/分片、工具、取回上限、方言规则 | 是 |
| `compliance` | 什么是禁止的、提交前检查什么 | 否 |
| `channel` | 怎么和元数据机器人、聊天群说话 | 否 |
| `knowledge` | 数据长什么样：带范围索引的表手册、指标定义、术语 | 建议 |
| `analysis-priors` | 我们已经知道什么：领域研究、已定结论、假设库、confounder、分析立场 | 建议 |
| `delivery` | 报告在这里长什么样：文档工具、词表、范文、语言相关的词单 | 是 |
| `operations` | 文件放哪、谁能拍板：工作区、审批、门策略、无人值守护栏 | 是 |
| `evals` | 怎么证明没退化 | 否 |

规范见 `adapter-spec/README.md`，接入步骤见 `docs/ADAPTER.md`，骨架见 `adapters/_template/`（含两篇虚构范文）。

## 流程

```
命题
  │ 🚪 门一：命题归属                                主会话
  ├─ analysis-brief → BRIEF.md（假设 / 维度 / 跑数清单）  skill
  │ 🚪 门二：执行计划（探针 / 机房 / 多天拆分）          主会话
  ├─ data-runner → raw/ + 跑数报告                      agent   ← hook 现场校验合规区 SQL、拦抽样
  ├─ 逐假设判定，回填 BRIEF                             主会话   → 写回 findings.md
  ├─ adversarial-reviewer → 挑战清单                    agent   （进 BRIEF §5，不进文档）
  ├─ report-writer(outline) → 待批大纲                  agent
  │ 🚪 门三：批大纲                                    主会话
  ├─ report-writer(draft) → md + xlsx + 校验             agent
  ├─ report-writer(review) → 问题清单                    agent
  │ 🚪 门四：改动计划确认                               主会话
  └─ 发布、登记版本                                     主会话
```

## 核心 / adapter 的判据

把你们公司的名词换成别家的，这条规则还对不对？对 → 核心；不对 → adapter。流程、四道门、假设树、取数粒度 ≠ 展示粒度、置信度三档、报告骨架、禁自造词是核心；机房、队列、截断阈值、合规红线、表手册、指标字典、范文、词表、文档工具、团队立场是 adapter。

## 安装

```bash
cp -R ds-harness/adapters/_template /path/to/my-team   # 按 docs/ADAPTER.md 填
ds-harness/bin/install.sh /path/to/my-team              # 核心 + adapter 一起装进 ~/.claude
```

团队 adapter 默认私有，放自己的仓库；本仓库 `adapters/` 下除 `_template` 外均被 git 忽略。

许可：MIT。
