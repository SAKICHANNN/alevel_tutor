# Pilot 总结报告 — alevel_tutor v0.2.0

> 生成日期：2026-06-01  
> 项目：Cambridge A-Level AI 辅导 Agent  
> 仓库：github.com/SAKICHANNN/alevel_tutor  
> 总 commits：68

---

## 一、项目概要

构建面向中国 A-Level 学生的 AI 辅导系统，覆盖 CAIE 四科（9701 Chemistry / 9702 Physics / 9708 Economics / 9709 Mathematics），支持教材问答、真题搜索、识图批改、考试套路总结。采用 **DeepSeek V4-Flash API（文字）+ Qwen3-VL-8B LM Studio（视觉）+ Ollama embeddings（检索）+ Qwen3-Reranker（精排）** 的本地+云端混合架构。

## 二、四周完成内容

| 周 | 核心成果 | 关键指标 |
|----|---------|---------|
| W1 | DeepSeek API 连通、PaddleOCR 3.x、Agent 核心回路、50 题测试集 | tool calling + grading JSON 全链路通 |
| W2 | ChromaDB 4 库（26,852 chunks）、RAG 接入 Agent、真题均衡索引 | textbooks 9,456 + papers 16,639 + techniques 47 + syllabi 710 |
| W3 | Qwen3-VL-8B 集成、Ollama embedding、Reranker、Citation Store、OCR 降级 | Reranker 可用（ModelScope），经济学 4th Ed 已索引 |
| W4 | **PedCoT 三路径评分引擎**、SQLite 6 表、cost/error logging、对话持久化、ChromaDB 备份 | 评分 MAE=0.300, r=0.898；100% prompt injection 拦截 |

## 三、技术栈

| 层 | 组件 | 选型 | 原因 |
|----|------|------|------|
| 文字 LLM | DeepSeek V4-Flash | ¥0.14/$0.28 per 1M | 便宜、function calling、thinking mode |
| 视觉 | Qwen3-VL-8B (LM Studio) | 本地免费 | 10s/page，pilot 阶段 0 API 成本 |
| Embedding | Ollama qwen3-embedding:0.6b | 1024d | 稳定，0.14s/chunk |
| Reranker | Qwen3-Reranker-0.6B | ModelScope 本地 | 1s/10pairs，0 API 成本 |
| 向量库 | ChromaDB | PersistentClient | 26,852 chunks，只读查询 |
| 数据库 | SQLite | WAL + single-write lock | 6 表，¥0 成本 |
| Web 前端 | Gradio 4.44.1 | Blocks | 聊天 + 图片上传 + 成本面板 |
| 打包 | Docker Compose | 3 services | web + 可选 Ollama/LM Studio |
| 评分引擎 | PedCoT 两阶段 | MS 匹配 → 自动生成 M-A-B | MAE 0.300, r 0.898 |

## 四、核心创新：PedCoT 三路径评分引擎

```
学生答案 → Path 0: ChromaDB MS 匹配 (Reranker > 0.75?)
               ├─ YES → Path 1: 直接对照真实 MS 评分 (1 API)
               └─ NO  → Path 2: PedCoT 两阶段
                              Stage 1: LLM 盲解 → M-A-B 分配表
                              Stage 2: 提取-对比-逐点打分
                         Path 3: 降级 (任何失败 → score=0)
```

学术基础：Jiang et al. IJCAI 2024 "LLMs can Find Mathematical Reasoning Mistakes by Pedagogical Chain-of-Thought" — 双阶段避免 conformality bias（单阶段 P+ 53% → 双阶段 81%）。

## 五、安全措施（W5 新增）

| 措施 | 实现 |
|------|------|
| Prompt injection 检测 | 24 条正则 + 27 测试案例，100% 拦截（0 FP） |
| 文件上传校验 | 6 种类型白名单、20MB 上限、EXIF 剥离 |
| RAG 内容标记 | 检索内容包裹 untrusted context marker |
| 工具调用白名单 | 6 个允许工具，参数注入检测 |
| 成本预算 | BudgetGuard：月 ¥50 / 日 ¥2 硬限制 |

## 六、当前能力矩阵

| 功能 | 状态 | 备注 |
|------|------|------|
| 文字辅导（四段式教学） | ✅ | 🎯比喻→📖讲解→📝套路→❓检查 |
| 教材搜索 (RAG) | ✅ | 4 科教材 + 真题 + 技巧，Reranker 精排 |
| 真题搜索 | ✅ | 16,639 chunks，按科目/年份/类型过滤 |
| 考试套路模板 | ✅ | 10 个 JSON 模板，动态加载 |
| 作业批改（文字） | ✅ | PedCoT M-A-B 评分 + 四维 rubric |
| 作业批改（图片） | ⚠️ | LM Studio 可用但连续调用不稳定，需云 VLM fallback |
| 图表分析 | ⚠️ | 基础可用，化学机理图无法自动提取 |
| Web 界面 | ✅ | Gradio Blocks，聊天 + 图片上传 + 成本面板 |
| CLI 界面 | ✅ | cmd.Cmd，/grade /analyze /cost /stats /subject |
| 成本追踪 | ✅ | 每次 API 调用自动记账，CLI + Web 面板 |
| 对话持久化 | ✅ | SQLite，重启后可加载历史 |
| Docker 部署 | ✅ | docker-compose up 一键启动 |
| 备份/恢复 | ✅ | ChromaDB + tutor.db 时间戳备份 |

## 七、已知限制

1. **VLM 连续调用不稳定**：Qwen3-VL-8B 热启动 10s/page，连续调用超时。需要云 VLM API（Zhipu GLM-4V / Qwen-VL-Flash）作为 fallback
2. **仅 9709 Math 评分校准完成**：其他三科（Chemistry/Physics/Economics）评分未正式校准
3. **QP 文本提取失败**：2022 试卷 PyMuPDF 提取全是省略号，MS 文本有编码损坏
4. **真人评分对照缺失**：无真实学生数据，gold set 基于 Cambridge 规则人工设定
5. **DeepSeek V4 幻觉率 94%**：用 RAG + citation + 低置信标记缓解，但风险仍在
6. **多用户不支持**：当前单用户 desktop 架构，无用户认证/隔离
7. **手写 OCR 精度未知**：未做真实学生手写答案测试

## 八、成本预估（Pilot 阶段）

假设单学生月均 200 次提问 + 50 次批改：
- 文字 API（DeepSeek V4-Flash）：~¥1-3/月
- 视觉：LM Studio 免费（本地），偶尔云 fallback ~¥1-2/月
- Embedding + Reranker：本地免费
- **总计：¥2-5/月/学生**（在 ¥20/月预算内）

## 九、下一步（W6）

| 需要人 | 任务 |
|--------|------|
| ✅ 可以马上做 | 多科目评分校准（9701/02/08）、QP+MS 自动映射 |
| ⚠️ 需要人 | 旋转 DeepSeek API key（旧 key 曾暴露）、找 5-10 名学生试用、录制演示视频 |

## 十、文档索引

- 开发计划：`docs/plans/development_plan.md`（439 行，2026-05-26）
- W1 日志：`docs/log/w1.md`（287 行）
- W2 日志：`docs/log/w2.md`（197 行）
- W3 日志：`docs/log/w3.md`（725 行）
- W4 日志：`docs/log/w4.md`（664 行）
- W5 计划：`docs/plans/week5_plan.md`（57 行）
- 数据获取：`SETUP_DATA.md`
