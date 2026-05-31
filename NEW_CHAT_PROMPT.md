# New Chat Prompt — alevel_tutor 继续开发

> 把这个文件粘贴到新 chat 的第一条消息。

---

你正在开发 `alevel_tutor`，一个 Cambridge A-Level AI 辅导 agent。
项目路径：`/Users/miaomiao/alevel_assistant`

## 一键验证环境

```bash
cd /Users/miaomiao/alevel_assistant
PYTHONPATH=. python3 tests/test_all.py   # 目标 57/57 全通过
python3 chat.py --subject 9709            # CLI 聊天测试
```

---

## 项目全貌

### 已完成：W1-W3（86 commits）

W1 核心回路：DeepSeek API → PaddleOCR → Agent 辅导 → Grading JSON → 50题测试集
W2 知识库：ChromaDB 四库构建 → RAG 搜索 → 经济学课本 → bug 修复
W3 视觉+高级：Qwen VLM 集成 → OCR 简化 → Exam-board 元数据 → Citation Store → Reranker

### 待开始：W4

1. 批改校准（W4.1）— gold set vs 真人评分
2. SQLite 数据模型（W4.2）— 6 表
3. error_logs 自动记录（W4.3）
4. 对话持久化（W4.4）
5. 成本日志 + BudgetGuard（W4.5）
6. ChromaDB 持久化策略（W4.6）
7. Reranker 生产接入（W4.8）— 代码已就绪，模型已下载到 ModelScope 缓存

---

## 文件结构详解

```
alevel_assistant/
├── chat.py                    CLI入口。cmd.Cmd子类，支持文字聊天、/grade批改、/analyze图表、subject切换
├── build_kb.py                KB构建入口。python3 build_kb.py 重建全部ChromaDB集合
├── requirements.txt           完整Python依赖（但缺paddlex[ocr], ftfy, sentence-transformers）
├── SETUP_DATA.md              16个数据源URL + 获取步骤 + GitHub策略
├── NEW_CHAT_PROMPT.md         本文件
├── .env                       API key（gitignored）
├── .env.example               API key模板
│
├── agent/
│   ├── config.py              LLM路由(DeepSeek/Zhipu/Qwen/LM Studio) + Subject注册表 + .env加载
│   ├── ocr/
│   │   ├── pipeline.py        主OCR管道：PaddleOCR文字(0.5s) + Qwen VLM全页解析(10-60s)
│   │   │                      含 extract_images_from_pdf(), extract_cross_page(), analyze_image_file()
│   │   ├── vision.py          视觉批改/图表分析：_call_vision_api() 统一GLM/Qwen/LM Studio
│   │   └── content_types.py   30种内容类型注册表（4科×7-8种，P0/P1/P2优先级）
│   ├── tutoring/
│   │   ├── core.py            Agent核心：tool calling(6个工具) + _call_llm(retry) + grade() + _detect_subject()
│   │   ├── prompts.py         system_prompt(welcome_message, grading_prompt) + JSON grading模板
│   │   └── patterns.py        10个题型套路模板（从JSON动态加载）
│   └── retrieval/
│       ├── search.py          向量搜索：_query_with_ollama() + search_textbooks/past_papers/techniques
│       ├── builder.py         知识库构建：OllamaEmbedFn + _chunk_text + _is_quality_chunk + build_all
│       └── reranker.py        两阶段检索：CrossEncoder(Qwen3-Reranker-0.6B) + pad_token修复
│
├── tools/
│   ├── crawler/               真题/教材爬虫（git sparse-checkout → 整理 → 索引）
│   │   ├── config.py          科目定义 + 文件命名正则 + FILE_TYPES映射
│   │   ├── downloader.py      git clone --filter=blob:none --sparse
│   │   ├── organizer.py       按 科目/年份/类型(qp/ms/er/gt) 整理
│   │   ├── pipeline.py        完整获取流程
│   │   ├── resource_index.py  144个免费在线资源索引
│   │   ├── techniques.py      4科Markdown技巧总结生成器
│   │   └── textbooks.py       教材下载器（3本自动+1本手动）
│   └── scripts/
│       ├── run_crawler.py      运行爬虫
│       ├── download_textbooks.py  下载教材
│       ├── master_summary.py   资源汇总
│       └── summary.py          简要汇总
│
├── docs/
│   ├── plans/
│   │   ├── development_plan.md    8周开发计划v3（含reranker §4.2B, 所有决策记录）
│   │   ├── gap_analysis_and_solutions.md  10个缺陷分析 + 606行附录
│   │   ├── Agentic Tutor MVP for Chinese A-Level Students.pdf  英文原始参考方案
│   │   └── agentic_tutor_zh_report.pdf  中文版详细方案（26页）
│   └── log/
│       ├── w1.md (287行, 10节)  W1：API + OCR + grading + test set + structure
│       ├── w2.md (197行, 6节)   W2：KB + RAG + bugs + reranker architecture
│       └── w3.md (655行, 18节)  W3：VLM + OCR简化 + Econ + embeddings + reranker + 所有被否定方案
│
├── tests/
│   └── test_all.py             57项全面测试（chat, tools, grading, retrieval, detection, OCR, config, thinking）
│
└── data/
    ├── past_papers/           2.4GB, gitignored（qp/ms/er/gt/ci, 2001-2022）
    ├── textbooks/             4本教材, gitignored
    │   ├── 9701_chemistry/     Chemistry Coursebook (Ryan & Norris, 36.5MB)
    │   ├── 9702_physics/       Physics Coursebook 2nd Ed (David Sang, 27.1MB)
    │   ├── 9709_mathematics/   Pure Math 1 (Sue Pemberton, 24.7MB)
    │   └── 9708_economics/     Economics 4th Ed (Bamford & Grant, 49MB)
    ├── syllabus/              4份考纲PDF (8MB, committed)
    ├── study_guides/          6份备考PDF + 5份MD (committed)
    ├── patterns/              4个JSON套路库 (committed)
    ├── eval/
    │   ├── test_questions_9709.json   50道9709测试题
    │   └── citation_store_seed.json   101条examiner report snippet
    └── chroma_db/             向量库 (gitignored, ~180MB SQLite)
```

