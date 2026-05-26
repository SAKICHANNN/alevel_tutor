# alevel_tutor — 终极开发计划 v3

> 生成日期：2026-05-26  
> 基于：四份 plans/ 文档 + 深度 web search + 全部对话历史决策

---

## 开场：从对话中诞生的所有决策

以下每个设计都来自我们对话过程中的明确讨论，不是凭空假设：

### 产品层面

| 决策 | 来自对话 | 落实位置 |
|------|---------|---------|
| **「通俗易懂 + 巧妙比喻」**教学风格 | 你要求「给理解能力稍微差的学生，用生活化比喻解释」 | `agent/prompts.py` SYSTEM_PROMPT — 四段式回答：🎯比喻→📖讲解→📝套路→❓检查 |
| **四种核心问答**：教材问答、题目问答、识图批改、套路总结 | 你列的四大功能需求 | `agent/core.py` TOOLS 定义了 search_textbook / search_past_paper / get_exam_pattern / grade_homework_image |
| **中文 API 模型**，不是 OpenAI | 你要求「DeepSeek、GLM、Qwen 这类便宜的中国模型，API 非本地，可拆分视觉和推理」 | `agent/config.py` — DeepSeek V4-Flash 文字 + GLM-4V-Plus/Qwen-VL 视觉 |
| **¥20/月预算约束** | PDF 方案提出，你认可 | 计划第六节成本控制，免费额度策略 |
| **多提供商**，不绑单一厂商 | 你在对话中质疑 PDF 的「单提供商」建议 | 已确认：DeepSeek 无视觉能力 → 文字和视觉必须分开 |
| **从 9709 Math 开始** | PDF 建议 + 你确认 | W1-W2 单科先行 |

### 数据层面

| 决策 | 来自对话 | 落实位置 |
|------|---------|---------|
| **实测试卷确定 30 种内容类型** | 你要求「去题目、课本、答案里面找所有需要识别的类型」 | `agent/content_types.py` — 88 页实际试卷采样，4 科 × 7-8 种，含实际频率统计 |
| **5,000 份真题已下载（2.4GB）** | 你要求「爬取所有 available 的 Cambridge A-Level 课本试题答案」 | `crawler/` 模块 + `data/past_papers/` |
| **6 份 PDF 指南已存档（41MB）** | 大量寻找学习资料的过程中保存 | `data/study_guides/pdf/` |
| **144 个免费资源索引** | 深度联网研究结果 | `crawler/resource_index.py` |
| **化学机理图（卷曲箭头）无法自动提取** | 实测搜索确认「目前没有工具能识别」 | `agent/ocr_pipeline.py` + gap_analysis 缺陷 2 |

### 架构层面

| 决策 | 来自对话 | 落实位置 |
|------|---------|---------|
| **10 个题型套路模板** | 你要求「总结题目套路和答案套路」 | `agent/patterns.py` — equilibrium, organic_mechanisms, chem_calculations, kinematics, paper5, circuits, econ_essay_20, econ_data_response, math_integration, math_differentiation |
| **Function Calling 工具路由**（不是多 Agent） | PDF 建议，你认可 | `agent/core.py` TOOLS 列表 + `_execute_tool()` |
| **CLI 聊天界面** | 你要求先做可用的东西 | `chat.py` — cmd.Cmd 子类，支持 /grade、/analyze、subject 切换 |
| **内容类型注册表** | 实测试卷后要求「记录好」 | `agent/content_types.py` — ContentCategory 枚举 + 每科详细配置 + P0/P1/P2 优先级 |
| **OCR 管道 6 引擎** | gap_analysis 中设计的混合方案 | `agent/ocr_pipeline.py` |
| **四维评分 rubric (40/35/15/10)** | PDF 方案设计，你确认 | 计划第三节 grading rubric |
| **error_logs 错因标签**（concept/method/algebra/units/...） | PDF 强调「整个项目最有价值的日志」，你认可 | `agent/core.py` + SQLite schema |

### 关键验证（不是假设，是实测）

