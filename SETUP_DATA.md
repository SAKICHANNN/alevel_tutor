# 完整数据集获取指南

本指南确保你可以在任何新机器上复现项目所需的**全部本地数据**（6.5GB）。

## 数据全景图

```
data/                          # 6.5GB 总计
├── past_papers/               # 2.4GB — 真题试卷 (QP+MS+ER+GT)
│   ├── 9701_chemistry/        #   708MB, 1,364 文件, 2001-2022
│   ├── 9702_physics/          #   792MB, 1,344 文件, 2002-2022
│   ├── 9708_economics/        #   372MB, 869 文件, 2001-2022
│   ├── 9709_mathematics/      #   554MB, 1,422 文件, 2001-2022
│   └── manifest.json          #   172KB, 所有文件索引
│
├── textbooks/                 # 88MB — 教材 PDF
│   ├── 9701_chemistry/        #   36.5MB Chemistry Coursebook (Ryan & Norris)
│   ├── 9702_physics/          #   27.1MB Physics Coursebook (David Sang)
│   └── 9709_mathematics/      #   24.7MB Pure Math 1 Coursebook (Sue Pemberton)
│
├── study_guides/              # 40MB — ✅ 已提交 Git
│   ├── *.md                   #   4 份 Markdown 技巧总结
│   └── pdf/                   #   6 份 PDF 备考指南
│       ├── chemistry_examiner_tips.pdf       (100KB)
│       ├── chemistry_example_responses.pdf   (4.0MB)
│       ├── chemistry_learner_guide.pdf       (29MB)
│       ├── economics_specimen_answers_p4.pdf (854KB)
│       ├── physics_example_responses_p3.pdf  (4.1MB)
│       └── physics_example_responses_p5.pdf  (2.4MB)
│
├── patterns/                  # ✅ 已提交 Git — 4 个 JSON 套路库
├── repo/                      # 3.9GB — ⚠️ Git 稀疏检出缓存，不需要提交
├── chroma_db/                 # 运行时生成 — 向量数据库索引
└── content_samples/           # 临时 — 采样图片，不需要提交
```

---

## 一、快速开始（克隆 + 一键获取全部数据）

```bash
# 1. 克隆代码
git clone https://github.com/SAKICHANNN/alevel_tutor.git
cd alevel_tutor

# 2. 安装依赖
pip install -r requirements.txt
pip install paddleocr paddlepaddle gradio fastapi uvicorn python-dotenv

# 3. 获取全部真题试卷（2.4GB，从 GitHub 镜像下载）
python3 scripts/run_crawler.py

# 4. 获取教材 PDF（88MB，从公开资源站下载）
python3 scripts/download_textbooks.py

# 5. 配置 API Key
echo 'DEEPSEEK_API_KEY=sk-xxx' > .env

# 6. 构建知识库（PDF → ChromaDB 向量）
python3 build_kb.py
```

---

## 二、逐个数据集详解

### 2.1 真题试卷（past_papers/）

