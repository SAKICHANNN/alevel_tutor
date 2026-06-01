# 图表渲染系统 — 终极方案

> 版本：v2.0 | 日期：2026-06-01
> 基于：深度研究 + W5 全部经验教训 + 回滚后的最新起点
> 起点 commit：dcd4afe (Kroki 4-engine baseline)

---

## 0. 经验教训（W5 全部失败总结）

| 尝试 | 方法 | 失败原因 |
|------|------|---------|
| 1 | Prompt 引导 LLM 用 Mermaid | LLM 仍输出 ASCII，且 Gradio 4.44.1 无 Mermaid.js |
| 2 | CDN 注入 Mermaid.js + MutationObserver | 脚本注入不可靠，Gradio 动态 DOM 难以追踪 |
| 3 | Kroki API 服务端渲染 | **成功** — 但 LLM 写的不精确坐标仍然不对 |
| 4 | matplotlib econ plotter (PNG) | PNG base64 58K 太大，Gradio markdown 不渲染 |
| 5 | matplotlib SVG | 16K 仍大，5 张图 = 80K 撑爆对话 |
| 6 | @diagram 自动注入 | 多关键词注入多图，重复渲染 |
| 7 | base64 inline 嵌入 | 任何 base64 方案都会撑大回答、污染对话历史 |

**核心教训：**
- **LLM 不会画图 — LLM 只会描述要画什么。** 让 LLM 写 TikZ 坐标 = 让 monkey 画 Monet。
- **base64 inline 在任何规模下都是死路。** 必须渲染到文件 → 网络 URL 引用。
- **模板不够灵活。** 经济图需要能调整弹性、标注不同点。

---

## 1. 全科目图表需求调查

### 1.1 9701 Chemistry (8 类)

| 类型 | 数量 | 精确度要求 | 推荐引擎 |
|------|------|-----------|---------|
| 化学方程式 | 高频 | 下标/箭头/状态符号 | **mhchem (Kroki TikZ)** |
| 结构式/骨架式 | 高频 | 键角/异构体 | **chemfig (Kroki TikZ)** |
| 反应机理（卷曲箭头） | P2/P4 | 箭头方向+中间体 | **chemfig + VLM 描述** |
| 能量循环 (Born-Haber/Hess) | P2/P4 | ΔH 标注+物种排列 | **TikZ (Kroki)** |
| 分子几何 (VSEPR) | 高频 | wedge/dash + 键角 | **TikZ** |
| 光谱图 (IR/NMR/MS) | P1 | 峰值/化学位移 | **matplotlib** |
| 速率/滴定/pH 曲线 | P2/P4 | 拐点/等当点 | **matplotlib** |
| 实验数据表 | 全卷 | 精度+单位 | **Markdown/HTML** |

### 1.2 9702 Physics (7 类)

| 类型 | 数量 | 精确度要求 | 推荐引擎 |
|------|------|-----------|---------|
| 电路图 | P1-P5 | 元件符号/连接 | **circuitikz (Kroki TikZ)** |
| 自由体图/力分解 | P4 | 矢量方向/角度 | **TikZ (Kroki)** |
| 波形图 (干涉/衍射) | P2/P4 | 波峰/波节/λ标注 | **matplotlib** |
| I-V/放电/谐振曲线 | P2/P4 | 轴+数据点 | **matplotlib** |
| 场线图 (电/磁/引力) | P2/P4 | 箭头密度/方向 | **TikZ (Kroki)** |
| 实验装置 | P3 | 模块示意 | **TikZ / Mermaid** |
| 数据表（含不确定度） | 全卷 | 有效数字 | **Markdown** |

### 1.3 9708 Economics (14 类，全部需要精确数学)