| 验证 | 方法 | 结论 |
|------|------|------|
| DeepSeek V4-Flash 价格 | 抓取并解析 [api-docs.deepseek.com](https://api-docs.deepseek.com/quick_start/pricing) | $0.14/$0.28/M |
| 阿里 Qwen3-8b 价格 | 抓取并解析 [help.aliyun.com](https://help.aliyun.com/zh/model-studio/model-pricing) | ¥0.5/¥2/M |
| Qwen-Flash / Qwen3-VL-Flash 成本 | 抓取并解析 [help.aliyun.com](https://help.aliyun.com/zh/model-studio/model-pricing) | 低价但不能按永久免费假设；免费额度/价格随账号、地域、模型版本变化 |
| 腾讯 OCR 价格 | 抓取并解析 [cloud.tencent.com](https://cloud.tencent.com/document/product/866/17619) | ¥0.15/次通用OCR + 1000次/月免费 |
| DeepSeek V4 数学能力 | HF 官方 benchmark table | Flash-Max: HMMT 94.8%, IMOAnswerBench 88.4%；Flash-Base: CMath 93.6%（不同模式/表格，不混作同一调用成本） |
| DeepSeek V4 幻觉率 | artificialanalysis.ai 独立评测 | 94-96% — 必须 RAG+引用来约束 |
| PP-FormulaNet 精度 | arxiv 2503.18382 论文 | 92.22% En-BLEU, 训练数据含 exam papers/textbooks |
| PaddleOCR-VL-1.5 排名 | 腾讯云开发者社区评测 | OmniDocBench 综合第一 (38/40)，超 GLM-OCR 和 DeepSeek-OCR |
| DECIMER 化学 OCR 真实精度 | WildMol benchmark | 56% WildMol, 88% clean images |
| Gradio Server 架构 | HuggingFace 官方博客 2026-04 | gradio.Server extends FastAPI，支持自定义前端 + Gradio 队列/GPU 管理 |

---

## 零-A、当前代码现状（v0.1.0，commit `7873ba0`）

以下模块已写但未端到端验证。计划中的 W1-W2 就是让它们跑通。

| 模块 | 状态 | W1 需要修复 |
|------|------|-----------|
| `agent/core.py` (Agent + tool calling) | 完整 | `grade_homework_image` 工具未真正调用 vision |
| `agent/config.py` (多模型路由) | 完整 | 需配 API key 验证 |
| `agent/prompts.py` (提示词) | 完整 | 四种提示词已写好 |
| `agent/patterns.py` (10 个套路) | 薄 | 需扩展到 50+ 个（W3） |
| `agent/content_types.py` (30 种内容) | 完整 | 无需修改 |
| `agent/ocr_pipeline.py` (6 引擎 OCR) | 框架 | 替换 Surya→PP-FormulaNet, 修复调用 API |
| `agent/retriever.py` (向量搜索) | 完整 | 需 W1 构建 ChromaDB |
| `agent/kb_builder.py` (知识库) | 完整 | chunking 策略改进 |
| `agent/vision.py` (图片批改) | 完整 | 需配 ZHIPU_API_KEY 验证 |
| `chat.py` (CLI 聊天) | 完整 | 无需修改 |
| Web 前端 | **无** | W1.6 用 Gradio Server 搭建 |

### 已完成的「未来兼容」改造（2026-05-26）

以下三件事已在 commit `20ff967` 之后完成，使得未来加 Edexcel/IB/AQA 只需加 JSON 配置文件：

| 改动 | 文件 | 效果 |
|------|------|------|
| Subject 三段式参数化 | `agent/config.py` | `Subject(board="caie-alevel", code="9701", name="Chemistry")` — 支持任意 exam board |
| Patterns JSON 化 | `data/patterns/caie-alevel_9701.json` 等 4 个文件 | 加 Edexcel Math = 加一个 JSON，不改代码 |
| Prompts 变量化 | `agent/prompts.py` | `system_prompt("IB Chemistry HL")` 生成动态提示词，不再硬编码 |
| 动态加载 | `agent/patterns.py` | 新 JSON 文件放入目录即自动加载 |

---

## 零、全部决策的数据来源与验证状态

所有关键判断均经过官方文档或独立基准验证（非 LLM 内建知识）：

| 判断 | 验证源 | 状态 |
|------|--------|------|
| DeepSeek V4-Flash 数学能力 | [DeepSeek官方HF](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash) — Flash-Max: HMMT 94.8%, IMOAnswerBench 88.4%；Flash-Base: CMath 93.6% | ✅ 确认，需按 mode 计成本 |
| DeepSeek V4-Flash vs Qwen 成本效率 | [ominigate.ai](https://ominigate.ai/en/vs/deepseek-v4-flash-vs-qwen3-6-max-preview) — 25x more cost-efficient per AA index point | ✅ 确认 |
| DeepSeek V4 幻觉率 | [artificialanalysis.ai](https://artificialanalysis.ai/articles/deepseek-is-back-among-the-leading-open-weights-models-with-v4-pro-and-v4-flash) — 94-96% hallucination rate | ⚠️ 关键风险 |
| Qwen-Flash / Qwen3-VL-Flash 低价与免费额度 | [阿里百炼官方价格页](https://help.aliyun.com/zh/model-studio/model-pricing) — 国内/国际/全球部署价格和免费额度不同，免费额度不能作为长期成本假设 | ⚠️ 需运行时读取最新价格 |
| PP-FormulaNet_plus-L 精度 | [arxiv 2503.18382](https://ar5iv.labs.arxiv.org/html/2503.18382) — 92.22% En-BLEU, 90.64% Zh-BLEU, trained on exam papers/textbooks | ✅ 确认 |
| PaddleOCR-VL-1.5 文档解析 SOTA | OmniDocBench综合第一(38/40), [腾讯云评测文章](https://cloud.tencent.com/developer/article/2633039) | ✅ 确认 |
| DECIMER 化学 OCR 精度 | [WildMol benchmark](https://arxiv.org/html/2605.05832) — 56% WildMol, 88% clean images; MolScribe 66% WildMol | ✅ 确认 |
| 化学结构识别 SOTA | [ChemVA 2026](https://arxiv.org/html/2605.17214v1) + [GTR-VL 2025](https://arxiv.org/pdf/2506.07553) — functional-group-level perception 是下一代方向 | ✅ 确认 |
| Gradio Server = FastAPI + 前端自由 | [HuggingFace blog 2026-04](https://huggingface.co/blog/introducing-gradio-server) — `gradio.Server` extends FastAPI, supports custom frontend | ✅ 确认 |
| 腾讯 OCR 真实成本 | [腾讯云计费页](https://cloud.tencent.com/document/product/866/17619) — 通用OCR ¥0.15/次+1000次/月免费, 试卷切题 ¥0.24/页, 数学公式 ¥0.15/次 | ✅ 确认 |

---

## 一、整体策略：6 周 → Pilot

**核心洞察**：从搜索验证结果看，这个项目的关键是**分层路由 + 低价/免费额度最大化 + VLM 按需调用**。不要被 PDF 方案的 Web 全栈计划拖慢——用 Gradio 先出可用的 Web 界面。

### 为什么是 6 周而不是 8 周

PDF 方案预计 6-8 周，但考虑了从零搭建 Next.js 前端的时间。实际上：

1. **Gradio Server** 可以在 1 天内搭建一个带聊天、上传、流式输出的 Web App（对比 Next.js 需要 1-2 周）
2. **PP-FormulaNet_plus 和 PaddleOCR-VL-1.5** 是现成的免费 SOTA 方案（不需要像之前以为的那样组合多工具调参）
3. **DeepSeek V4-Flash thinking mode** 一个模型覆盖所有文字辅导需求（不需要为数学/化学/物理分别选模型）

### 为什么这个项目有可能成功

**三个被低估的优势**：
1. **DeepSeek V4-Flash reasoning content** 可转写为解题步骤 → 学生看到整理后的思路，而不是原始 chain-of-thought
2. **PP-FormulaNet_plus 训练数据包含 textbooks/exam papers** → 公式识别是专门为教育场景训练的，不是通用 OCR
3. **低成本足够 pilot** → Qwen-Flash / Qwen3-VL-Flash 价格很低，部分账号/地域有短期免费额度；PaddleOCR 自部署不产生 API 费 → pilot 可低成本启动，但不能按永久 0 成本设计

**四个不可忽视的风险**：
1. **DeepSeek V4 94% 幻觉率** → 不确定时也会给出答案 → 必须用 RAG + citation 约束
2. **化学结构 OCR 没有可靠的免费方案** → DECIMER/MolScribe 在真实场景精度 < 70% → 需要多引擎 + 人工确认
3. **手写数学 OCR 精度 < 60%** → 学生手写作业批改可能是最大的体验问题 → 需要诚实降级策略
4. **免费额度/模型价格会变** → Qwen/视觉模型按地域、账号、版本计费不同 → BudgetGuard 必须以配置表和实际 token 日志为准

---

## 二、分周计划

### Week 1-2：核心闭环（文字 + 图片 + 批改，单科 9709 Math）

**目标**：9709 Math 一条完整链路→ OCR → tutor → grade，在 Gradio Web 界面上跑通。

| # | 任务 | 完成标准 |
|---|------|---------|
| W1.1 | 修复 `ocr_pipeline.py` — 替换 Surya 为 PP-FormulaNet_plus-L | Math formula OCR BLEU > 85% |
| W1.2 | 集成 PaddleOCR-VL-1.5 统一文档解析（文字+表格+公式） | 分三档验收：PDF 渲染页、清晰拍照页、手写答案页；分别记录准确率、median/p95 延迟、低置信率 |
| W1.3 | 接入 DeepSeek V4-Flash API（thinking mode） | 返回 `reasoning_content` + `content`；tool-call 后续轮次能完整回传 `reasoning_content`，不触发 400 |
| W1.4 | 实现 hint-first 教学 → full solution 两步流 | 学生看到：巧提示 → 自己试 → 完整解答 |
| W1.5 | 实现 grading JSON（四维评分 40/35/15/10） | 批改输出结构化 JSON 而非自由文本 |
| W1.6 | 搭建 Gradio Server Web App | ChatInterface + 图片上传 + 流式输出 |
| W1.7 | 准备 50 道 9709 Math 金标题，跑通全流程 | 按 PDF 渲染/清晰拍照/手写答案分层记录：OCR精度、回答质量、批改误差 |
| W1.8 | 写 W1 测试报告 | `plans/week1_report.md` |

**W2 退出标准**：
1. PDF 渲染页/清晰拍照页：50 道数学题上传→OCR→hint→full solution→grade 全流程 > 80% 成功率
2. 手写答案页：不强行要求同等成功率；要求能稳定给出置信度、局部识别结果和「重拍/手动输入」降级提示
3. OCR 报告必须区分 accuracy、低置信率、median/p95 latency，不能只给单一成功率

### Week 3：扩展到 4 科

**目标**：4 科图片题都能 OCR，引用系统上线，低置信降级就绪。

| # | 任务 | 完成标准 |
|---|------|---------|
| W3.1 | 加入 PP-FormulaNet_plus 中文数学公式模式 | 中英文公式混合识别测试通过 |
| W3.2 | 加入 DECIMER + MolScribe 双引擎化学结构 OCR | 每种结构至少一个引擎能正确输出 SMILES |
| W3.3 | 化学机理图（卷曲箭头）→ Qwen3-VL 语义判断 + 保留原图 | 机理题不尝试自动提取，给 VLM 描述 |
| W3.4 | 经济学图表 → Qwen3-VL 解释 + PaddleOCR 轴标签 | 供需图/AD-AS/弹性图识别正确率 > 80% |
| W3.5 | 物理电路/力/波图 → Qwen3-VL 描述 | 图类型识别正确率 > 85% |
| W3.6 | Citation Store seed — 4 科 × 30=120 条 snippet | 优先 examiner report + mark scheme 关键句 |
| W3.7 | OCR 置信度分级 → 降级提示 | <0.5 诚实说「看不清，请重拍或手动输入」 |
| W3.8 | 写 W3 测试报告 | `plans/week3_report.md` |

**W3 退出标准**：4 科各 20 题 OCR，按题面截图/拍照/手写答案分层统计；题面截图与清晰拍照低置信率 < 20%，手写答案允许更高低置信率但必须可解释降级。引用 chip 出现在每个正式答案末尾。

### Week 4：批改校准 + 数据库

**目标**：批改和真人评分对标，错题日志入库。

| # | 任务 | 完成标准 |
|---|------|---------|
| W4.1 | 批改校准 — 每科 20 题金标题 vs 真人评分 | MAE < 0.5/4，相关性 > 0.85 |
| W4.2 | SQLite 数据模型（users, questions, answers, error_logs 等 6 表） | 迁移成功，读写正常 |
| W4.3 | error_logs 自动记录（error_family + error_atom） | 每次批改自动写入错因标签 |
| W4.4 | 对话持久化 — 刷新可看历史 | Gradio ChatInterface 重启后加载历史 |
| W4.5 | 成本日志 + BudgetGuard | 每次 API 调用记录 model/tokens/cost |
| W4.6 | 写 W4 测试报告 | `plans/week4_report.md` |

### Week 5-6：Pilot 准备 + 上线

**目标**：安全合规、Docker 打包、邀请学生试用。

| # | 任务 | 完成标准 |
|---|------|---------|
| W5.1 | 内容安全过滤 + prompt injection 防护 | 违禁词库 + 文件白名单 |
| W5.2 | EXIF 去除 + PII 分离 | 上传图片自动去元数据 |
| W5.3 | 隐私合规（账号删除/导出） | PIPL 基础合规通过 |
| W5.4 | Docker Compose 打包 | `docker-compose up` 一键启动 |
| W5.5 | 准备 5-10 名学生试用 | 演示账号 + 反馈问卷 |
| W5.6 | README + 演示视频 | 3-5 分钟展示全流程 |
| W5.7 | 写 Pilot 总结报告 | `plans/pilot_report.md` |

---

## 三、技术决策总表

### 模型路由

| 任务 | 模型 | 价格 | 原因 |
|------|------|------|------|
| 文字辅导（主力） | DeepSeek V4-Flash (thinking=high) | $0.14/$0.28/M | 1M context，导出 reasoning_content；HMMT/IMO 等高分主要来自 Max/High reasoning 模式，需计入 reasoning token 成本 |
| 文字辅导（轻量） | Qwen-Flash | 低价/短期免费额度 | 概念解释、简单提示；不可把免费额度作为长期假设 |
| 复杂推理 | DeepSeek V4-Flash (thinking=max) | 同上 | 被难住的题才升到 max |
| 视觉图表理解 | Qwen3-VL-Flash | 低价/短期免费额度 | 基础图表识别；价格随地域和版本变化 |
| OCR 文档解析 | PaddleOCR-VL-1.5 | 免费自部署 | 文字+表格+公式一体化，OmniDocBench SOTA |
| 数学公式 OCR | PP-FormulaNet_plus-L | 免费自部署 | 92.22% En-BLEU，专门训练于考试/教材 |
| 化学结构 OCR | DECIMER + MolScribe 双引擎 | 免费自部署 | DECIMER 56% WildMol, MolScribe 66% — 互补 |
| 视觉 fallback | Qwen-VL-OCR 或 GLM-4V-Plus | ¥1-5/M | 低置信时才调用 |
| 手写文本 | PaddleOCR handwriting model | 免费自部署 | 作为候选方案；学生真实手写需本地金标题验证，不能按公开/通用精度直接承诺 |
| 批改评分 | DeepSeek V4-Flash (thinking=high) | 同上 | 四维评分 JSON 输出 |

### 已废弃的方案

| 原方案 | 废弃原因 |
|--------|---------|
| Surya LaTeX OCR 做主公式引擎 | PP-FormulaNet_plus 精度更高（92% vs ~85%），且训练数据包含教育场景 |
| Qwen2.5-Math-7B 做数学批改 | DeepSeek V4-Flash 数学更强 + 更便宜 + 省一个模型调用 |
| 阿里百炼为单一提供商 | DeepSeek 无视觉能力，必须多源 |
| Next.js 从零写前端（Phase 4） | Gradio Server 1 天出 Web，Next.js 留到要商业化时 |
| PostgreSQL + Redis + OSS | SQLite + 本地文件 pilot 完全够用 |

---

## 四、关键设计

### 4.1 DeepSeek V4 幻觉率 94% 的应对

**问题**：DeepSeek V4 不确定时几乎总是给出答案（而不是说「不确定」）。

**方案**：
1. **所有正式答案必须带 citation chip**（强制引用来源，没有来源就不该输出确信答案）
2. **RAG 检索优先**：先搜教材/真题，用检索到的内容约束 LLM 输出
3. **低置信标记**：如果检索结果和 LLM 输出不一致，标记低置信
4. **Examiner Report 优先引用**：ER 里的答案经过了真实考试验证，比 LLM 自由生成可靠

### 4.2 代价：DeepSeek V4-Flash thinking 的 reasoning tokens

DeepSeek thinking mode 会额外产生 reasoning tokens（不计入 `content` 输出而是独立的 `reasoning_content` 字段）。这增加成本但也提供了解题过程的完整可视化。**对学生展示时不直接裸露完整 chain-of-thought，而是展示经过整理的解题步骤**，避免把内部推理噪声当成教学内容。

工程上必须注意：如果 thinking mode 中发生 tool call，DeepSeek API 要求后续请求完整带回上一轮 `reasoning_content`，否则会返回 400。W1.3 必须实现 `ReasoningState`：
1. 保存 assistant 的 `content`、`reasoning_content`、tool calls、tool results
2. 后续 user turn 自动拼回合法 messages
3. 成本日志单独记录 visible output tokens 与 reasoning tokens
4. 展示层只显示整理后的步骤，不把原始 `reasoning_content` 直接暴露给学生

### 4.3 CanonicalQuestion 更新（加入 depends_on）

```json
{
  "subparts": [
    {
      "label": "(a)", "marks": 3, "target_skill": "resolve_forces",
      "expected_answer": {"value": 4.9, "unit": "m/s²", "tolerance": 0.1},
      "depends_on": null, "carry_forward": false
    },
    {
      "label": "(b)", "marks": 4, "target_skill": "use_suvat",
      "depends_on": "(a)", "carry_forward": true,
      "ft_note": "FT from (a) accepted — award method marks if method correct"
    }
  ]
}
```

### 4.4 输出分级策略

| 用户动作 | LLM 调用 | 输出长度 | 预估 cost |
|---------|---------|---------|-----------|
| 拿到提示 (hint) | DeepSeek thinking=off | ~200 tokens | ¥0.001 |
| 请求完整答案 | DeepSeek thinking=high | ~1,500 tokens | ¥0.005 |
| 提交批改 | DeepSeek thinking=high + grading JSON | ~800 tokens | ¥0.004 |
| 图片题（OCR） | PaddleOCR-VL-1.5 (免费) | — | ¥0 |
| 图片题（视觉 fallback） | Qwen3-VL-Flash（低价/免费额度视账号而定） | — | 按实际价格表 |
| 单题总成本 | — | — | **目标 ¥0.001-0.020；以 BudgetGuard 实测为准** |

---

## 五、立即执行

以下命令基于当前项目实际状态——依赖已安装（chromadb + PyMuPDF + sentence-transformers），数据已下载。

```bash
# 1. 配 API Key（把 sk-xxx 替换为真实 key）
export DEEPSEEK_API_KEY=sk-xxx
export ZHIPU_API_KEY=xxx        # 备用视觉。也用百炼的话：export DASHSCOPE_API_KEY=xxx

# 2. 补充安装（已有 chromadb, PyMuPDF, sentence-transformers, requests, rich）
pip install paddleocr paddlepaddle gradio fastapi uvicorn python-dotenv

# 3. 下载 PaddleOCR 模型（首次需等待下载 ~500MB）
python3 -c "
from paddleocr import PaddleOCR
ocr = PaddleOCR(lang='en', use_angle_cls=True, show_log=False)
print('PaddleOCR ready')
"

# 4. 修复 ocr_pipeline.py 以匹配 web search 验证的新方案
#    - agent/ocr_pipeline.py: 替换 Surya LaTeX → PP-FormulaNet_plus-L
#    - agent/ocr_pipeline.py: 添加 DECIMER + MolScribe 双引擎化学 OCR
#    - agent/ocr_pipeline.py: 添加置信度分级 + <0.5 降级逻辑
#    - agent/core.py: grade_homework_image 工具改为真正调用 vision.grade_homework

# 5. 验证 DeepSeek API 连通
python3 -c "
from agent.core import Agent
agent = Agent()
print(agent.chat('What is 2+2? Answer in one word.'))
"

# 6. 构建知识库（教材 + 真题采样 + 学习指南 → ChromaDB）
python3 build_kb.py --subject 9709 --max-papers 30

# 7. 创建 Gradio Web App（替换 CLI 的 chat.py）
#    文件：app.py — Gradio Server + ChatInterface + 图片上传 + 流式输出
#    参考：gr.ChatInterface + gradio.Server（兼容 FastAPI 路由）

# 8. 准备 50 道 9709 Math 金标题
#    从 data/past_papers/9709_mathematics/2022/ 选 P1/P4/P5 各 15-20 题
#    每道题：渲染题目页为 PNG + 记录标准答案 + 标注 mark points

# 9. 逐题跑 OCR → tutor → grade 全流程，记录 accuracy
```

---

## 六、不做的事（明确排除）

| 不做 | 原因 | 何时做 |
|------|------|--------|
| Next.js 前端 | Gradio Server 1 天出，Next.js 留到商业化 | v1.0 之后 |
| PostgreSQL / Redis / OSS | SQLite + 本地文件 pilot 够用 | 用户 > 100 且有付费 |
| 作业自动切题 | 腾讯 ¥0.24/页 可用但加了复杂度 | v1.1 |
| 用户画像 / 智能推荐 | 先验证核心教学功能 | v1.2 |
| 语音输入 / TTS | 与核心教学无关 | v2.0 |
| 多 Agent 协作 | 工具路由就够了 | 永远不必要 |
| 自主出题 | 先做好「学生来问→给出好回答」 | v1.0 之后 |
