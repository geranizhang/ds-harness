# ds-harness

一个 Claude Code plugin：把一个数据分析命题从假设树走到可交付报告。主会话负责对话和四道人工门；三个 agent 分担跑数、对抗审查、写稿；能用代码判定对错的规则做成脚本；不可逆的错误由 hook 在环境层拦截。**数据平台、合规规则、报告范文、团队词表全部放在 adapter 里**，核心不含任何一家的东西。

English: [README.md](README.md)

## 流程

```
命题
  │ 🚪 门一：命题归属                                主会话
  ├─ analysis-brief → BRIEF.md（假设 / 维度 / 跑数清单）  skill
  │ 🚪 门二：执行计划（探针 / 机房 / 多天拆分）          主会话
  ├─ data-runner → raw/ + 跑数报告                      agent   ← hook 现场校验合规区 SQL、拦抽样
  ├─ 逐假设判定，回填 BRIEF                             主会话
  ├─ adversarial-reviewer → 挑战清单                    agent   （进 BRIEF §5，不进文档）
  ├─ report-writer(outline) → 待批大纲                  agent
  │ 🚪 门三：批大纲                                    主会话
  ├─ report-writer(draft) → md + xlsx + 校验             agent
  ├─ report-writer(review) → 问题清单                    agent
  │ 🚪 门四：改动计划确认                               主会话
  └─ 发布、登记版本                                     主会话
```

agent 不能中途问人：需要拍板的事返回 `BLOCKED`，主会话问完把答案交回同一个 agent。agent 不改参考库：返回的「reference 待更新」由主会话写入。

## 三层约束

| 层 | 是什么 | 在哪 |
|---|---|---|
| 知识与流程 | 规则、口径、范文——写给模型遵守 | `skills/`、`agents/`、`adapters/<name>/references/` |
| 确定性校验 | 能用代码判断的：SQL 口径区与抽样、raw 截断、正文每个数字回查到表、表格陷阱 | `skills/*/scripts/` |
| 环境强制 | 合规区提交现场校验；抽样无批准即拦 | `hooks/guard.sh` |

每条规则都问一句：**是环境强制的，还是请求模型遵守的？** 长会话里请求会衰减，所以能搬进下两层的都搬。

## 核心 / adapter 的切分

判据一句话：把你们公司的名词换成别家的，这条规则还对不对？对 → 核心；不对 → adapter。流程、四道门、假设树、取数粒度 ≠ 展示粒度、置信度三档、报告骨架、禁自造词是核心；机房、队列、截断阈值、合规红线、表手册、指标字典、范文、词表、文档工具是 adapter。

## 安装与接入

见 `README.md`「Install」和 `docs/ADAPTER.md`。接入自己的平台：复制 `adapters/_template`，填 `adapter.json`，写五个参考文件（平台 / 表 / 指标 / 术语 / 交付），放 1–3 篇范文，跑 `build_vocab.py`，跑 `evals/`。

团队 adapter 默认私有：放在自己的仓库里用 `DS_HARNESS_ADAPTER_DIR` 指过去，或放进 `adapters/<name>/`（除 `_template` 外该目录被 git 忽略）。本框架抽象自一个内部团队的配置，那份 adapter 在单独的私有仓库里。

许可：MIT。

## 不包含

个人 memory、项目目录、文档工具的 skill、凭证、拉起 `qa-followup` 的消息守护进程。
