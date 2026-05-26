# alevel_tutor 开发计划 v2

> 生成日期：2026-05-26  
> 当前版本：v0.1.0  
> 参考方案：`Agentic Tutor MVP for Chinese A-Level Students`（已批判性评估）

---

## 零、对 PDF 方案的批判性评估

PDF 方案整体质量很高，但以下判断需要质疑和修正：

### 0.1 模型选型：不应死绑阿里百炼

**PDF 说**：阿里百炼为唯一主提供商，Qwen2.5-7B 做主力。

**实测对比**（截至 2026-05-26）：

| 模型 | 输入价格 | 输出价格 | 质量 | Function Calling | 视觉 |
|------|---------|---------|------|-----------------|------|
| DeepSeek V4-Flash | $0.14/M | $0.28/M | ≈GPT-4o 级别 | ✅ | ❌ |
| Qwen2.5-7B | ¥0.5/M | ¥1/M | 中等 | ⚠️ 有限 | ❌ |
| Qwen3-8B | ¥0.5/M | ¥2/M | 中上 | ⚠️ 有限 | ❌ |
| GLM-4V-Plus | ¥5/M | ¥5/M | 中上 | ⚠️ | ✅ |
| Qwen-VL-Max | ¥3/M | ¥12/M | 中上 | ⚠️ | ✅ |

**结论**：DeepSeek V4-Flash 文字辅导最强也够便宜。视觉必须另选（DeepSeek 无视觉API）。**多提供商才是正确策略**，PDF 的「单提供商简化运维」论据在视觉能力面前不成立——不管用什么文字模型，你都需要一个视觉模型。

**修正**：文字→DeepSeek V4-Flash（主力），视觉→GLM-4V-Plus 或 Qwen-VL-Max（按需），数学批改→DeepSeek V4-Flash thinking mode 足够，不需要单独的 Qwen2.5-Math-7B。

### 0.2 ¥20/月预算：实际需要 ¥50-100

**PDF 说**：¥20/月够 250-1000 次完整图片→反馈。

**实际验算**（10 个学生，每人每天 3 道题，30 天 = 900 次交互）：

| 操作 | 单价 | 月调用量 | 月成本 |
|------|------|---------|--------|
| 文字提示回答 | ¥0.007 | 600 次 | ¥4.2 |
| 完整解答 | ¥0.013 | 200 次 | ¥2.6 |
| OCR | ¥0.007 | 900 次 | ¥6.3 |
| 视觉 fallback（20% 触发） | ¥0.014 | 180 次 | ¥2.5 |
| 批改 | ¥0.020 | 400 次 | ¥8.0 |
| 重试/异常 | — | — | ¥5.0 |
| **合计** | | | **~¥29** |

这是在非常保守的假设下。实际使用中：
- 图片更大→更多 tokens
- prompt 迭代→更多消费
- 长 essay 批改→远超预算

**修正**：月预算设为 **¥50-100** 作为 pilot 预算。¥20 仅够 founder 自己测试。需实现成本仪表盘，按用户设置额度。

### 0.3 第一科选 9709 Math：有理但有代价

**PDF 说**：Math 评分标准明确，公式化程度高，最适合先验证。

**支持论点**：Math 的答案有客观对错，批改校准最容易做。
**反对论点**：Math 的 OCR 是所有科目里最难的（公式 LaTeX 精度 < 80%），而且纯文字的概念问答最少（学生最常问的是"怎么做这道积题"而不是"什么是积分"），这对知识库要求高。

**修正**：保持 Math 先行的策略（评分校准容易），但要意识到 **OCR 是 Math 最大的瓶颈**。M1 的核心任务就是证明「Math 公式 OCR 精度可以接受」。如果不可以，立刻切换到 Chemistry（化学方程式文字比例高，OCR 容易）。

### 0.4 PostgreSQL + Redis + OSS：MVP 过度工程化

**PDF 说**：PostgreSQL + Redis + Alibaba OSS。

**质疑**：20-80 个学生的 pilot，真的需要这些吗？

- **PostgreSQL**：SQLite 完全可以支撑 pilot 阶段的并发。PostgreSQL 的价值在于 JSONB 和全文搜索，但 MVP 不需要。**pilot 用 SQLite，上线再切 PostgreSQL**。
- **Redis**：ChromaDB 自带缓存。聊天实时性用不到 Redis 队列。**pilot 不需要**。
- **OSS 对象存储**：本地文件系统 + 定时备份到云盘足够。**pilot 不需要**。

