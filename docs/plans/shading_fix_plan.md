# 面积/填色修复计划

> 问题：经济图涉及面积（DWL、消费者剩余、税收矩形等）没显示
> 根因：填色功能需要 x1/x2 坐标，但 LLM 不知道这些值

---

## 根因

当前 `_draw_shading` 需要手动指定 `x1`, `x2`：
```python
x1 = sh.get("x1", 0)  # LLM 写 0 → 填了整张图
x2 = sh.get("x2", x_max)
```

LLM 不知道均衡点的 x 坐标，所以填色要么不填，要么填错范围。

---

## 修复方案

### 核心思路：填色自动引用均衡点

不要求 LLM 写 x1/x2。LLM 只指定：
- 填哪两条线之间（upper_curve, lower_curve）
- 从哪个均衡点到哪个均衡点（left_eq, right_eq）

**示例（外部性 DWL）**：
```json
"shading": [
  {"type": "between", "upper": "MSC", "lower": "MPC",
   "left_eq": "Eₛ", "right_eq": "Eₚ",
   "color": "dwl", "label": "DWL"}
]
```

**示例（税收消费者负担）**：
```json
"shading": [
  {"type": "between", "upper": "D", "lower": "S",
   "left_eq": "E", "right_eq": "E_t",
   "color": "cs", "label": "consumer burden"}
]
```

### 实现步骤

**Step 1: 保存均衡点坐标**
渲染时把所有均衡点存入 `{label: (x, y)}` 字典。

**Step 2: 重写 `_draw_shading`**
```python
def _draw_shading(ax, sh, drawn, eq_points, x_max):
    upper = sh.get("upper")  # 上方曲线 ID
    lower = sh.get("lower")  # 下方曲线 ID
    left_eq = sh.get("left_eq")   # 左边界（均衡点标签）
    right_eq = sh.get("right_eq") # 右边界
    
    # 从均衡点获取 x 坐标
    x1 = eq_points.get(left_eq, (0, 0))[0]
    x2 = eq_points.get(right_eq, (x_max, 0))[0]
    
    # 取 upper/lower 曲线在 [x1, x2] 区间的 y 值
    xs = np.linspace(x1, x2, 100)
    y_upper = upper_line(xs)
    y_lower = lower_line(xs)
    
    ax.fill_between(xs, y_upper, y_lower, ...)
```

**Step 3: 更新 spec_builder**
自动为需要填色的图类型生成 shading spec：
- `build_externality` → DWL 填色
- `build_tax` → 消费者/生产者负担填色
- `build_monopoly` → DWL 三角形

---

## 实施顺序

1. 重写 `_draw_shading` — 用均衡点引用
2. 更新 `_plot` — 保存均衡点坐标
3. 更新 `spec_builder` — 自动生成 shading
4. 测试 → VLM 验证
