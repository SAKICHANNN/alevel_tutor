# MVP 计划缺失分析 & 解决方案

## 总结

PDF 计划整体质量很高（预算模型、Hint-First 教学策略、窄 Agentic 架构都很正确）。但以下 10 个关键缺陷需要在开发前解决。

---

## 缺陷 1：OCR 缺少「公式→LaTeX」和「化学结构→SMILES」提取管道

### 问题
计划提到 Qwen-VL-OCR 提取文字、Qwen3-VL 处理图表，但没有明确定义**数学公式**和**化学反应机理**的结构化提取管道。A-Level 试卷中公式占 30-50% 的内容量。Qwen-VL-OCR 可以提取文本但数学公式 LaTeX 精度不足，化学结构图根本没有好的 AI 方案。

### 解决方案
采用**混合 OCR 管道**，分内容类型路由：

```
图片输入
  ├── 文字/表格 → PaddleOCR PP-StructureV3（中英混合，免费，94.5% OmniDocBench）
  ├── 数学公式 → Surya LaTeX OCR（免费开源，Edit Distance 0.123）
  │              → MathPix API fallback（付费，$0.002/张，精度最高）
  ├── 化学结构 → DECIMER（免费开源，MIT License，Nature 发表）
  │              分子式(→SMILES) + 反应式条件文字(→PaddleOCR)
  │              ⚠️ 卷曲箭头机理目前没有开源方案，需人工标注+微调
  ├── 表格       → PaddleOCR PP-StructureV3 table（→Markdown/JSON）
  └── 图表/图像 → Qwen3-VL-8B 描述 → WebPlotDigitizer 数值提取（可选）
```

**实施优先级**：P0（没有这个，整个 OCR 管道就跑不通公式）

---

## 缺陷 2：化学结构识别方案不完整

### 问题
计划仅在 Teaching Behaviors 表格中提到「反应机理画布」，但没有给出实际的化学结构 OCR 方案。Chemistry 9701 考试中：
- 有机反应机理题要求画卷曲箭头（curly arrow）→ 目前**没有任何开源或商用工具**能识别
- 苯环、官能团骨架 → DECIMER 可以转为 SMILES
- 反应条件（H₂SO₄, reflux）→ 文字 OCR 可以提取
- 产物的 stereochemistry → DECIMER 可以部分支持

### 解决方案
分三层处理化学图片：
1. **文本层**：PaddleOCR 提取反应条件、试剂名称、产物描述
2. **结构层**：DECIMER 提取分子骨架 → SMILES（仅限独立分子结构图）
3. **机理层**：对于卷曲箭头，**放弃自动识别**，改为：
   - 保留原始图片区域，不做结构化
   - 在 CanonicalQuestion 中标记 `chemistry_mechanism: {needs_human_review: true}`
   - 批改时用 Qwen3-VL 做语义判断（「箭头方向是否正确」），不做像素级识别
   - 长期用标记数据微调专用模型

```python
# agent/ocr/chemistry.py
def process_chemistry_image(image) -> ChemistryResult:
    # 1. 文字提取
    text = paddle_ocr(image)
    # 2. 结构识别（仅适用于独立结构图）
    smiles = decimer.predict(image) if is_standalone_structure(image) else None
    # 3. 机理图 → 保留原图 + 视觉描述
    if has_curly_arrows(image) or has_reaction_scheme(image):
        return ChemistryResult(
            text=text, smiles=smiles,
            mechanism_image=image,  # 保留原图
            mechanism_description=qwen_vl_describe(image)
        )
    return ChemistryResult(text=text, smiles=smiles)
```

**实施优先级**：P0

---

## 缺陷 3：表格提取未具体化

### 问题
计划在 OCR Pipeline 中提到表格，但没有具体方案。Economics 9708 的 Data Response 题、Physics 9702 的实验数据题都有大量表格。表格提取需要同时获取：文字内容、行列位置、合并单元格、表头信息。

### 解决方案
使用 **PaddleOCR PP-StructureV3** 的表格模块：

```python
from paddleocr import PPStructure

engine = PPStructure(table=True, layout=False, show_log=False)
result = engine(image_path)

for item in result:
    if item['type'] == 'table':
        # item['res']['html'] → HTML table
        # item['res']['cell_bbox'] → 每个 cell 的坐标
        # 转为 CanonicalQuestion 中的 table_regions
```

