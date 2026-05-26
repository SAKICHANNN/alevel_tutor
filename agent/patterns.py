"""
Pattern system: structured database of exam techniques, question patterns,
answer templates, and common mistakes for each subject.
"""
import json
from typing import Optional

# ── Core Pattern Database ──

PATTERNS = {
    # ===== CHEMISTRY 9701 =====
    "chem_equilibrium": {
        "subject": "9701",
        "topic": "Chemical Equilibrium / Le Chatelier's Principle",
        "question_recognition": [
            "关键词: equilibrium, shift, increase/decrease, pressure, temperature, concentration, catalyst",
            "常见问法: 'Explain what happens when...' / 'State and explain the effect of...'",
            "Paper 2/4 的结构题或选择题",
        ],
        "answer_template": [
            "Step 1: 说出条件变化是什么 (e.g. temperature increased)",
            "Step 2: 说出平衡向哪个方向移动 (left/right, endothermic/exothermic direction)",
            "Step 3: 解释为什么会移动 (The system opposes the change by...)",
            "Step 4: 说明结果 (e.g. yield of product increases/decreases)",
            "Step 5: 如果是催化剂: 只加速到达平衡的速度，不改变平衡位置！",
        ],
        "common_mistakes": [
            "只说 'equilibrium shifts to the left/right' 不解释为什么",
            "催化剂忘了说 'does not affect position of equilibrium'",
            "增加压力时应该看气体的摩尔数（moles of gas）而不是所有物质",
            "温度变化时要根据 ΔH 判断是 exothermic 还是 endothermic 方向",
        ],
        "keywords": [
            "Le Chatelier's principle: system opposes the change",
            "Kc: only affected by temperature",
            "Catalyst: speeds up forward AND backward equally",
        ],
        "analogy": "舞池比喻：舞池满了，新来一群人挤进来 → 大家往旁边空房间移动。条件变化 = 新进来的人；平衡移动 = 人群重新分布。",
    },
    "chem_organic_mechanisms": {
        "subject": "9701",
        "topic": "Organic Reaction Mechanisms",
        "question_recognition": [
            "关键词: mechanism, curly arrow, electrophilic, nucleophilic, SN1, SN2",
            "常见问法: 'Draw the mechanism for...' / 'Describe the mechanism of...'",
            "出现在 Paper 2/4",
        ],
        "answer_template": [
            "Step 1: 识别反应类型 (electrophilic addition / nucleophilic substitution / etc.)",
            "Step 2: 画出完整的 displayed formula（展示所有原子和键）",
            "Step 3: 用卷曲箭头 (curly arrows) 画电子移动",
            "  - 箭头必须从孤对电子(lone pair)或键的中间开始",
            "  - 箭头必须指向原子或要形成的键",
            "Step 4: 标出所有中间体的电荷",
            "Step 5: 如果有 intermediate (如 carbocation)，画出来",
        ],
        "common_mistakes": [
            "卷曲箭头从碳原子开始（应该从键/孤对电子开始）",
            "忘了画中间体上的电荷",
            "SN1 vs SN2 混淆: SN1=两步+carbocation；SN2=一步+inversion",
            "忘了画 dipole (δ+ δ-)",
        ],
        "keywords": [
            "Electrophile: electron-deficient, accepts electron pair",
            "Nucleophile: electron-rich, donates electron pair",
            "SN1: 2 steps, carbocation intermediate, racemisation",
            "SN2: 1 step, inversion of configuration",
        ],
    },
    "chem_calculations": {
        "subject": "9701",
        "topic": "Stoichiometry & Mole Calculations",
        "question_recognition": [
            "关键词: calculate, moles, mass, volume, concentration, limiting reagent, yield",
            "常见问法: 'Calculate the mass of...' / 'Determine the limiting reagent'",
        ],
        "answer_template": [
            "Step 1: 写出配平的化学方程式",
            "Step 2: 计算每种已知物质的 moles (n = m/M 或 n = cV 或 n = V/24)",
            "Step 3: 用 mole ratio 找 limiting reagent",
            "Step 4: 计算产物的 theoretical yield",
            "Step 5: 如果需要 percentage yield: (actual / theoretical) × 100",
            "全过程中不要四舍五入！只在最后答案四舍五入到 3 s.f.",
        ],
        "common_mistakes": [
            "中间步骤四舍五入导致最终答案偏差",
            "忘记配平方程式就用 mole ratio",
            "限性试剂判断错误",
            "单位不一致 (cm³ vs dm³, g vs kg)",
            "3 s.f. 和 3 d.p. 混淆",
        ],
        "keywords": [
            "n = m/M (moles = mass / molar mass)",
            "n = cV (moles = concentration × volume in dm³)",
            "Gas at RTP: 1 mol = 24 dm³",
            "Limiting reagent: the one that runs out first",
        ],
    },

    # ===== PHYSICS 9702 =====
    "phys_kinematics": {
        "subject": "9702",
        "topic": "Kinematics / SUVAT",
        "question_recognition": [
            "关键词: displacement, velocity, acceleration, time, suvat, projectile",
            "常见问法: 'Calculate the...' / 'Find the time taken...'",
        ],
        "answer_template": [
            "Step 1: 列出已知量和未知量 (s, u, v, a, t)",
            "Step 2: 选择不包含未知量的 SUVAT 方程",
            "Step 3: 代入数值（注意方向！向上设为+，向下设为-）",
            "Step 4: 解方程",
            "Step 5: 选符合物理意义的答案（如时间不能为负）",
        ],
        "common_mistakes": [
            "选错方程（用了包含两个未知量的方程）",
            "忘记设定正方向，符号错乱",
            "投掷运动中忘记加速度始终是 g=9.81 向下",
            "单位转换错误（km→m, cm→m）",
        ],
        "keywords": [
            "v = u + at",
            "s = ut + ½at²",
            "v² = u² + 2as",
            "s = ½(u+v)t",
        ],
    },
    "phys_paper5": {
        "subject": "9702",
        "topic": "Paper 5: Planning, Analysis, Evaluation",
        "question_recognition": [
            "关键词: plan, experiment, variable, graph, uncertainty, improve",
            "Paper 5 专属题型",
        ],
        "answer_template": [
            "Planning:",
            "  1. 列出 Independent / Dependent / Controlled variables（各3个）",
            "  2. 列出器材并说明用途",
            "  3. 写步骤（足够详细，别人能复现）",
            "  4. 说明如何分析数据（画什么图，y=mx+c 形式，如何提取需要的量）",
            "  5. 安全注意事项（具体的，不是 '小心实验'）",
            "Analysis:",
            "  1. 表格：每列有单位/不确定性",
            "  2. 画图：标轴+单位，点占 >50% 网格，画最佳拟合线",
            "  3. 算 gradient + y-intercept（展示三角形法）",
            "  4. 画 worst acceptable line，算不确定性",
            "Evaluation:",
            "  1. 结论：回答实验目的",
            "  2. 指出局限性：具体的问题（不说 'human error'）",
            "  3. 改进建议：具体行动（不说 'be more careful'）",
        ],
        "common_mistakes": [
            "Improvement 太泛（'use better equipment' 没分）",
            "忘了算 uncertainty",
            "表格里不写单位",
            "安全建议太泛（'wear goggles' 不够具体）",
        ],
    },
    "phys_circuits": {
        "subject": "9702",
        "topic": "Electric Circuits / Kirchhoff's Laws",
        "question_recognition": [
            "关键词: circuit, current, voltage, resistance, Kirchhoff, potential divider",
            "常见问法: 'Calculate the current through...' / 'Explain why...'",
        ],
        "answer_template": [
            "Step 1: 标注电路中已知的电流方向",
            "Step 2: 应用 Kirchhoff 第一定律 (junction rule): ΣI_in = ΣI_out",
            "Step 3: 应用 Kirchhoff 第二定律 (loop rule): ΣV = 0 绕一圈",
            "Step 4: 用 V=IR 将电压转为电流×电阻",
            "Step 5: 解联立方程",
        ],
        "common_mistakes": [
            "符号方向搞反",
            "并联电阻公式用错: 1/R_total = 1/R₁ + 1/R₂",
            "忘了 internal resistance",
            "LDR/thermistor 电阻随光/温度变化的趋势记反",
        ],
    },

    # ===== ECONOMICS 9708 =====
    "econ_essay_20": {
        "subject": "9708",
        "topic": "20-Mark Essay Structure",
        "question_recognition": [
            "Paper 4 essay 题, 20 分",
            "关键词: Discuss, Evaluate, Assess, To what extent",
        ],
        "answer_template": [
            "Introduction (2-3 min): 定义关键词，重述论点",
            "Core Analysis (10-12 min):",
            "  画图并解释（至少2个 diagram）",
            "  2-3 个因果链条 (cause → mechanism → effect)",
            "Impacts (7-8 min):",
            "  短期 vs 长期，对不同群体的影响",
            "Evaluation (10-12 min): ← 最关键部分",
            "  维度1: 弹性依赖（PED/PES 影响效果）",
            "  维度2: 时间滞后（政策实施到见效有时间差）",
            "  维度3: 假设限制（ceteris paribus 不成立）",
            "  维度4: 意外后果",
            "  提出替代方案",
            "Conclusion (2-3 min): 做出有根据的判断，直接回答问题",
        ],
        "common_mistakes": [
            "单方面论述 → 零分 evaluation",
            "图画了但不解释 → 图画白画了",
            "Diagram 不标轴、不标曲线、不标均衡点",
            "结论不直接回答问题，只是总结",
        ],
        "keywords": [
            "AO1 (33%): Knowledge — define, recall facts",
            "AO2 (37%): Analysis — cause-and-effect chains",
            "AO3 (30%): Evaluation — weigh arguments, reach judgement",
        ],
    },
    "econ_data_response": {
        "subject": "9708",
        "topic": "Data Response Questions",
        "question_recognition": [
            "Paper 2 data response 题",
            "有 extract/table/graph 提供数据",
        ],
        "answer_template": [
            "Part (a): 直接从数据中提取/计算，引用具体数字",
            "Part (b): 解释趋势/关系，画图并用数据支持",
            "Part (c): 分析原因，2个以上的因果链，引用 extract",
            "Part (d): 评估，双面论述，用数据支持，有结论",
            "关键: 每部分都要引用 extract 中的具体数据！",
        ],
        "common_mistakes": [
            "不引用数据/不引用 extract → 低分",
            "只描述趋势不解释原因 → AO1 不是 AO2",
            "Part (d) 只给单方面分析 → 不给 evaluation 分",
        ],
    },

    # ===== MATHEMATICS 9709 =====
    "math_integration": {
        "subject": "9709",
        "topic": "Integration & Area Problems",
        "question_recognition": [
            "关键词: integrate, find the area, ∫, definite integral, volume of revolution",
        ],
        "answer_template": [
            "Step 1: 写出积分式 ∫ f(x) dx",
            "Step 2: 求不定积分 (antiderivative + C)",
            "  - ∫ xⁿ dx = xⁿ⁺¹/(n+1) + C (n ≠ -1)",
            "  - ∫ 1/x dx = ln|x| + C",
            "  - ∫ sin x dx = -cos x + C, ∫ cos x dx = sin x + C",
            "  - ∫ eˣ dx = eˣ + C",
            "Step 3: 定积分: [F(x)]ᵇₐ = F(b) - F(a)",
            "  - 必须展示代入上下限的过程！",
            "Step 4: 计算面积时注意曲线是否穿越 x 轴",
            "  - 如果穿越，要分段算，每段取绝对值",
            "Step 5: 体积: V = π ∫ y² dx",
        ],
        "common_mistakes": [
            "忘了写 +C（不定积分必扣分）",
            "直接用计算器积分不展示步骤 → 零分",
            "面积计算没检查曲线是否穿越 x 轴",
            "定积分代入上下限步骤不清晰",
        ],
        "keywords": [
            "∫ xⁿ dx = xⁿ⁺¹/(n+1) + C",
            "Definite: [F(x)]ᵇₐ = F(b) - F(a)",
            "Area: ∫ y dx, check for sign changes",
            "Volume of revolution: V = π∫ y² dx",
        ],
    },
    "math_differentiation": {
        "subject": "9709",
        "topic": "Differentiation & Applications",
        "question_recognition": [
            "关键词: differentiate, derivative, dy/dx, stationary point, rate of change, tangent, normal",
        ],
        "answer_template": [
            "Step 1: 套用微分法则",
            "  - d(xⁿ)/dx = nxⁿ⁻¹",
            "  - Chain rule: dy/dx = dy/du × du/dx",
            "  - Product: d(uv)/dx = u'v + uv'",
            "  - Quotient: d(u/v)/dx = (u'v - uv')/v²",
            "Step 2: Stationary point → dy/dx = 0",
            "  - 求二阶导数判断最大/最小",
            "Step 3: 切线斜率 = dy/dx at that point",
            "  - Tangent: y - y₁ = m(x - x₁)",
            "  - Normal: slope = -1/m",
            "Step 4: 相关速率: dx/dt = dx/dy × dy/dt",
        ],
        "common_mistakes": [
            "Chain rule 忘了乘内部的导数",
            "Stationary point 判断用错二阶导数符号",
            "混淆 tangent 和 normal 的斜率关系",
        ],
    },
}