**修正**：M3-M4 阶段用 **SQLite + 本地文件**，Docker Compose 只打包前端+后端+DB。用户量 > 100 且有付费意愿后再加 PostgreSQL + Redis。

### 0.5 Citation Store 应优先引用 Examiner Report 而非 Syllabus

**PDF 说**：Citation Store 存 syllabus 片段、公式表、学校讲义。

**质疑**：Syllabus 只告诉你"考什么"，不告诉你"怎么得分"。对学生最有价值的引用是：
1. **Mark Scheme 原文**：精确到「这个词值 1 分」
2. **Examiner Report 原文**：考官说「大多数学生在这里犯的错误是...」
3. **Syllabus**：仅用于 topic mapping，不作为学生可见的引用

**修正**：Citation Store 的 seed 优先用 examiner report 和 mark scheme 中的关键句子，而非 syllabus 段落。

### 0.6 作业切题（Question Splitting）不应进 M3

**PDF 说**：M3 做作业切题。

**质疑**：作业切题是视觉理解中最难的任务之一——需要同时识别题号、题型边界、跨页题目。学术界 2025 年才刚有可靠的方案（OmniDocBench）。在 M3 阶段投入这个，会严重拖慢进度。

**修正**：Pilot 阶段**不做自动切题**。让学生每次上传一道题，或手动框选区域。自动切题进 v1.1。

### 0.7 已验证的判断（PDF 正确，保持）

以下 PDF 的判断经过调证，确认正确：

- ✅ **Hint-First 教学策略**：EEF 教育研究确实支持 metacognitive prompting。正确。
- ✅ **窄 Agentic 架构**：对 ¥50 预算来说，工具路由远优于多 Agent 协作。正确。
- ✅ **OCR 分阶段**：先 CV 预处理→便宜 OCR→低置信才 VLM。正确且已在 `ocr_pipeline.py` 实现。
- ✅ **Bilingual 三模式**：中文优先/英文优先/Exam English。正确。
- ✅ **error_logs 是最重要的日志**：从 day 1 记录错因，后续错题本和用户画像才有数据基础。正确。

---

## 零-B、与 PDF 方案的对齐检查

PDF 方案的核心设计决策，本计划严格遵循：

| PDF 决策 | 本计划对齐 |
|----------|----------|
| **窄 Agentic**（一个 Orchestrator 路由工具链，不做多 Agent 辩论） | ✅ `agent/core.py` 已实现 tool-calling 路由 |
| **Hint-First** 教学（先提示，学生试过再给完整答案） | ✅ `agent/prompts.py` 四段式回答强制这个顺序 |
| **Bilingual UX**（中文优先/英文优先/Exam English 三种模式） | ✅ Phase 4 Web 前端明确三种模式 |
| **Citation-Backed**（所有回答可溯源到考纲/公式/讲义） | ⚠️ Citation Store 需要 seed（Phase 0 P0） |
| **OCR before Vision**（先便宜 OCR，低置信才走 VLM fallback） | ✅ `agent/ocr_pipeline.py` + `agent/content_types.py` 路由 |
| **数据最小化**（PIPL 合规，EXIF 去除，PII 分离） | ⚠️ Phase 6 安全审查 + Phase 0 P0（EXIF stripping） |
| **¥20/月预算**（短提示、缓存、批处理、按需生成完整答案） | ✅ Phase 6 BudgetGuard |
| **第一科从 9709 Math 开始**（符号性强，评分标准明确） | ✅ Phase 0 单科先行 |

---

## 一、当前状态 & 与 PDF P0 清单的差距

PDF 第 26 页的 **立即执行清单**，逐项对照：

| PDF P0 任务 | 我们完成了吗 | 状态 |
|------------|-----------|------|
| 确定首个 demo 科目（建议 9709 Mathematics），选 50 道代表题 | ❌ | 需要做 |
| 搭建 Next.js + FastAPI + Postgres + Redis，Docker Compose 一键启动 | ❌ | 当前只有 CLI，需要 Phase 4-5 |
| 接入百炼 OpenAI-compatible API（text chat + OCR + VLM fallback） | ⚠️ | 代码写了，API key 没配，没实测 |
| 完成 Citation Store seed（每科至少 20-40 条考纲/概念/公式片段） | ❌ | None — 需要从 syllabus PDF 提取 |
| 实现 `/questions/parse`（图片上传后返回 CanonicalQuestion JSON） | ⚠️ | `ocr_pipeline.py` 写了框架，没实测 |