**来源**：GitHub 镜像 [`caie-exams/pastpapers`](https://github.com/caie-exams/pastpapers)（A-Levels 分支）

**获取方式**：
```bash
python3 scripts/run_crawler.py
```

**原理**：`crawler/downloader.py` 使用 `git clone --filter=blob:none --sparse` 只拉取 4 个科目的目录，不下载整个仓库。`crawler/organizer.py` 按 `科目/年份/类型(qp/ms/er/gt)` 整理。

**包含内容**：
- **qp** (Question Paper) — 考试题目
- **ms** (Mark Scheme) — 标准答案 + 评分标准
- **er** (Examiner Report) — 考官报告 + 常见错误分析
- **gt** (Grade Threshold) — 分数线
- **ci** (Confidential Instructions) — 实验指导（仅化学/物理）

**更新**：再次运行 `python3 scripts/run_crawler.py` 即可 git pull 最新年份。

---

### 2.2 教材 PDF（textbooks/）

**来源**：公开教育资源站（exampaperspractice.co.uk, cienotes.com, learnedguys.com）

**获取方式**：
```bash
python3 scripts/download_textbooks.py
```

**已自动下载 3 本**：
| 教材 | 大小 | 来源 |
|------|------|------|
| Chemistry Coursebook (Ryan & Norris) | 36.5MB | exampaperspractice.co.uk |
| Physics Coursebook 2nd Ed (David Sang) | 27.1MB | cienotes.com |
| Pure Mathematics 1 (Sue Pemberton) | 24.7MB | learnedguys.com |

**还需要手动获取**：
| 教材 | URL |
|------|-----|
| Chemistry 2nd Ed (Hodder - Cann & Hughes) | https://chemistry.com.pk/books/cambridge-international-as-a-level-chemistry-2e-peter-cann/ |
| Economics Coursebook | https://gamatrain.com/paper/109/Cambridge-International-AS-and-A-level-Economics-Coursebook |
| Pure Math 2&3, Mechanics, Stats | https://ebooks.papacambridge.com/ebooks/caie/cambridge-advancedcambridge-asa-level-mathematics-9709 |

---

### 2.3 学习指南 PDF（study_guides/pdf/）

**✅ 已提交 Git**，克隆代码即获得。不需要额外下载。

---

### 2.4 套路模式库（patterns/）

**✅ 已提交 Git**，4 个 JSON 文件对应 4 科。格式：

```json
{
  "board": "caie-alevel",
  "subject_code": "9701",
  "patterns": {
    "chem_equilibrium": {
      "topic": "Chemical Equilibrium / Le Chatelier's Principle",
      "question_recognition": [...],
      "answer_template": [...],
      "common_mistakes": [...],
      "keywords": [...],
      "analogy": "..."
    }
  }
}
```

---

### 2.5 向量数据库（chroma_db/）

**运行时生成**，不需要提交。构建命令：
```bash
python3 build_kb.py
```

---

## 三、推到 GitHub 的策略

### 已提交（直接可达）

| 目录 | 大小 | 方式 |
|------|------|------|
| `data/study_guides/` | 40MB | Git 直接提交 |
| `data/patterns/` | 20KB | Git 直接提交 |
| `data/past_papers/manifest.json` | 172KB | Git 直接提交 |

### 不能直接提交（>100MB 或可重新生成）

| 目录 | 大小 | 推荐方案 |
|------|------|---------|
| `data/past_papers/` (PDFs) | 2.4GB | **Git LFS** 或脚本重新下载 |
| `data/textbooks/` | 88MB | Git LFS（少量大文件，适合 LFS） |
| `data/repo/` | 3.9GB | **不要提交** — 它是 git clone 的缓存，从零 rebuild 更快 |
| `data/chroma_db/` | 可变 | **不要提交** — `build_kb.py` 重新生成 |

### 方案 A：Git LFS（推荐，如果你需要别人 clone 即用）

```bash
# 安装 Git LFS
brew install git-lfs
git lfs install

# 追踪大文件
git lfs track "data/past_papers/**/*.pdf"
git lfs track "data/textbooks/**/*.pdf"
git lfs track "data/study_guides/pdf/*.pdf"

# 取消 .gitignore 中的排除（改为不忽略）
# 把 .gitignore 中 data/past_papers/ 那行去掉

# 提交所有数据
git add data/past_papers/ data/textbooks/ .gitattributes
git commit -m "data: add 5,000 past papers + 3 textbooks via Git LFS"
git push
```

**注意**：GitHub LFS 免费额度是 1GB 存储 + 1GB 带宽/月。2.4GB 会超额。需要购买 data pack（$5/月 50GB）。

### 方案 B：脚本 + README（免费，推荐用于开源）

保持 `.gitignore` 不变，在 README 中写明 `python3 scripts/run_crawler.py` 即可获取全部数据。用户 clone 后跑一条命令就能重建整个数据集。

**优势**：
- 不占 GitHub LFS 额度
- 真题每天都在更新，脚本可以 git pull 最新版
- 用户不需要下载 2.4GB 的 git history

**劣势**：
- 用户需要等待下载（首次 ~10 分钟，取决于网速）

### 方案 C：Release 附件

```bash
# 打包数据
tar -czf alevel_data.tar.gz data/past_papers/ data/textbooks/

# 在 GitHub Release 页面手动上传
# 或通过 gh CLI
gh release create v0.1.0-data alevel_data.tar.gz
```

---

## 四、验证数据完整性

```bash
# 检查命令行
python3 scripts/master_summary.py

# 预期输出
# ┌─ Past Papers ──────────────────────────────┐
# │ Chemistry   9701  1,364 files  2001-2022   │
# │ Physics     9702  1,344 files  2002-2022   │
# │ Economics   9708    869 files  2001-2022   │
# │ Mathematics 9709  1,422 files  2001-2022   │
# └────────────────────────────────────────────┘
#
# ┌─ Textbooks ────────────────────────────────┐
# │ Chemistry Coursebook (Ryan & Norris)  36.5M│
# │ Physics Coursebook 2nd Ed             27.1M│
# │ Pure Math 1 Coursebook                24.7M│
# └────────────────────────────────────────────┘
```

---

## 五、CI/CD 建议

如果你要把数据获取加入 CI（如 GitHub Actions）：

```yaml
# .github/workflows/setup-data.yml
- name: Download past papers
  run: python3 scripts/run_crawler.py
  timeout-minutes: 30

- name: Download textbooks
  run: python3 scripts/download_textbooks.py
  timeout-minutes: 10
```

但注意免费 GitHub Actions runner 只有 14GB 磁盘，2.4GB + 3.9GB(repo) = 6.3GB 可以放下。
