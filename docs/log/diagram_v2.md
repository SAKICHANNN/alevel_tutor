# Diagram V2 Development Log

## Phase 0 — 2026-06-01

### commit 89aa7a8: econ diagrams learning plan
- `docs/plans/econ_diagrams_learn_plan.md` — Phase 0 research: 经济学考试所需图类型、现有 TikZ/Mermaid 方案、VLM 验证策略

### commit 227f4f0: workflow specification
- `docs/plans/diagram_system_v2.md` §6 — 工作流规范：分支策略、commit 格式、log 编写、测试先行、debug 流程、回滚 guard

## Phase 1 — 2026-06-01

### commit 7946281: Python matplotlib plotter
- 实现：render_economics(json_spec) → compact PNG (55 DPI, ~17KB)
- 决策：用代数 solve_line_intersection() 求解交点而非 scipy（线性方程不需要迭代）
- 6 种曲线类型：line (intercept+slope), vertical, horizontal
- 均衡点：投影虚线到轴，白边黑点，可配置偏移标签
- 填色：between 类型，支持两曲线间区域
- 9 色调色板：demand, supply, msc, msb, ad, sras, lras, tax, dwl 等
- 同时保存完整 SVG 到 data/rendered/ 供 VLM 检查
- 问题：StaticFiles mount 在 Gradio 4.44.1 中 404（路由冲突）
- 解决：改用 compact base64 PNG inline（17KB vs 原 58KB PNG / 16KB SVG）
- 下一步：Phase 2 — LLM 集成 + system prompt 更新

## Phase 2 — 2026-06-01

### commit 2510b80: LLM integration
- 实现：system prompt 更新 — 精简版图表规则
- 决策：移除 67 行冗长 TikZ 示例，替换为 3 行 `plot` JSON 格式说明
- 经济图 → ```plot JSON，电路/化学 → ```tikz template=xxx
- 观察：LLM 仍在用旧 TikZ 格式，但渲染管道已支持 `plot`
- 下一步：Phase 3 — VLM 验证渲染质量

## Phase 3 — 2026-06-01

### commit 8cf5dcd: Cambridge-standard diagram style
- 100 DPI → 提升清晰度
- Bold labels — 坐标轴字体加粗
- Larger figure size — 增大画布防止文字重叠
- Cambridge exam style palette: 蓝(D)、红(S)、绿(MSB)……

### commit ce95399: intersection fix plan
- 文档：LLM 描述意图，Python 计算精确坐标（而非反过来）
- 根本原因：LLM 不具备生成精确数学坐标的能力（DeTikZify/CAGE 论文验证）

## Phase 4 — 2026-06-01

### commit fa5085c: spec_builder — LLM describes type, Python computes exact math
- 新增 `agent/diagrams/spec_builder.py`：LLM 只填类型+参数，Python 计算交点/斜率
- 模式：`{"type": "demand_supply", "elasticity": "elastic"}` → builder 计算完整 spec → plotter 渲染
- 14 种经济图类型支持
- 35 项图表测试全部通过（test_diagram_v2.py），VLM 验证 Grade A on 2/3 类型

### commit 59ab005: shading uses equilibrium labels
- 填色区域改用 Pe/Qe 标签代替手动 x1/x2 坐标
- 避免 LLM 猜测网格坐标导致填色错位

### commit d08a56d: 35 diagram tests
- 35 项图表测试全部通过（test_diagram_v2.py）
- VLM 验证：Grade A on 2/3 diagram types

### commit 1c1664c: max_tokens 4096→8192
- 避免长回复（含多张图表）被截断
- 后进一步扩到 20480

### commit 99ae2d7: ASCII detection patch
- `_sanitize_output` ASCII 检测同时检查 `data:image/png`（不限于 svg）
- 修复：PNG 图表存在时误报 ASCII 警告

### commit 76b4271: PNG → SVG output
- 输出格式从 base64 PNG (50KB) 切换到 base64 SVG (16KB)，体积 3x 减小
- **彻底解决中文乱码**：SVG 直接嵌入文字不再依赖 matplotlib 字体系统
- 新增 LLM 生成 SVG 的系统提示模板（坐标轴、色系、标注规范）
- 限制每回复最多 2 张图（`prompts.py:18`），避免 8 张图刷屏占用 token