| 类型 | 精确度要求 | 推荐引擎 |
|------|-----------|---------|
| 供需均衡 + 平移 | 交点必须用方程解 | **Python + matplotlib** |
| 弹性 (PED/PES/YED/XED) | 斜率精确反映弹性值 | **Python + matplotlib** |
| 负/正外部性 + DWL | MSC/MPC 间距 = 外部成本 | **Python + matplotlib** |
| 税收/补贴归宿 | 楔子宽度 = 税/补贴额 | **Python + matplotlib** |
| 价格上限/下限 | 短缺/过剩精确到交点 | **Python + matplotlib** |
| AD-AS 模型 | AD/SRAS 交点 + LRAS 位置 | **Python + matplotlib** |
| 垄断/买方垄断 | MR 斜率 = 2×AR | **Python + matplotlib** |
| 关税 | 5 区域精确 | **Python + matplotlib** |
| PPC/PPF | 凹形 + 增长平移 | **Python + matplotlib** |
| 凯恩斯 LRAS | 三段式精确 | **Python + matplotlib** |
| 菲利普斯曲线 | SR/LR 区分 | **Python + matplotlib** |
| 比较优势 | 两个国家 + 相对价格 | **Python + matplotlib** |
| 汇率 | 供需或利率平价 | **Python + matplotlib** |
| Lorenz 曲线 | 累积比例精确 | **Python + matplotlib** |

**关键洞察：经济学 14 类图全部可以归约为「画直线 + 求交点 + 标点 + 填色」。完全可以用同一个 Python 引擎处理。**

### 1.4 9709 Mathematics (7 类)

| 类型 | 精确度要求 | 推荐引擎 |
|------|-----------|---------|
| 坐标几何 (圆/线/切线) | 准确坐标 | **Python + matplotlib** / TikZ pgfplots |
| 三角函数图 | 周期/振幅/相位 | **Python + matplotlib** |
| 力学图 (滑轮/斜面) | 矢量方向 | **TikZ** |
| 向量图 (2D/3D) | 坐标轴+方向 | **TikZ** |
| 函数图 (积分/微分) | 零点/驻点 | **Python + matplotlib** |
| 统计分布/累积频率 | 直方图正确 | **Python + matplotlib** |
| 数值方法 (迭代/牛顿) | 切线+根 | **Python + matplotlib** |

---

## 2. 架构设计

### 2.1 核心理念

```
LLM 负责：描述「画什么」— 什么类型的图、哪些曲线、怎么标注
Python 负责：计算「怎么画」— 求交点、算斜率、渲染输出
Kroki 负责：部分 TikZ 模板的 LaTeX 渲染
文件系统负责：存储渲染结果
Gradio 负责：用短 URL 引用图片
```

### 2.2 数据流

```
用户提问 → Agent (DeepSeek)
                ↓
          LLM 回复（含图表规格）
                ↓
          _sanitize_output
                ↓
          extract_and_render_*
                ↓
   ┌───────────┼───────────┐
   ↓           ↓           ↓
```mermaid  ```tikz  ```plot
   ↓           ↓           ↓
 Kroki      Kroki      Python
 render     render     matplotlib
   ↓           ↓           ↓
  SVG        SVG        PNG
   └───────────┼───────────┘
               ↓
      保存到 data/rendered/{hash}.{svg|png}
               ↓
      替换为 ![diagram](/diagrams/{hash}.{ext})
         （短 URL，不是 base64！）
```

### 2.3 新格式规范

**格式 1：```plot — Python matplotlib 渲染（经济图/函数图/数据图）**
```
```plot
{
  "type": "economics",
  "diagram": "demand_supply",
  "curves": [
    {"id": "D", "intercept": 7, "slope": -1, "label": "D", "color": "blue"},
    {"id": "S", "intercept": 1.5, "slope": 0.6, "label": "S", "color": "red"}
  ],
  "equilibria": [{"c1": "D", "c2": "S", "label": "E"}],
  "shading": [],
  "axes": {"x": "Quantity", "y": "Price"}
}
```
```

**格式 2：```tikz — Kroki LaTeX 渲染（电路/化学/力学图）**
保留现有 Kroki TikZ 通路，不再做 template 框架。

**格式 3：```mermaid — Kroki 流程图**（已有，不变）