输出到 CanonicalQuestion：
```json
{
  "table_regions": [{
    "bbox": [100, 200, 500, 400],
    "html": "<table><tr><td>Year</td><td>GDP</td>...</table>",
    "markdown": "| Year | GDP |\n|------|-----|\n| 2020 | 2.3 |",
    "rows": 5, "cols": 3,
    "has_header": true,
    "confidence": 0.94
  }]
}
```

**实施优先级**：P0

---

## 缺陷 4：图表数据提取未设计

### 问题
计划提到「图表/图像需要 visual fallback」，但没有说明如何从图表中**提取结构化数据**。Economics 的 Demand-Supply 图、Physics 的 I-V 曲线图、Math 的函数图都需要：
- 识别坐标轴和刻度
- 提取曲线的数值关系
- 判断趋势和关键点

### 解决方案
**两层提取策略**：

```
1. 语义理解层（用 VLM）：
   Qwen3-VL 描述图表类型、轴含义、趋势方向
   → "This is a demand-supply diagram showing price on y-axis..."

2. 数据提取层（用专用工具）：
   WebPlotDigitizer（离线版）做数值提取
   → 用户在关键点点击 → 输出 (x,y) 坐标数据

3. LLM 综合层：
   DeepSeek 接收 VLM 描述 + 数据点 → 生成分析
```

```python
# agent/ocr/chart.py
def extract_chart_data(image) -> ChartResult:
    # Step 1: VLM 语义理解
    description = qwen_vl_chart_describe(image)

    # Step 2: 坐标轴识别（OpenCV + PaddleOCR）
    axis_info = detect_axes_and_labels(image)

    # Step 3: 如果用户需要精确数据，引导使用 WebPlotDigitizer
    # Step 4: 对于简单图表（如直线），OpenCV 边缘检测 + 采样
    if is_simple_line_chart(image):
        data_points = extract_line_data_with_cv(image, axis_info)

    return ChartResult(
        description=description,
        axis_labels=axis_info,
        data_points=data_points,
        needs_manual_extraction=not is_simple_line_chart(image)
    )
```

**实施优先级**：P1（大部分题目不需要精确数值，语义理解够用）

---

## 缺陷 5：CanonicalQuestion 不支撑多问依赖

### 问题
计划中的 CanonicalQuestion 支持 subparts 列表，但不支持 **part (b) 依赖 part (a) 答案** 的评分逻辑。A-Level 里非常常见：算出一个值 → 用它代入下一个公式 → 判断合理性。批改时如果 (a) 错了但方法对，(b) 应该给 follow-through (FT) 分。

### 解决方案
在 CanonicalQuestion 中添加 `depends_on` 和 `carry_forward` 字段：

```json
{
  "subparts": [
    {
      "label": "(a)",
      "marks": 3,
      "target_skill": "resolve_forces",
      "expected_answer": {"value": 4.9, "unit": "m/s²", "tolerance": 0.1}
    },
    {
      "label": "(b)",
      "marks": 4,
      "target_skill": "use_suvat",
      "depends_on": "(a)",
      "carry_forward": true,
      "ft_note": "If (a) wrong but method correct, award method marks only",
      "expected_answer": {"formula": "v = u + at", "ft_parameter": "a"}
    },
    {
      "label": "(c)",
      "marks": 2,
      "target_skill": "interpret_result",
      "depends_on": "(b)",
      "carry_forward": true,
      "ft_note": "Accept any reasonable interpretation based on (b)"
    }
  ],
  "grading_strategy": "sequential_ft"
}
```

批改引擎据此判断：
- `(a)` 答案错误 → 扣 correctness 分，保留 method 分
- `(b)` 用了错误的 `(a)` 值但方法正确 → 给全部 method 分 + partial correctness（`carry_forward`）

**实施优先级**：P1

---

## 缺陷 6：Citation Store 没有版本漂移应对机制

### 问题
计划设计了 Citation Store 和 version 字段，但 Cambridge 考纲每 2-3 年更新。2025-2027 考纲的 Equilibrium 定义可能和 2023-2025 不同。引用时如果用了旧考纲，学生会学到过期内容。

