# New Chat Prompt — alevel_tutor Continuation

你正在开发 `alevel_tutor`，一个 Cambridge A-Level AI 辅导 agent。项目在 `/Users/miaomiao/alevel_assistant`。

## 快速验证环境

```bash
cd /Users/miaomiao/alevel_assistant
PYTHONPATH=. python3 tests/test_all.py  # 应该 57/57 全通过
```

## 当前状态

- **W1-W3 全部完成**（86 commits，mastering）
- **W4 待开始**：批改校准 + SQLite 数据库 + Reranker 生产接入
- **主要功能全部可用**：Agent 辅导、RAG 搜索、OCR、VLM 视觉、Grading JSON、Citation、Reranker

## 架构

```
图片 → PaddleOCR(文字) + Qwen3-VL-8B(LM Studio本地, 图表/公式)
文字 → DeepSeek V4-Flash API ($0.14/$0.28 per 1M tokens)
向量 → ChromaDB (4 collections, 26,142 chunks, Ollama qwen3-embedding:0.6b 1024d)
Reranker → Qwen3-Reranker-0.6B (ModelScope 缓存, cross-encoder)
```

## API Keys (.env 文件, gitignored)

```
DEEPSEEK_API_KEY=sk-xxx
```

## 本地服务

```bash
# Ollama (embedding models)
ollama list  # qwen3-embedding:0.6b, qwen3-embedding:4b, qwen3-embedding:8b

# LM Studio (VLM)
# 模型: qwen/qwen3-vl-8b, 端口 1234
# GUI → Local Server → Start Server
```

## 关键目录

```
agent/              核心代码
  ocr/              OCR管道(pipeline, vision, content_types)
  tutoring/         教学引擎(core, prompts, patterns)
  retrieval/        检索(search, builder, reranker)
tools/
  crawler/          数据采集
  scripts/          运行脚本
docs/
  plans/            开发计划
  log/              w1.md, w2.md, w3.md (共 1,500+ 行，完整日志)
data/
  past_papers/      2.4GB 真题 (gitignored)
  textbooks/        4本教材 (gitignored)
  syllabus/         4份考纲 (committed)
  study_guides/     备考指南 (committed)
  eval/             测试题集 + citation store (committed)
  chroma_db/        向量库 (gitignored)
SETUP_DATA.md       完整数据获取指南 (16个URL)
```

## 当前 KB 状态

```
textbooks:   9,456 chunks (Chem+Phys+Math+Econ)
past_papers: 16,639 chunks (qp/ms/er/gt for 4 subjects)
techniques:  47 chunks
syllabi:     710 chunks
Total:       26,852 chunks
Embedding:   qwen3-embedding:0.6b (1024d)
```

## Agent 能力

- `chat.py` — CLI 聊天界面 (`/grade`, `/analyze`, `subject` 切换)
- `build_kb.py` — 构建 ChromaDB 知识库
- 文字辅导：比喻→步骤→套路→检查 四段式
- Grading JSON：四维评分 (correctness/method/representation/communication)
- 5 个 search tool + 10 个 exam pattern
- Reranker: `search_textbooks(use_rerank=True)`
- 视觉提取: `extract_images_from_pdf()`, `extract_cross_page()`, `analyze_image_file()`

## W4 待做（docs/plans/development_plan.md）

1. 批改校准 (W4.1) — gold set vs 真人评分
2. SQLite 数据模型 (W4.2) — 6 表
3. error_logs (W4.3)
4. 对话持久化 (W4.4)
5. 成本日志 + BudgetGuard (W4.5)
6. ChromaDB 持久化策略 (W4.6)
7. Reranker 生产接入 (W4.8) — 代码已就绪，模型已下载

## 已知待决策

1. **4b embedding 升级**：设 `EMBED_MODEL=qwen3-embedding:4b` + `python3 build_kb.py` 重建(~3h)。当前 0.6b 稳定。
2. **VLM 速度**：本地 10s/page，连续调用不稳定。交互建议云 API。
3. **Economics 教材**：4th Ed 已下载并索引。

## 快速开始

```bash
cd /Users/miaomiao/alevel_assistant
source .env  # 或 export DEEPSEEK_API_KEY=...
PYTHONPATH=. python3 chat.py --subject 9709
```

## 阅读顺序

1. `docs/log/w3.md` §18 — 所有被否定方案的教训
2. `docs/plans/development_plan.md` — 完整计划
3. `SETUP_DATA.md` — 数据获取指南
4. `tests/test_all.py` — 验证环境