---

## API Keys & 外部服务

### .env 文件（gitignored）
```bash
DEEPSEEK_API_KEY=sk-xxx
ZHIPU_API_KEY=    # 未配置（可选）
DASHSCOPE_API_KEY= # 未配置（可选）
```

### 模型路由（agent/config.py MODELS dict）

| Key | Provider | Model | 用途 | 价格 |
|-----|----------|-------|------|------|
| `tutor` | deepseek | deepseek-v4-flash | 文字辅导 | $0.14/$0.28 per 1M |
| `reasoner` | deepseek | deepseek-v4-flash + thinking=True | 复杂推理 | 同上 |
| `fast` | deepseek | deepseek-v4-flash | 简单任务(低temp) | 同上 |
| `vision` | zhipu | glm-4v-plus | 云视觉(未配key) | ¥5/M |
| `vision_qwen` | qwen | qwen-vl-max | 云视觉(未配key) | ¥3/$9 per 1M |
| `vision_local` | lmstudio | qwen/qwen3-vl-8b | **本地视觉(当前)** | 免费 |

`get_active_vision_model()` 优先级：vision_local → vision → vision_qwen

### 本地服务

**Ollama**（embedding）：
```bash
ollama list
# qwen3-embedding:0.6b  (1024d, 当前使用, 0.14s/chunk)
# qwen3-embedding:4b    (2560d, 升级路径, 0.5s/query, 82% better semantics)
# qwen3-embedding:8b    (4096d, 最大)
# text-embedding-nomic-embed-text-v1.5 (备用)
```
当前使用 0.6b。换 4b：`EMBED_MODEL=qwen3-embedding:4b python3 build_kb.py`（~3h重建）

**LM Studio**（VLM视觉）：
- 模型：`qwen/qwen3-vl-8b`
- 端口：`127.0.0.1:1234`
- 速度：热启动10s/page，连续调用不稳定（120-300s timeout）
- 启动：GUI → Local Server → Start Server

---

## ChromaDB 知识库状态

```
Collection     | Chunks  | Embedding                    | 来源
textbooks      | 9,456   | qwen3-embedding:0.6b (1024d) | 4本教材 (Chem+Phys+Math+Econ)
past_papers    | 16,639  | qwen3-embedding:0.6b (1024d) | 211 PDFs (4科×10 per type)
techniques     | 47      | qwen3-embedding:0.6b (1024d) | 5份MD + patterns
syllabi        | 710     | qwen3-embedding:0.6b (1024d) | 4份考纲PDF
TOTAL          | 26,852  |                              |
```