### 2.4 文件服务

在 web/app.py 中添加 Gradio 静态路由：
```python
# 服务 data/rendered/ 目录下的图片
demo.mount("/diagrams", gr.StaticFiles(directory="data/rendered"))
```

渲染后的图片通过 `![diagram](/diagrams/abc123.svg)` 引用 → 零 base64 膨胀。

---

## 3. 实现路线图

### Phase 1：核心渲染引擎（Python matplotlib）

**文件**：`agent/diagrams/plotter.py`

实现 `render_plot(spec: dict) -> Path`：
- 解析 JSON spec
- 调用 matplotlib 渲染
- 保存到 `data/rendered/{hash}.svg`
- 返回文件路径

**支持的经济图类型**（通过参数化 spec 覆盖全部 14 种）：
- demand_supply, demand_shift, supply_shift
- externality (positive/negative/production/consumption)
- tax, subsidy
- price_ceiling, price_floor
- ad_as, ad_shift
- monopoly, monopsony
- tariff
- ppc
- keynesian_lras

**数学保证**：
- 所有交点通过 `scipy.optimize` 或代数求解
- 所有标注位置通过坐标计算
- 所有填色区域通过多边形定义

### Phase 2：LLM 集成

**更新 system prompt**：
- 移除所有旧的 TikZ 示例
- 添加 `plot` 格式的示例
- 强制：「画经济图/函数图 → 用 `\`\`\`plot`，画电路/化学/力学 → 用 `\`\`\`tikz`」

**更新 render_all_diagrams()**：
- 添加 `extract_and_render_plot()`
- 处理顺序：plot → mermaid → tikz → vegalite

### Phase 3：VLM 质量验证

对每种图类型：
1. 生成示例 spec
2. 渲染到文件
3. Qwen VL 检查：标注是否完整、曲线是否正确、是否符合 Cambridge 标准
4. 迭代修正直到 Grade A

### Phase 4：测试套件

每种图类型 3+ 测试用例：
- 完美答案
- 平移/弹性变化
- 边界情况

### Phase 5：物理/化学扩展

将 plotter 模式扩展到：
- 波形图（干涉/衍射）
- I-V 特性曲线
- 速率曲线
- 等

---

## 4. 关键决策

| 决策 | 理由 |
|------|------|
| Python matplotlib 做主引擎 | 精确数学、LLM 只需描述不要计算 |
| SVG 格式 > PNG | 体积小（16K vs 58K）、矢量无损 |
| 文件 URL > base64 inline | 零膨胀、对话历史清洁 |
| Kroki TikZ 保留为辅助 | 电路/化学结构仍需 LaTeX |
| 不自己做模板系统 | 参数化 spec 比硬编码模板更灵活 |
| VLM 做质量检查 | 唯一能确定「肉眼看起来对不对」的方法 |

## 5. 成功标准

- [ ] 任意经济概念提问 → 自动产生精确图（交点数学解）
- [ ] 图显示在 Gradio 聊天中，无 base64 膨胀
- [ ] VLM 对每种图类型给出 Grade A
- [ ] 多轮对话不受图表影响
- [ ] 物理/化学/数学图也都通过 Kroki 正常渲染
- [ ] ASCII 字符图 = 0 出现

---

## 6. 开发流程规范

### 6.1 分支策略

| 阶段 | 分支 | 说明 |
|------|------|------|
| Phase 1 | `feat/diagram-plotter` | Python matplotlib 渲染引擎 |
| Phase 2 | `feat/diagram-llm-int` | LLM 集成 + system prompt 更新 |
| Phase 3 | `feat/diagram-vlm` | VLM 质量验证 |
| Phase 4 | `feat/diagram-tests` | 测试套件 |
| Phase 5 | `feat/diagram-physchem` | 物理/化学扩展 |

每个分支从 `main` 切出，完成后 merge 回 `main`。

### 6.2 Commit 规范

