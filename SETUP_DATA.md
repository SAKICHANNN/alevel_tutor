# 完整数据集获取指南

本指南确保你可以在任何新机器上完全复现项目所需的**全部本地数据**（~10GB）。

---

## 数据全景图

```
data/                              # ~10GB 总计
├── past_papers/                   # 2.4GB — 真题试卷 (QP+MS+ER+GT+CI)
│   ├── 9701_chemistry/            #   708MB, 1,364 文件, 2001-2022
│   ├── 9702_physics/              #   792MB, 1,344 文件, 2002-2022
│   ├── 9708_economics/            #   372MB, 869 文件, 2001-2022
│   ├── 9709_mathematics/          #   554MB, 1,422 文件, 2001-2022
│   └── manifest.json
│
├── textbooks/                     # 教材 PDF
│   ├── 9701_chemistry/            #   Chemistry Coursebook (Ryan & Norris) — 自动下载
│   ├── 9702_physics/              #   Physics Coursebook 2nd Ed (David Sang) — 自动下载
│   ├── 9709_mathematics/          #   Pure Math 1 Coursebook (Sue Pemberton) — 自动下载
│   └── 9708_economics/            #   Economics Coursebook 4th Ed (Bamford & Grant) — ⚠️ 需手动下载
│
├── syllabus/                      # 8MB — 官方 Cambridge syllabus PDF（✅ 已提交 Git）
│   ├── 9701_chemistry_syllabus.pdf        # 4.0MB, 2025-2027
│   ├── 9702_physics_syllabus.pdf          # 2.5MB, 2025-2027
│   ├── 9708_economics_syllabus.pdf        # 0.6MB, 2026-2028
│   └── 9709_mathematics_syllabus.pdf      # 1.2MB, 2026-2027
│
├── study_guides/                  # 40MB — 备考指南（✅ 已提交 Git）
│   ├── *.md                       #   4 份 Markdown 技巧总结
│   └── pdf/                       #   6 份 PDF（Examiner Tips + Example Responses + Learner Guide）
│
├── patterns/                      # 已提交 Git — 4 个 JSON 套路模式库
├── eval/
│   ├── test_questions_9709.json        # 50 道 9709 测试题（✅ 已提交）
│   └── citation_store_seed.json       # 101 条 examiner report snippet（✅ 已提交）
│
├── repo/                          # 3.9GB — ⚠️ Git 稀疏检出缓存，不提交
└── chroma_db/                     # 运行时生成 — 向量数据库（~180MB SQLite）
```

---

## 一、快速开始（克隆 + 一键获取全部数据）

```bash
# 1. 克隆代码
git clone https://github.com/SAKICHANNN/alevel_tutor.git
cd alevel_tutor

# 2. 安装依赖
pip install -r requirements.txt
pip install paddlepaddle paddleocr "paddlex[ocr]" ftfy  # PaddleOCR
pip install chromadb sentence-transformers                # 向量数据库 + 备用 embeddings
pip install fastapi uvicorn python-dotenv                 # Web + 配置

# 3. 获取全部真题试卷（2.4GB）
python3 tools/scripts/run_crawler.py

# 4. 获取教材 PDF（自动下载 3 本，第 4 本见下方手动步骤）
python3 tools/scripts/download_textbooks.py

# 5. 配置 API Key
echo 'DEEPSEEK_API_KEY=sk-xxx' > .env

# 6. 下载 Ollama 模型（本地 embedding + 视觉）
ollama pull qwen3-embedding:0.6b   # 向量嵌入（1024 维，0.6GB）
ollama pull qwen3-embedding:4b     # 更大嵌入模型（2.5GB，可选）
ollama pull qwen3-embedding:8b     # 最大嵌入模型（4.7GB，可选）

# 7. 在 LM Studio 中加载 VLM 模型
#    搜索并下载 qwen/qwen3-vl-8b，启动 Local Server (端口 1234)

# 8. 构建知识库（PDF → ChromaDB 向量）
python3 build_kb.py

# 9. 验证
PYTHONPATH=. python3 tests/test_all.py
```

---

## 二、逐个数据集详解

### 2.1 真题试卷（past_papers/）