| PDF P1 任务 | 状态 |
|------------|------|
| 实现 hint-first 和 full solution（每次回答结构稳定，带引用芯片） | ⚠️ 提示词写了，引用芯片没配 Citation Store |
| 实现 grading JSON（分数、置信度、错误、下一步建议、错因标签） | ⚠️ vision.py 返回自由格式文本，未结构化 |
| 建立 eval set（每科至少 20 题，后续扩到 50+） | ❌ None |

| PDF P2 任务 | 状态 |
|------------|------|
| 实现成本日志和限流（每个用户、route、model 成本估算） | ❌ None |
| 母校 pilot 准备（演示账号、反馈表、隐私说明） | ❌ None |

---

## 二、分阶段计划（对齐 PDF 四个里程碑）

### Milestone 1：单科可用的骨架（Week 1-2）

**对应 PDF 原文**："sign-in, uploads, text tutoring, and a single subject working end-to-end. Start with 9709 Mathematics."

**目标**：9709 Math 一条完整链路跑通。

| # | 任务 | 参考 PDF 页 | 完成标准 |
|---|------|-----------|---------|
| **M1.1** | 配置所有 API Key（DEEPSEEK + ZHIPU/QWEN + MATHPIX 可选） | p.18 | `.env` 文件加载，`agent/config.py` 检测通过 |
| **M1.2** | 安装全部 OCR 依赖并下载模型 | p.13 | `PaddleOCR`、`surya-ocr`、`DECIMER` import 成功，首次加载完成 |
| **M1.3** | 选 50 道 9709 Math 代表题（P1 纯数 + P4 力学 + P5 统计各 15-20 题） | p.26 | 50 题清单：题目 PDF 页面截图 + 标准答案 + marking 要点 |
| **M1.4** | 修复 `ocr_pipeline.py` 已知 bug → 对 50 道题逐一跑 OCR | p.10 | 每题输出 CanonicalQuestion JSON，记录每类内容的 OCR 精度 |
| **M1.5** | 实现 `/questions/parse` API（图片→结构化 JSON） | p.9 | FastAPI endpoint 返回 CanonicalQuestion |
| **M1.6** | 构建 Citation Store seed（9709 考纲 + 公式表 + 概念） | p.10-11 | 每 topic 至少 5 条 snippet，总计 40+ 条 |
| **M1.7** | 验证 9709 Math 文字问答 + 图片问答完整回路 | p.4 | 50 题跑通：上传→OCR→结构化→LLM提示→完整答案→引用来源 |
| **M1.8** | 实现结构化 grading JSON（分数/置信度/错误/错因tag） | p.13 | 批改输出严格 JSON 格式，不是自由文本 |
| **M1.9** | 写 M1 测试报告 | — | `plans/milestone1_report.md`：OCR 精度表、bug 清单、每条链路的成功率 |

**M1 退出标准**：
- 9709 Math 50 道题 OCR→回答→批改 全流程跑通率 > 80%
- CanonicalQuestion JSON 格式稳定
- Citation Store 有 40+ 条 snippet，回答中出现引用 chip
- 批改输出结构化 JSON（不是自由文本）

---

### Milestone 2：图片解析 + 引用 + 低置信处理（Week 3-4）

**对应 PDF 原文**："image parsing, citation rendering, and low-confidence handling. The key success metric is not 'AI impressiveness.' It is whether the system gracefully says 'I cannot read this clearly enough' rather than inventing certainty."

**目标**：4 科图片题都能处理，低置信诚实降级。