| 时机 | 消息格式 | 示例 |
|------|---------|------|
| 每完成一个图类型 | `feat(diagram): demand_supply plotter with intersection solver` | — |
| 每通过一个 VLM 检查 | `verify(diagram): demand_supply Grade A VLM-confirmed` | — |
| 每 fix 一个 bug | `fix(diagram): projection lines missing on tax diagram` | — |
| 每通过一个测试 | `test(diagram): add 5 demand_supply variant test cases` | — |
| 每完成一个阶段 | `feat(diagram): Phase 1 complete — all 14 econ types` | — |

**规则**：每完成一个最小可验证单元（一个图类型、一个测试、一个 bug fix）立即 commit，不积攒。

### 6.3 Log 规范

**文件**：`docs/log/diagram_v2.md`（新建）

**每次 commit 后记录**：
- 做了什么
- 为什么这样做（决策原因）
- 遇到的问题 + 如何解决的
- 下一步

**格式**：
```
## Phase 1 — 2026-06-02

### commit abc1234: demand_supply plotter
- 实现：matplotlib 渲染，对称轴标签，投影线
- 决策：用 scipy.optimize.fsolve 解交点而非代数 —— 因为后续要支持非线性曲线
- 问题：matplotlib 中文字体缺失 → 回退英文标签
- 下一步：实现 demand_shift 变体
```

### 6.4 测试规范

**每个图类型至少 3 个测试用例**：

| 用例 | 目的 |
|------|------|
| 完美答案 | 验证基本渲染正确（无错误、有SVG输出） |
| 参数变化 | 验证弹性/平移/缩放（不同 intercept/slope） |
| 边界情况 | 验证极端参数（完美弹性/无弹性/零值） |

**测试文件**：`tests/test_diagram_v2.py`

**测试结构**：
```python
# 每个图类型一个 test class
class TestDemandSupply:
    def test_basic_equilibrium(self): ...
    def test_elastic_demand(self): ...
    def test_perfectly_inelastic(self): ...

class TestADAS:
    def test_basic_ad_as(self): ...
    def test_demand_pull_inflation(self): ...
    def test_cost_push_stagflation(self): ...
```

**每次 Phase 完成后**：
```bash
PYTHONPATH=. python3 tests/test_diagram_v2.py
# 目标：全部 PASS，0 FAIL
```

### 6.5 Debug 规范

**遇到任何渲染问题时**：

1. **隔离**：用最小 spec 复现问题
2. **对比**：与 Cambridge 教材/真题对照
3. **VLM 检查**：`curl` 发送渲染结果给 Qwen VL，问「这张图符合 Cambridge A-Level 标准吗？哪里不对？」
4. **修复**：改代码 → 重新渲染 → 再 VLM
5. **记录**：问题 + 根因 + 修复 → `docs/log/diagram_v2.md`

**VLM Debug 命令模板**：
```bash
# 1. 生成图
python3 -c "from agent.diagrams.plotter import render; render('demand_supply', {...})" > /tmp/test.svg

# 2. VLM 检查
python3 -c "
import base64, requests
svg = open('/tmp/test.svg','rb').read()
b64 = base64.b64encode(svg).decode()
r = requests.post('http://127.0.0.1:1234/v1/chat/completions', json={
  'model':'qwen/qwen3-vl-8b',
  'messages':[{'role':'user','content':[
    {'type':'text','text':'Grade this Cambridge A-Level diagram. Check axes, curves, labels, intersections. Output JSON: {pass:bool, grade:A/B/C/F, issues:[], summary:str}'},
    {'type':'image_url','image_url':{'url':f'data:image/svg+xml;base64,{b64}'}}
  ]}],
  'temperature':0.1, 'max_tokens':300
}, timeout=120)
print(r.json()['choices'][0]['message']['content'])
"
```

### 6.6 回滚保护

**每个 Phase 开始前**：
```bash
git branch backup-$(date +%Y%m%d-%H%M)  # 创建时间戳备份
```

**每个 Phase 完成后**：
```bash
git tag phase-1-complete  # 打标签，方便快速回退
```