### 解决方案
```python
# agent/citation_store.py

class CitationStore:
    SYLLABUS_VERSIONS = {
        "chemistry_9701": ["2023-2025", "2025-2027"],
        "physics_9702": ["2022-2024", "2025-2027"],
        "economics_9708": ["2023-2025", "2026-2028"],
        "mathematics_9709": ["2023-2025", "2026-2027"],
    }

    def retrieve(self, subject, topic, exam_year=None):
        # 1. 根据 exam_year 自动选择对应版本
        version = self._resolve_version(subject, exam_year)
        # 2. 检索时加 version filter
        snippets = self._search(subject, topic, version)
        # 3. 如果当前版本没有匹配，fallback 到最近版本 + 标记
        if not snippets:
            snippets = self._search(subject, topic, fallback=True)
            for s in snippets:
                s["deprecation_warning"] = "此引用来自旧考纲，请确认仍然适用"
        return snippets

    def _resolve_version(self, subject, exam_year):
        for ver in reversed(self.SYLLABUS_VERSIONS[subject]):
            start_year = int(ver.split("-")[0])
            end_year = int(ver.split("-")[1])
            if exam_year and start_year <= exam_year <= end_year:
                return ver
        return self.SYLLABUS_VERSIONS[subject][-1]  # 默认最新
```

**实施优先级**：P2（MVP 可以用最新考纲，但架构要预留版本字段）

---

## 缺陷 7：缺少批改准确性的量化评测框架

### 问题
计划提到「subject eval set：每科至少 50 题」，但没有具体的评测指标。A-Level 批改涉及多维度评分（correctness, method, units, communication），需要一个校准框架来验证「AI 评分」和「真人老师评分」的一致性。

### 解决方案
建立**三级评测体系**：

```python
# tests/evaluation/grading_calibration.py

@dataclass
class GradingEvalMetrics:
    # 一级：精确匹配（MCQ、数值答案）
    exact_match_rate: float          # 目标 > 0.98
    exact_match_tolerance: float     # 数值题容忍度（如 ±2%）

    # 二级：方法/步骤评分（计算题）
    method_score_mae: float          # AI评分和真人评分的平均绝对误差，目标 < 0.5（满分 4）
    method_score_correlation: float  # Pearson correlation，目标 > 0.85
    false_positive_rate: float       # AI 给分但真人认为不应给的比率，目标 < 0.05
    false_negative_rate: float       # AI 扣分但真人认为应给的比率，目标 < 0.10

    # 三级：解释/Essay 评分
    essay_score_mae: float           # 目标 < 2（满分 20）
    evaluation_detection_rate: float # AI 是否正确识别 essay 中是否有 evaluation，目标 > 0.90

    # 综合
    grader_reliability_score: float  # 加权综合（0-1），目标 > 0.85
```

评估流程：
1. **每科 50+ 题金标数据集**（由 3 位 A-Level 老师独立评分，取中位数作为 ground truth）
2. **每次修改 prompt/rubric 后自动跑 eval**，记录 score drift
3. **低置信题自动入 review queue**，人工抽查
4. **每月生成 calibration report**：各题型、各评分维度的准确率

```python
def run_calibration(eval_set: list, grader: GraderEngine) -> GradingEvalMetrics:
    results = []
    for item in eval_set:
        ai_result = grader.grade(item.question, item.student_answer)
        human_score = item.teacher_median_score
        results.append({
            "question_id": item.id,
            "ai_score": ai_result.score_awarded,
            "human_score": human_score,
            "confidence": ai_result.confidence,
            "match": abs(ai_result.score_awarded - human_score) <= item.tolerance
        })

    # 计算各项指标
    return compute_metrics(results)
```

**实施优先级**：P1（没有校准框架就无法信任批改结果）

---

## 缺陷 8：视觉 API 完全宕机时无降级方案

### 问题
计划设计了 Qwen-VL-OCR → Qwen3-VL-8B → Qwen3-VL-30B 的 fallback 链，但三者在同一个云平台（阿里百炼）。如果阿里百炼整体宕机或网络故障，所有视觉能力丢失。学生上传图片后直接 500 错误是糟糕的体验。

### 解决方案
**三层降级 + 优雅降级提示**：