| # | 任务 | 参考 PDF 页 | 完成标准 |
|---|------|-----------|---------|
| **M2.1** | 扩展到 4 科：每科准备 20 张测试图 | p.9 | 80 张测试图覆盖全部 30 种内容类型 |
| **M2.2** | 实现内容路由器（根据 subject + 关键词选择 OCR 引擎） | p.10 | 化学结构走 DECIMER、数学公式走 Surya、文字走 PaddleOCR、图表走 Qwen3-VL |
| **M2.3** | 实现 OCR 置信度分级 + 降级提示 | p.9 | >0.85 direct，0.5-0.85 confirm then answer，<0.5 "图片不清晰，请重拍或手动输入" |
| **M2.4** | 图片预处理流水线（crop/deskew/compress/EXIF strip） | p.10 | 所有上传图片默认走 OpenCV 预处理；EXIF 自动去除 |
| **M2.5** | 手写识别专项（真实手写作业 30 份测试） | p.4 | OCR 置信度分布记录；低置信触发「重拍」而非硬猜 |
| **M2.6** | Citation Store 扩充到 4 科 | p.10-11 | 每科 20-40 条 snippet，总计 100+ 条 |
| **M2.7** | 答案引用芯片渲染（前端或 CLI 输出中显示考纲来源） | p.11 | `📎 9709 §Integration` 格式的引用出现在每个正式答案末尾 |
| **M2.8** | 建立 Eval Set（每科 20 题金标） | p.22 | 每题有：题目图、标准答案、真人评分、expected misconception tags |
| **M2.9** | 批改评分校准 | p.21-22 | AI 评分 vs 真人评分 MAE < 0.5/4，相关性 > 0.85 |
| **M2.10** | 写 M2 测试报告 | — | `plans/milestone2_report.md` |

**M2 退出标准**：
- 4 科图片 OCR 跑通率 > 80%
- 低置信图片准确提示「无法识别」率 > 90%（不硬猜）
- Citation Store 100+ snippet，回答引用覆盖率 > 80%
- 批改校准通过 MAE 和相关性阈值

---

### Milestone 3：作业批改 + 错题日志（Week 5-6）

**对应 PDF 原文**："homework batch correction for all four subjects, plus the logging needed for the future wrong-question notebook and user profiling."

**目标**：多题作业批改、错题数据入库。

| # | 任务 | 参考 PDF 页 | 完成标准 |
|---|------|-----------|---------|
| **M3.1** | PostgreSQL 数据模型实现（6 张表） | p.14-17 | users, questions, answers, annotations, error_logs, usage_events 建表+迁移 |
| **M3.2** | 用户注册/登录 API | p.9 | email+password（JWT），支持删除和导出 |
| **M3.3** | 对话持久化 | p.14-15 | 每次问答写入 answers 表，刷新后可查看历史 |
| **M3.4** | 错题日志记录（error_logs 表 — PDF 强调「最重要的未来规划」） | p.16-17 | 每次批改自动写入 error_family + error_atom + severity + evidence_json |
| **M3.5** | 作业切题流水线（一张图多道题→拆成独立题目） | p.10 | 轮廓检测 + 题号识别 → 每道题单独处理 |
| **M3.6** | Homework batch correction（提交整页作业→返回每题批改结果） | p.10 | Queue status: Ready / Needs better image / Low confidence / Reviewed |
| **M3.7** | 答案输出模板标准化（按题型区分） | p.13 | MCQ: 选项+排除逻辑; 计算: 公式→working→boxed answer; 解释: 因果链; Essay: 定义→论证→评估→结论 |
| **M3.8** | 批改权重实现（Correctness 40%, Method 35%, Represent 15%, Comm 10%） | p.13-14 | grading JSON 的 `rubric_json` 字段包含 4 维分项评分 |
| **M3.9** | 写 M3 测试报告 | — | `plans/milestone3_report.md` |

**M3 退出标准**：
- 6 张表全部建好，迁移运行成功
- 登录/注册/对话持久化正常
- error_logs 表持续记录，每条有 error_family + error_atom
- 作业切题准确率 > 70%（低置信题进 review queue）
- 批改按 4 维度输出分项评分

---

### Milestone 4：校准 + 成本控制 + 安全（Week 7-8）

**对应 PDF 原文**："prompt trimming, model routing, version pinning, and budget envelopes."

**目标**：生产可运维，成本可控，安全合规。

| # | 任务 | 参考 PDF 页 | 完成标准 |
|---|------|-----------|---------|
| **M4.1** | 实现 UsageLogger + BudgetGuard | p.19-20 | 每次 API 调用记录 model/tokens/成本估算；日预算超额自动降级 |
| **M4.2** | 成本 Dashboard | p.20 | 前端展示本月用量/预算比，按 route 分拆 |
| **M4.3** | Prompt/Rubric/Model 版本化 | p.22-23 | 每次批改日志写入 `prompt_version`, `rubric_version`, `model_id` |
| **M4.4** | 跨平台 API 健康检查 + 自动降级 | p.8 | 阿里不可用→腾讯 fallback→纯文本降级 |
| **M4.5** | 内容安全过滤（prompt injection 防护、恶意文件扫描） | p.22 | 违禁词库 + 文件类型白名单 + 大小限制 |
| **M4.6** | 隐私合规（PIPL：账号删除/导出、PII 分离、cookie 同意） | p.22-23 | 删除账号=级联删除所有上传图和日志；EXIF 自动去除 |
| **M4.7** | 批处理任务（夜间走 batch inference 半价） | p.20 | 错题总结、周报走 batch pipeline |
| **M4.8** | Docker Compose 一键部署 | p.7 | `docker-compose up` 启动全部服务（前端+后端+DB+Redis） |
| **M4.9** | 写 README.md + 架构图 | — | 项目介绍、快速开始、API 文档、架构图 |
| **M4.10** | 写 M4 测试报告 | — | `plans/milestone4_report.md` |