def get_pattern(subject_code: str, topic_keywords: str) -> Optional[dict]:
    """Find matching exam pattern by subject + topic keywords."""
    topic_lower = topic_keywords.lower()
    best_match = None
    best_score = 0

    for key, pattern in PATTERNS.items():
        if pattern["subject"] != subject_code:
            continue
        topic = pattern["topic"].lower()
        score = sum(1 for word in topic_lower.split() if word in topic)
        if score > best_score:
            best_score = score
            best_match = pattern

    return best_match


def list_patterns_by_subject(subject_code: str) -> list:
    return [
        {"key": key, "topic": p["topic"]}
        for key, p in PATTERNS.items()
        if p["subject"] == subject_code
    ]


def format_pattern_for_prompt(pattern: dict) -> str:
    """Format a pattern into a readable string for the LLM context."""
    if not pattern:
        return ""

    lines = [f"## {pattern['topic']}"]
    lines.append("\n### 题型识别")
    for item in pattern.get("question_recognition", []):
        lines.append(f"- {item}")

    lines.append("\n### 标准答题步骤")
    for item in pattern.get("answer_template", []):
        lines.append(f"- {item}")

    lines.append("\n### 常见扣分点")
    for item in pattern.get("common_mistakes", []):
        lines.append(f"- {item}")

    lines.append("\n### 关键词/公式")
    for item in pattern.get("keywords", []):
        lines.append(f"- {item}")

    if pattern.get("analogy"):
        lines.append(f"\n### 推荐比喻\n{pattern['analogy']}")

    return "\n".join(lines)