搜索质量：0.6b 语义分离弱（gap 0.076），但 Reranker 补偿。0.6b 检索 100% 命中（8/8 < 0.85 threshold）。

### 重建命令
```bash
python3 build_kb.py                          # 重建全部集合 (~51min)
python3 build_kb.py --subject 9708           # 只重建经济
python3 build_kb.py --max-per-type 5         # 少索引一些论文(更快)
```

---

## 关键代码约定

### 搜索函数签名
```python
search_textbooks(query, subject_code=None, n_results=5, use_rerank=False)
search_past_papers(query, subject_code=None, paper_type=None, n_results=5, use_rerank=False)
search_techniques(query, subject_code=None, n_results=3)
# use_rerank=True → 取2×候选 → reranker排序 → 返回top_n
```

### Agent 工具调用
6个工具：`search_textbook`, `search_past_paper`, `get_exam_pattern`, `search_exam_techniques`, `grade_homework_image`, `get_subject_info`

### Subject 系统
```python
from agent.config import SUBJECTS, SUBJECT_BY_CODE, register_subject
# 4个CAIE科目 + 动态注册新科目
# register_subject('ib-dp', 'chem-hl', 'Chemistry HL', 'HL', ...)
```

### 视觉函数
```python
extract_images_from_pdf(pdf_path, subject_code, page_range, min_drawings=0)
# 自动跳过封面/空白/纯文本页，渲染矢量图+提取嵌入图 → Qwen VLM
extract_cross_page(pdf_path, subject_code, start_page, end_page)
# 连续多页一起发送VLM，用于跨页内容
analyze_image_file(image_path, subject_code="")
# 任意PNG/JPG文件分析
```

### Grading
```python
agent.grade(question, mark_scheme, student_answer) → dict
# 返回 {"score_awarded": 2, "score_max": 2, "rubric": {...}, "misconception_tags": [...]}
```

---

## 已知问题和限制

1. **4b embedding 升级失败**：后台进程 died silently，textbooks只到539 chunks。4b代码保留，env var控制。
2. **VLM 连续调用不稳定**：LM Studio 连续请求会 timeout。单次10s可接受。
3. **0.6b 嵌入语义弱**：gap 0.076。Reranker 部分补偿。4b 是最终解。
4. **Economics 概念搜索**：用 Reranker 后改善明显（score 0.9），无 Reranker 时 dist=0.623 仍可用。
5. **PyMuPDF 文本提取有公式损坏**：`f(x)` → `f\u0000x\u0001`，不宜用于公式搜索。
6. **ChromaDB PersistentClient 不能多进程**：当前单进程 OK。
7. **HF/hf-mirror 在中国不稳定**：ModelScope 替代。Ollama 模型直接可用。
8. **DeepSeek V4 幻觉率 94%**：用 RAG + citation 约束。

---

## 常用命令

```bash
cd /Users/miaomiao/alevel_assistant

# 环境
source .env
export PYTHONPATH=.

# 测试
python3 tests/test_all.py                    # 57项全测试

# 聊天
python3 chat.py                              # 默认启动
python3 chat.py --subject 9709               # 指定科目

# KB
python3 build_kb.py                          # 重建全部
python3 -c "from agent.retrieval.search import get_collection_stats; print(get_collection_stats())"

# 验证搜索
python3 -c "
from agent.retrieval.search import search_textbooks
r = search_textbooks('Le Chatelier', '9701', use_rerank=True)
print(r[0]['content'][:100])
"

# 视觉提取（需要LM Studio运行）
python3 -c "
from agent.ocr.pipeline import extract_images_from_pdf
r = extract_images_from_pdf('data/past_papers/9702_physics/2022/qp/9702_m22_qp_42.pdf', '9702', (5,6))
print(r[0].get('page_analysis',''))
"
```

---

## 阅读建议（新chat理解项目的最短路径）

1. `NEW_CHAT_PROMPT.md`（本文件）
2. `docs/log/w3.md` §18（所有被否定方案的教训）
3. `docs/plans/development_plan.md`（完整计划 v3）
4. `SETUP_DATA.md`（数据获取指南，16个URL）
5. `tests/test_all.py`（了解所有子系统如何调用）