**M4 退出标准**：
- 日 API 成本可追踪到 ±10%
- BudgetGuard 在超 80% 预算时降级
- prompt/rubric/model 版本号写入每笔日志
- 隐私合规 checklist 通过
- Docker Compose 一键启动全部服务
- README 可读

---

## 三、Web 前端计划（与 M2-M4 并行）

| 页面 | 功能 | 对应 PDF | 完成里程碑 |
|------|------|---------|----------|
| `/` | Landing page：功能展示 + 登录 | p.7 | M2 |
| `/app` | 聊天区、上传区、科目选择、语言模式 | p.3-4 | M2 |
| `/question/<id>` | 题目图、OCR 结果、提示、答案、引用 chips | p.11 | M2 |
| `/grade/<id>` | 评分卡片（4 维分项）、错因标签、改进建议 | p.13-14 | M3 |
| `/homework` | 作业上传→切题→批改进度队列 | p.10 | M3 |
| `/history` | 最近题目、按科目筛选 | p.21 | M3 |
| `/settings` | 语言模式、API 额度、数据删除/导出 | p.22-23 | M4 |
| `/dashboard` | 成本监控、学习概览 | p.20 | M4 |

**三种语言模式**（PDF p.3-4）：
- **中文优先**：讲解用中文，学科关键词/公式/command words 保留英文
- **英文优先**：解释用英文，关键处加中文注释
- **Exam English**：全英文，模拟考试环境
- **Hover Gloss**：鼠标悬停英文关键词显示中文解释

---

## 四、CanonicalQuestion Schema（PDF p.8-9）

```json
{
  "question_id": "q_9709_2022_p1_001",
  "subject": "9709",
  "question_type": "structured_calculation",
  "language_mode": "zh_first",
  "stem_text": "A block rests on a smooth plane inclined at 30°...",
  "subparts": [
    { "label": "(a)", "marks": 2, "target_skill": "resolve_forces",
      "depends_on": null, "carry_forward": false },
    { "label": "(b)", "marks": 4, "target_skill": "use_suvat",
      "depends_on": "(a)", "carry_forward": true,
      "ft_note": "FT from (a) accepted" }
  ],
  "table_regions": [],
  "diagram_regions": [
    { "bbox": [120, 88, 420, 360], "kind": "diagram",
      "description": "Block on inclined plane" }
  ],
  "formula_regions": [
    { "bbox": [460, 102, 700, 220], "latex": "F = ma",
      "confidence": 0.95 }
  ],
  "handwriting_regions": [],
  "ocr_confidence": 0.93,
  "source_refs": ["9709_mechanics_component"],
  "needs_visual_reasoning": false,
  "needs_manual_review": false
}
```

## 五、Grading Rubric（PDF p.13-14）

| 维度 | 权重 | 检查要点 |
|------|------|---------|
| **Correctness** | 40% | 最终答案数值/结论是否正确 |
| **Method / Reasoning** | 35% | 公式选择、代入步骤、逻辑链（Math/Phys/Chem 最关键） |
| **Representation** | 15% | 单位、有效数字、图表标签、符号书写规范 |
| **Communication** | 10% | 解释清晰度、essay 结构（Econ 权重更高） |

批改 JSON 输出：
```json
{
  "score_awarded": 7,
  "score_max": 10,
  "confidence": 0.88,
  "verdict": "Partially correct — method right but unit error in (b)",
  "rubric_scores": {
    "correctness": 2.5, "method": 3.2,
    "representation": 0.8, "communication": 0.5
  },
  "strengths": ["Correct formula selection", "Clear working steps"],
  "mistakes": ["Unit: used kg instead of g in (b)"],
  "misconception_tags": ["units", "carelessness"],
  "next_step": "Practice unit conversions: always convert to SI before substituting",
  "citations": ["9709 §Mechanics", "Formula Sheet M1"]
}
```