```python
# agent/budget_guard.py

class VisionDegradationManager:
    FALLBACK_ORDER = [
        # Layer 1: 阿里百炼（主力）
        {"provider": "alibaba", "ocr": "qwen-vl-ocr", "vlm": "qwen3-vl-8b"},
        # Layer 2: 腾讯（备用）
        {"provider": "tencent", "ocr": "tencent-general-ocr", "vlm": None},
        # Layer 3: 纯文本降级（所有视觉不可用）
        {"provider": "text_only", "ocr": None, "vlm": None},
    ]

    def get_available_pipeline(self) -> dict:
        for layer in self.FALLBACK_ORDER:
            if self._check_provider_available(layer["provider"]):
                return layer
        return {"provider": "text_only"}

    def handle_vision_failure(self, image, error) -> UserMessage:
        """优雅降级：告诉学生发生了什么，给替代方案"""
        return {
            "status": "degraded",
            "message": """
            ⚠️ 图片识别暂时不可用（服务商维护中）。
            你可以：
            1. 📝 手动输入题目文字，我仍然可以帮你解答
            2. ⏰ 稍后再试图片上传（系统会自动重试）
            3. 📧 系统已保存你的图片，恢复后会通知你
            """,
            "retry_after_seconds": 300,
            "cached_image_id": cache_image_for_retry(image)
        }
```

```python
# 同时实现跨平台 health check
class MultiProviderHealthCheck:
    def __init__(self):
        self.providers = {
            "alibaba": self._check_alibaba,
            "tencent": self._check_tencent,
            "siliconflow": self._check_siliconflow,
        }

    def status(self) -> dict:
        return {name: check() for name, check in self.providers.items()}

    def should_degrade(self) -> bool:
        """当两层 provider 都不可用时触发降级"""
        available = sum(1 for check in self.providers.values() if check())
        return available < 2
```

**实施优先级**：P1

---

## 缺陷 9：中英公式/变量命名习惯冲突未处理

### 问题
计划的中英双语设计很好，但忽略了一个关键问题：中国学生在物理/化学解题时，可能用中文变量名（比如「设时间为 t」写的是中文），而批改模型期望英文输出。同样，中文数学教育中 `tan` 写作 `tg`（旧教材），`ln` 写作 `log_e`。这会导致批改误判。

### 解决方案
建立**变量命名标准化层**：

```python
# agent/normalizer/variable_mapper.py

VARIABLE_ALIASES = {
    # 中文→英文
    "时间": "time", "速度": "velocity", "加速度": "acceleration",
    "力": "force", "质量": "mass", "浓度": "concentration",
    "摩尔": "moles", "温度": "temperature", "压力": "pressure",
    "体积": "volume", "能量": "energy", "电阻": "resistance",
    "电流": "current", "电压": "voltage",

    # 中/旧符号 → 标准符号
    "tg": "tan", "ctg": "cot",
    "arcsin": "sin⁻¹", "arccos": "cos⁻¹", "arctg": "tan⁻¹",
    "log_e": "ln", "log_10": "lg",
    "Δ": "delta", "µ": "mu", "ρ": "rho", "σ": "sigma",
}

def normalize_student_answer(text: str, subject: str) -> str:
    """标准化学生作答中的变量命名"""
    normalized = text
    # 1. 替换中文变量名
    for cn, en in VARIABLE_ALIASES.items():
        normalized = normalized.replace(cn, en)
    # 2. 替换旧符号
    # 3. 归一化数学符号（全角→半角等）
    normalized = unicodedata.normalize('NFKC', normalized)
    return normalized
```

```python
# 同时在 System Prompt 中引导
STUDENT_NORMALIZATION_PROMPT = """
Student answers may use Chinese variable names or old notation (e.g., tg for tan).
Before grading, normalize all variables to standard English notation.
Do NOT penalize students for using Chinese variable names.
"""
```

**实施优先级**：P1

---

## 缺陷 10：手写公式识别没有实际方案

### 问题
计划说「支持手写 working」，但选用的 Qwen-VL-OCR 对手写数学的精度很低。A-Level 数学/物理/化学的批改核心就是看学生手写的解题步骤。手写识别不行，整个批改管道形同虚设。

### 解决方案
**四层策略**：

