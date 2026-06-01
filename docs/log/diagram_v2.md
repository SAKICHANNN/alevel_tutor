# Diagram V2 Development Log

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