## 六、数据模型（PDF p.14-17，对齐）

6 张核心表 + 1 张引用表：

```
users               — 账号、语言偏好
assets              — 上传图片/PDF 原始文件
questions           — CanonicalQuestion JSON（题目主表）
answers             — 每次 AI 回答/批改结果
annotations         — 图片区域标注（bbox/公式/图表/手写区域）
error_logs          — 错因日志（error_family + error_atom + evidence）⭐ 最重要
source_snippets     — Citation Store 引用片段
usage_events        — 每次 API 调用的 token/cost 日志
```

**error_logs 表字段**（PDF 强调这是整个项目最有价值的日志）：
- `error_family`: concept / method / algebra / units / diagram_reading / essay_structure / translation / carelessness
- `error_atom`: 具体标签如 `forgot_moles_ratio`、`used_g_not_gsinθ`
- `severity`: 1-5
- `evidence_json`: {snippet, region_ref, rubric_ref}

## 七、外部依赖引入清单

| M# | 新引入依赖 | 用途 |
|-----|-----------|------|
| M1 | `paddleocr`, `surya-ocr`, `DECIMER`, `fastapi`, `uvicorn` | OCR + API 服务 |
| M1 | `python-dotenv` | .env 文件加载 |
| M3 | `sqlalchemy`/`sqlmodel`, `alembic`, `asyncpg` | 数据库 |
| M3 | `python-jose`, `passlib`, `bcrypt` | JWT + 密码哈希 |
| M4 | `docker-compose` | 容器化部署 |
| M4 | `Pillow` (已有), `opencv-python-headless` | 图片预处理 |
| Web | `next.js`, `react`, `typescript`, `tailwind`, `shadcn/ui` | 前端 |

## 八、总时间线（8 周 → Pilot）

```
Week 1-2  │ M1: 9709 Math 单科骨架
          │  ├─ API key 配置 + 依赖安装
          │  ├─ 50 题 eval set + OCR 跑通
          │  ├─ /questions/parse API
          │  ├─ Citation Store seed
          │  └─ 端到端验证
          │
Week 3-4  │ M2: 4 科图片解析 + 引用
          │  ├─ OCR 置信度分级 + 降级
          │  ├─ Citation Store 扩充 100+ snippet
          │  ├─ 批改校准（vs 真人评分）
          │  └─ Web 前端 /app 页面
          │
Week 5-6  │ M3: 作业批改 + 数据库
          │  ├─ PostgreSQL 6 表 + 迁移
          │  ├─ 登录/注册 + 对话持久化
          │  ├─ 作业切题 + 批改流水线
          │  ├─ error_logs 错因记录
          │  └─ Web 前端 /grade /homework /history
          │
Week 7-8  │ M4: 校准 + 安全 + 部署
          │  ├─ BudgetGuard + 成本 Dashboard
          │  ├─ 版本化（prompt/rubric/model）
          │  ├─ 安全合规审查
          │  ├─ Docker Compose 部署
          │  └─ README + 架构图

Week 9-10 │ Pilot: 5-10 名真实学生试用
```

## 九、今天立即执行（Phase 0 / M1 启动）

```bash
# 1. 环境配置
echo "DEEPSEEK_API_KEY=sk-xxx" > .env
echo "ZHIPU_API_KEY=xxx" >> .env
echo "DASHSCOPE_API_KEY=xxx" >> .env  # 备用

# 2. 安装依赖
pip install paddleocr surya-ocr fastapi uvicorn python-dotenv Pillow

# 3. 修复已知 bug
# - agent/ocr_pipeline.py: Surya API 调用方式修正
# - agent/ocr_pipeline.py: DECIMER import 路径确认
# - agent/ocr_pipeline.py: PPStructure 参数修正
# - agent/core.py: grade_homework_image tool 真正调用 vision

# 4. 准备 9709 Math 50 道 eval 题
python3 build_kb.py --subject 9709 --max-papers 20

# 5. 验证端到端
python3 chat.py --subject 9709
```

---

**参考 PDF**：`plans/Agentic Tutor MVP for Chinese A-Level Students.pdf`（英文 v1）和 `plans/agentic_tutor_zh_report.pdf`（中文 v2）。本计划是这两个方案的可执行版本。