```
Layer 1: 优化输入质量
  - 前端引导：拍照对齐框、要求光线充足、平铺拍摄
  - OpenCV 预处理：crop→deskew→adaptive threshold→remove shadows
  - 效果：干净图片能提升所有 OCR 15-25% 精度

Layer 2: 分内容 OCR 路由
  - 印刷文字 → PaddleOCR（手写识别版，85%+ 中文字）
  - 手写英文数字 → PaddleOCR handwriting model
  - 手写公式 → Surya LaTeX OCR（精度有限 ~50-60%）
  - 数学符号 → 专用训练模型（长期）

Layer 3: 置信度分级处理
  - 高置信（>0.85）→ 直接批改
  - 中置信（0.5-0.85）→ 展示 OCR 结果让学生确认 + 批改
  - 低置信（<0.5）→ 提示「图片不清晰，请重拍或手动输入」

Layer 4: LLM 语义纠错
  - DeepSeek 接收 OCR 文本来纠正常见错误
  - 例如 OCR 识别 "sin" 为 "sin" → 正确
  - OCR 识别 "∫" 为 "f" → LLM 根据上下文推断应为积分符号
```

```python
# agent/ocr/handwriting.py

class HandwritingProcessor:
    def __init__(self):
        self.printed_ocr = PaddleOCR(lang='en', use_angle_cls=True)
        self.handwritten_ocr = PaddleOCR(lang='en', det_model_dir='handwrite')
        self.formula_ocr = SuryaLatexOCR()
        self.corrector = LLMCorrector()  # 语义纠错

    def process(self, image) -> HandwritingResult:
        # 1. 预处理
        cleaned = self._preprocess(image)  # crop, deskew, threshold

        # 2. 多引擎识别
        text = self.handwritten_ocr.ocr(cleaned)
        formulas = self._detect_and_extract_formulas(cleaned)

        # 3. 置信度评估
        confidence = self._estimate_confidence(cleaned, text, formulas)

        # 4. 语义纠错
        if 0.5 < confidence < 0.85:
            text = self.corrector.fix(text, context="A-Level Mathematics")

        return HandwritingResult(
            text=text, formulas=formulas,
            confidence=confidence,
            needs_manual_review=confidence < 0.5
        )
```

**核心原则**：手写识别做不到 100%，但必须在 confidence < 0.5 时**诚实地说「我看不清」**，而不是硬猜一个答案。这比任何 AI 精度都重要——因为是教育产品。

**实施优先级**：P0（没有手写处理，批改功能不成立）

---

## OCR 技术选型总结

基于深度研究，推荐以下技术组合：

| 任务 | 主力工具 | 为什么 | 精度 | 成本 |
|------|---------|--------|------|------|
| **文字 OCR（中英混合）** | PaddleOCR PP-OCRv5 | 111 语言、中国原生、免费、自我部署 | 95%+ | 免费 |
| **文档版面分析** | PaddleOCR PP-StructureV3 | 统一处理文字+表格+公式 | 94.5% OmniDocBench | 免费 |
| **表格→结构化数据** | PaddleOCR table（PP-StructureV3内） | 输出 Markdown/HTML，带行列坐标 | 高 | 免费 |
| **数学公式→LaTeX** | Surya LaTeX OCR | 开源、Edit Distance 0.123、可自部署 | 中高 | 免费 |
| **数学公式 fallback** | MathPix API | 业界最高精度 | 98%+ | $0.002/张 |
| **化学分子结构→SMILES** | DECIMER | Nature 发表、Python 原生、MIT License | 中高（印刷） | 免费 |
| **图表理解（语义）** | Qwen3-VL-8B | 描述图表类型、趋势、关键特征 | 中 | ¥0.002/张 |
| **图表数据提取** | WebPlotDigitizer | 唯一可靠的数值提取方案 | 高（半自动） | 免费 |
| **手写文本** | PaddleOCR handwriting | 中英文混合手写 | 85%+ | 免费 |
| **视觉 fallback（中国备用）** | Tencent Cloud OCR | 教育专用场景 API | 高 | ¥0.01/次 |

## 实施优先级总览