**来源**：GitHub 镜像 [`caie-exams/pastpapers`](https://github.com/caie-exams/pastpapers)（A-Levels 分支）

**获取**：
```bash
python3 tools/scripts/run_crawler.py
```

**内容**：
- **qp** (Question Paper) — 考试题目
- **ms** (Mark Scheme) — 标准答案 + 评分标准
- **er** (Examiner Report) — 考官报告 + 常见错误分析
- **gt** (Grade Threshold) — 分数线
- **ci** (Confidential Instructions) — 实验指导（化学/物理）

**更新**：再次运行即可 `git pull` 最新年份。

---

### 2.2 教材 PDF（textbooks/）

**来源**：公开教育资源站

**自动下载 3 本**（`python3 tools/scripts/download_textbooks.py`）：

| 教材 | 大小 | 自动来源 |
|------|------|---------|
| Chemistry Coursebook (Ryan & Norris) | 36.5MB | exampaperspractice.co.uk |
| Physics Coursebook 2nd Ed (David Sang) | 27.1MB | cienotes.com |
| Pure Mathematics 1 (Sue Pemberton) | 24.7MB | learnedguys.com |

**需手动下载 1 本**（Economics 4th Edition，自动下载失败）：

| 教材 | 手动下载 URL |
|------|------------|
| Economics Coursebook 4th Ed (Bamford & Grant) | https://annas-archive.org/md5/f3800227814f467f7e7b52a89c114845 |

下载后放到 `data/textbooks/9708_economics/`。

另外经济学还有 Hodder 版（Peter Smith, 2nd Ed）在：
- https://pdfcoffee.com/hodder-education-cambridge-international-as-and-a-level-economics-pdf-free.html

---

### 2.3 Syllabus PDF（data/syllabus/）

**✅ 已提交 Git**，4 份最新官方考纲直接跟随代码库。

URL 记录（如需更新版本时重下载）：
```
9701 Chemistry:  https://www.cambridgeinternational.org/Images/664563-2025-2027-syllabus.pdf
9702 Physics:    https://www.cambridgeinternational.org/Images/664565-2025-2027-syllabus.pdf
9708 Economics:  https://www.cambridgeinternational.org/Images/697423-2026-2028-syllabus.pdf
9709 Math:       https://www.cambridgeinternational.org/Images/697427-2026-2027-syllabus.pdf
```

---

### 2.4 学习指南 PDF（study_guides/）

**✅ 已提交 Git**，6 份 PDF：

| 文件 | 大小 | 来源 |
|------|------|------|
| chemistry_examiner_tips.pdf | 100KB | learnedguys.com |
| chemistry_example_responses.pdf | 4.0MB | nvdiaries.weebly.com |
| chemistry_learner_guide.pdf | 29MB | sharpschool.com |
| economics_specimen_answers_p4.pdf | 854KB | learnedguys.com |
| physics_example_responses_p3.pdf | 4.1MB | learnedguys.com |
| physics_example_responses_p5.pdf | 2.4MB | xtremepape.rs |

---

### 2.5 套路模式库（patterns/）

**✅ 已提交 Git**，4 个 JSON 文件，10 个套路模板。

加新科目/考试局的套路：在 `data/patterns/` 下新建 `{board}_{code}.json`，格式参照已有文件。

---

### 2.6 测试集（eval/）

**✅ 已提交 Git**：

| 文件 | 内容 |
|------|------|
| test_questions_9709.json | 50 道 9709 数学真题，按 topic 分类 |
| citation_store_seed.json | 101 条 examiner report snippet |

---

### 2.7 向量数据库（chroma_db/）

**运行时生成**。构建命令：
```bash
python3 build_kb.py
```

需要使用 **Ollama qwen3-embedding** 模型（本地免费）。4 个 collection：

| Collection | 内容 | Chunks | Embedding |
|-----------|------|--------|-----------|
| textbooks | 3 本教材 | 6,367 | qwen3-embedding:0.6b, 1024d |
| past_papers | 211 份真题 | 16,639 | 同上 |
| techniques | 4 份 Markdown | 47 | 同上 |
| syllabi | 4 份考纲 | 710 | 同上 |
| **总计** | | **23,763** | |

没有 Ollama 时 fallback 到 `sentence-transformers/all-MiniLM-L6-v2`（384d），但会触发 79MB 模型下载。

---

### 2.8 LM Studio 视觉模型

用于 OCR（公式提取、图表分析、手写批改）：

| 模型 | 大小 | 下载 |
|------|------|------|
| qwen/qwen3-vl-8b | ~5GB | LM Studio 内搜索下载 |
| qwen/qwen3-vl-30b | ~15GB | 更大，可选 |

启动后确保 Local Server 在 `http://127.0.0.1:1234`。

---

## 三、完整依赖列表

### 3.1 Python 包

见 `requirements.txt`。额外需要：

```bash
pip install paddlepaddle paddleocr "paddlex[ocr]" ftfy  # OCR 引擎
pip install chromadb sentence-transformers                # 向量数据库
pip install fastapi uvicorn python-dotenv                 # API + 配置
pip install gitpython requests rich                       # 爬虫 + UI
```

### 3.2 外部服务

| 服务 | 用途 | 必需 |
|------|------|------|
| DeepSeek API (deepseek-v4-flash) | 文字辅导、批改 | ✅ 不可替代 |
| Ollama (本地) | 向量嵌入 + VLM 离线 fallback | ⚠️ 可 fallback 到 sentence-transformers |
| LM Studio (本地) | Qwen3-VL 视觉分析 | ⚠️ 可跳过（无图片功能） |
| Zhipu/Qwen Cloud API | 云端视觉 fallback | ❌ 可选 |

---

## 四、验证数据完整性

```bash
# 所有数据集验证
PYTHONPATH=. python3 tests/test_all.py

# 应输出：RESULTS: 57 passed, 0 failed, 0 skipped

# 知识库状态
PYTHONPATH=. python3 -c "
from agent.retrieval.search import get_collection_stats
for k,v in get_collection_stats().items():
    print(f'{k}: {v[\"count\"]} chunks')
"
# textures: 6367 / past_papers: 16639 / techniques: 47

# 数据量
du -sh data/past_papers/ data/textbooks/ data/syllabus/
# past_papers: 2.4GB / textbooks: ~88MB / syllabus: 8MB
```

---

## 五、URL 速查表（所有数据来源）

| 数据 | URL |
|------|-----|
| 真题试卷 | https://github.com/caie-exams/pastpapers (A-Levels 分支) |
| Chemistry Coursebook | https://www.exampaperspractice.co.uk/wp-content/uploads/CambridgeInternationalASALevelChemistryCoursebook.pdf |
| Physics Coursebook | https://www.cienotes.com/wp-content/uploads/2018/07/Cambridge-International-AS-and-A-Level-Physics-Coursebook-by-David-Sang-Graham-Jones-Gurinder-Chadha-and-Richard-Woodside.pdf |
| Pure Math 1 Coursebook | https://www.learnedguys.com/uploads/files/335/Cambridge%20International%20AS%20A%20Level%20Mathematics%20Pure%20Mathematics%201.pdf |
| Economics 4th Ed (手动) | https://annas-archive.org/md5/f3800227814f467f7e7b52a89c114845 |
| Economics Hodder 2nd Ed | https://pdfcoffee.com/hodder-education-cambridge-international-as-and-a-level-economics-pdf-free.html |
| 9701 Syllabus | https://www.cambridgeinternational.org/Images/664563-2025-2027-syllabus.pdf |
| 9702 Syllabus | https://www.cambridgeinternational.org/Images/664565-2025-2027-syllabus.pdf |
| 9708 Syllabus | https://www.cambridgeinternational.org/Images/697423-2026-2028-syllabus.pdf |
| 9709 Syllabus | https://www.cambridgeinternational.org/Images/697427-2026-2027-syllabus.pdf |
| Examiner Tips (Chem) | https://www.learnedguys.com/uploads/files/288/Examiner%20tips.pdf |
| Example Responses (Chem) | https://nvdiaries.weebly.com/uploads/7/9/6/5/79657776/9701_chemistry_example_candidate_responses_2013.pdf |
| Learner Guide (Chem) | https://cdnsm5-ss20.sharpschool.com/UserFiles/Servers/Server_4787602/File/Academics/Magnet%20Program%20-%20Cambridge%20AICE/Chemistry%209701_Learner_Guide_(for_examination_from_2022).pdf |
| Example Responses P3 (Phys) | https://www.learnedguys.com/uploads/files/350/9702_Example_Candidate_Responses_Paper_3_(for_examination_from_2016).pdf |
| Example Responses P5 (Phys) | https://papers.xtremepape.rs/CAIE/AS%20and%20A%20Level/Physics%20(9702)/ECR_AS-AL_Physics_9702_P5_v1.pdf |
| Specimen Answers P4 (Econ) | https://www.learnedguys.com/uploads/files/2094/9708_Specimen_Paper_Answers_Paper_4_(for_examination_from_2023).pdf |