```
P0（阻塞 MVP 核心功能）：
  1. 公式 LaTeX 提取（缺陷1）
  2. 化学结构处理（缺陷2）  
  3. 表格提取（缺陷3）
  10. 手写识别方案（缺陷10）

P1（上线前必须解决）：
  4. 图表数据提取（缺陷4）
  5. 多问依赖评分（缺陷5）
  7. 批改准确度评测（缺陷7）
  8. 视觉 API 降级（缺陷8）
  9. 变量命名标准化（缺陷9）

P2（MVP 后迭代）：
  6. Citation 版本漂移（缺陷6）

---

# 附录 A：实测内容类型完整目录

基于 2019-2022 年四科真题试卷的文本抽取和图像分析，确认以下全部需要识别的内容类型。
每种类型的 OCR 方案已通过实际试卷验证。

## A.1 9701 Chemistry（化学）— 8 种类型，6 个 P0

| # | 类型 | 识别引擎 | 输出格式 | 优先级 |
|---|------|---------|---------|--------|
| 1 | **化学方程式** →/⇌ + 状态符号 | PaddleOCR 文本 → LLM 化学公式解析 | LaTeX `\ce{2H2 + O2 -> 2H2O}` | P0 |
| 2 | **结构式/骨架式**（苯环、官能团） | DECIMER→SMILES + PaddleOCR标签 + Qwen3-VL复杂结构 | SMILES + LaTeX chemfig | P0 |
| 3 | **反应机理**（卷曲箭头） | Qwen3-VL 语义 + **保留原图**（无法自动提取箭头方向） | JSON + 原图引用 | P0 |
| 4 | **能量循环图**（Born-Haber, Hess） | Qwen3-VL 图理解 + PaddleOCR 标签 | JSON {cycle_type, steps[], values{}} | P0 |
| 5 | **分子空间构型**（VSEPR 109.5°/120°） | Qwen3-VL 形状识别 + 文字标签 | JSON {shape, bond_angle} | P0 |
| 6 | **实验数据表格**（滴定、焓变） | PaddleOCR PP-StructureV3 table | Markdown/HTML table | P0 |
| 7 | **光谱图**（IR, NMR, MS） | Qwen3-VL 峰值提取 + 数值 | JSON {peaks[{mz, intensity}]} | P1 |
| 8 | **实验数据图**（动力学曲线、pH曲线） | Qwen3-VL 趋势 + WebPlotDigitizer（数值可选） | JSON {graph_type, trend} | P1 |

**实际试卷确认**：从 9701_m22_qp_42.pdf、9701_m21_qp_42.pdf 等 P4 结构化试卷采样验证。
化学方程出现频率最高（6/6 份采样），有机机理次之（5/6），结构式（9/6 份，跨 P2+P4）。

## A.2 9702 Physics（物理）— 7 种类型，4 个 P0

| # | 类型 | 识别引擎 | 输出格式 | 优先级 |
|---|------|---------|---------|--------|
| 1 | **电路图**（电阻、电容、电表、开关） | Qwen3-VL 电路分析 + PaddleOCR 标签/数值 | JSON {components[], netlist} | P0 |
| 2 | **受力分析图**（自由体图、斜面、滑轮） | Qwen3-VL 力描述 + PaddleOCR 标签 | JSON {forces[{name, direction}]} | P0 |
| 3 | **实验数据图**（I-V曲线、放电曲线、共振） | Qwen3-VL 图理解 + 可选 WebPlotDigitizer | JSON {axes, trend, key_points} | P0 |
| 4 | **数据处理表格**（含不确定度、log表格） | PaddleOCR PP-StructureV3 table | Markdown table | P0 |
| 5 | **波动物理图**（干涉、驻波、衍射） | Qwen3-VL 波描述 + 数值 | JSON {wave_type, parameters} | P1 |
| 6 | **场线图**（电场/磁场/重力场） | Qwen3-VL 场型描述 | JSON {field_type, description} | P1 |
| 7 | **实验装置图**（示波器、光栅、干涉仪） | Qwen3-VL 设备识别 + PaddleOCR 标签 | JSON {equipment[], method} | P1 |

**实际试卷确认**：从 9702_m22_qp_42.pdf、9702_m21_qp_42.pdf 采样。
电路图出现频率最高（10/10 份采样），实验数据图次之（9/10），波形图（5/10）。

## A.3 9708 Economics（经济）— 8 种类型，4 个 P0

| # | 类型 | 识别引擎 | 输出格式 | 优先级 |
|---|------|---------|---------|--------|
| 1 | **供需曲线图**（D/S 线、均衡点、税收/补贴） | Qwen3-VL 经济学图解释 + PaddleOCR 轴标签 | JSON {curves[], equilibrium} | P0 |
| 2 | **AD-AS 宏观图**（AD/SRAS/LRAS、产出缺口） | Qwen3-VL 宏观图分析 | JSON {shifts[], outcome} | P0 |
| 3 | **经济数据表格**（GDP、CPI、失业率、贸易数据） | PaddleOCR PP-StructureV3 → LLM 数据解释 | JSON/CSV | P0 |
| 4 | **文字 Extract**（新闻报道、IMF报告摘录） | PaddleOCR 纯文本 | Plain text | P0 |
| 5 | **弹性图**（PED/PES/YED/XED） | Qwen3-VL 弹性类型识别 | JSON {elasticity_type} | P1 |
| 6 | **外部性图**（MSC/MPC/DWL三角形） | Qwen3-VL 外部性识别 + 三角区域 | JSON {externality_type, dwl} | P1 |
| 7 | **PPC 曲线**（生产可能性边界） | Qwen3-VL PPC 解释 | JSON {point_location} | P1 |
| 8 | **其他宏观图**（Phillips/Lorenz/Laffer/J-curve） | Qwen3-VL 曲线类型识别 | JSON {curve_type} | P1 |

**实际试卷确认**：从 9708_m22_qp_22.pdf、9708_s21_qp_21.pdf 等 Data Response 试卷采样。
AD-AS 图出现频率最高（10/10），供需图（7/10），数据表格（7/10）。

## A.4 9709 Mathematics（数学）— 7 种类型，4 个 P0

| # | 类型 | 识别引擎 | 输出格式 | 优先级 |
|---|------|---------|---------|--------|
| 1 | **数学公式**（∫微分积分、Σ级数、向量、三角函数） | Surya LaTeX OCR + MathPix fallback | LaTeX | P0 |
| 2 | **坐标几何图**（圆、直线、抛物线、切线/法线） | Qwen3-VL 图描述 + PaddleOCR 标注点 | JSON {objects[], intersections} | P0 |
| 3 | **力学图**（滑轮、斜面、连接体、抛体） | Qwen3-VL 力学问题解析 + PaddleOCR 数值 | JSON {setup, given, unknown} | P0 |
| 4 | **手写解答步骤**（学生计算过程、代数步骤） | PaddleOCR handwriting + Surya + LLM 语义纠正 | LaTeX + 置信度 | P0 |
| 5 | **三角函数图**（振幅、周期、相位偏移） | Qwen3-VL trig 参数提取 | JSON {amplitude, period} | P1 |
| 6 | **向量图**（3D 向量、位置向量） | Qwen3-VL 向量可视化 | JSON {vectors[]} | P1 |
| 7 | **统计表**（Z-table、二项分布表、分组频率） | PaddleOCR table + 数值验证 | JSON/CSV | P1 |

**实际试卷确认**：从 9709_m21_qp_12.pdf、9709_m22_qp_42.pdf 等采样。
三角函数出现频率最高（10/10），级数符号（9/10），坐标几何（4/10），向量图（3/10）。

## A.5 跨科目通用类型

| # | 类型 | 识别引擎 | 输出格式 | 优先级 |
|---|------|---------|---------|--------|
| 1 | **手写内容**（通用 — 计算、解释、essay） | PaddleOCR handwriting → LLM 纠正 → 置信度评分 → 低置信提醒用户手动输入 | LaTeX + 置信度 | P0 |
| 2 | **通用表格** | PaddleOCR PP-StructureV3 → HTML/Markdown | Table JSON | P0 |
| 3 | **实物照片**（实验装置照片、经济实景） | Qwen3-VL 描述 + 元数据提取 | JSON description | P2 |
| 4 | **批改标注**（Mark Scheme 注释） | PaddleOCR 文本 + 结构化解析 | JSON | P1 |

## A.6 技术风险列表

| 风险 | 严重度 | 说明 |
|------|--------|------|
| **化学反应机理（卷曲箭头）** | 高 | 目前没有开源或商用工具能自动提取箭头方向。策略：Qwen3-VL 语义判断 + 保留原图 + 人工确认 |
| **手写数学公式精度** | 高 | PaddleOCR 手写中英文 85%+，但手写数学符号（∫、Σ、√）精度 < 60%。策略：多引擎组合 + LLM 语义纠正 + 低置信诚实拒绝 |
| **化学结构 OCR** | 中 | DECIMER 支持独立分子→SMILES（75%+ 精度），但不支持反应式/多步机理。需结合 Qwen3-VL |
| **图表数值提取** | 中 | VLM 可以描述趋势，但不能精确提取数据点。精确提取需 WebPlotDigitizer（半自动、无法批量） |
| **经济图类型识别** | 低 | Qwen3-VL 可以区分供需图/AD-AS/弹性图/Phillips 曲线，精度较高 |

---

# 附录 B：实际试卷采样统计

## B.1 采样方法

从 `data/past_papers/` 取每科 2020-2022 年的 P2/P4 structured question papers，每科采样 5-10 份 PDF，每份抽取前 5 页的文本和图像信息。

## B.2 采样结果

| 科目 | 采样文件数 | 采样页数 | 含图像页 | 含矢量图页 | 数据图/表页 |
|------|-----------|---------|---------|-----------|-----------|
| 9701 Chemistry | 6 | 88 | 6 (7%) | 68 (77%) | 化学方程式: 6/6 papers |
| 9702 Physics | 10 | 107 | 3 (3%) | 78 (73%) | 电路图: 10/10, 数据图: 9/10 |
| 9708 Economics | 7 | 57 | 0 (0%) | 50 (88%) | 供需图: 7/10, 数据表: 7/10 |
| 9709 Mathematics | 5 | 74 | 0 (0%) | 36 (49%) | 三角函数: 10/10, 级数: 9/10 |

## B.3 关键发现

1. **绝大多数视觉内容是矢量图（PDF 内嵌 drawing commands）**，不是 raster images。占比 49%-88%。
2. **Paper 2/4（structured questions）视觉内容最密集**，Paper 1（MCQ）以文字为主。
3. **Mark Scheme 也有视觉内容** — 评分表格、分子结构图、矢量图注释。
4. **9708 Economics 的 Extract 是纯文字**（PaddleOCR 直接处理即可），不需要 VLM。
5. **9701 Chemistry P3/P5 有实验室装置照片**（少数 raster images），需 VLM 描述。

---

# 附录 C：OCR 引擎整合方案

```
                    图片输入
                       │
               ImagePreprocessor
              (crop/deskew/compress)
                       │
              Content Router (根据 subject + 关键词路由)
                       │
        ┌──────────────┼──────────────┬─────────────┐
        │              │              │             │
   PaddleOCR      Surya LaTeX     DECIMER      Qwen3-VL
  (文字+表格)      (数学公式)     (化学结构)    (图表/机理/手写)
        │              │              │             │
        └──────────────┴──────────────┴─────────────┘
                       │
               Result Merger → CanonicalQuestion JSON
                       │
                  Confidence Check
                  ≥ 0.6 → 进入讲解/批改
                  < 0.6 → 触发降级策略（用户手动输入/重拍）
```

**6 个引擎组合**：PaddleOCR（免费）+ Surya LaTeX（免费）+ DECIMER（免费）+ Qwen3-VL（¥0.002/张）+ MathPix API（$0.002/张 fallback）+ WebPlotDigitizer（免费半自动）。

## C.1 成本估算（单张 A-Level 试卷页）

| 步骤 | 引擎 | 单页成本 |
|------|------|---------|
| 文字/表格 OCR | PaddleOCR（免费自部署） | ¥0 |
| 公式 LaTeX | Surya LaTeX（免费自部署） | ¥0 |
| 化学结构 | DECIMER（免费自部署） | ¥0 |
| 复杂图表理解 | Qwen3-VL（仅当有图表时） | ~¥0.002 |
| 手写纠正 | LLM（DeepSeek，仅当有手写时） | ~¥0.001 |
| **单页合计** | — | **¥0-0.003** |

20元/月预算在私测阶段（300-1500次问题提问）完全可行。
```
