# 交点精度修复计划

> 日期：2026-06-02
> 问题：经济图交点位置错误

---

## 0. 根因分析

### 数学是对的，Spec 是错的

`solve_line_intersection(i1, s1, i2, s2)` 的计算是精确的。但交点错是因为 LLM 生成的 JSON spec 中**曲线之间的数学关系不正确**。

### 具体错误

| 图类型 | LLM 可能的错误 | 正确关系 |
|--------|---------------|---------|
| Monopoly | MR slope 随便写 | **MR slope = 2 × AR slope**（MR=9-2Q when AR=9-Q） |
| Externality | MSC intercept 随意 | **MSC intercept = MPC intercept + external_cost** |
| Tax | S+tax intercept 随意 | **S+tax intercept = S intercept + tax_amount** |
| Monopsony | MCL slope 随意 | **MCL slope = 2 × ACL slope**（线性供给） |
| AD-AS | AD/SRAS 任意 | **AD 必须在 LRAS 左侧与 SRAS 相交**（衰退缺口） |
| Demand shift | D2 intercept 任意 | **D2 = D1 + shift_amount** |

**根本问题**：LLM 不了解经济曲线之间的数学约束。它只是随便填数字。

---

## 1. 解决方案：LLM 描述 → Python 计算

### 新架构

```
LLM 输出：{"type": "monopoly", "demand_intercept": 9, "mc_slope": 0.8}
                ↓
Python 计算：AR = 9 - Q
           MR = 9 - 2Q  (自动从 AR 推导)
           MC = 1 + 0.8Q
           交点 = 精确计算
                ↓
           渲染为图
```

### 新旧对比

| | 旧（LLM 写 spec） | 新（Python 算 spec） |
|--|-------------------|---------------------|
| LLM 任务 | 写完整 JSON（含 intercept/slope） | 只写类型 + 少量参数 |
| 数学保证 | ❌ LLM 猜数字 | ✅ Python 算 |
| 弹性调整 | LLM 改 slope | 参数 "elastic"/"inelastic" |
| 平移 | LLM 改 intercept | 参数 shift=+2 |

---

## 2. 实现计划

### Step 1: 创建 `agent/diagrams/spec_builder.py`

每种图类型一个 builder 函数，接收高层参数，输出精确 spec：

```python
def build_demand_supply(elasticity="normal", shift=None, shift_curve=None, shift_amount=0):
    """elasticity: 'elastic'|'normal'|'inelastic'"""
    D_slope = {"elastic": -0.3, "normal": -1.0, "inelastic": -1.5}[elasticity]
    S_slope = 0.6
    D_intercept = 7
    S_intercept = 1.5
    
    curves = [{"id":"D","type":"line","intercept":D_intercept,"slope":D_slope,...}]
    
    if shift and shift_curve == "demand":
        curves.append({"id":"D2","type":"line","intercept":D_intercept+shift_amount,...})
    
    equilibria = [{"c1":"D","c2":"S","label":"E"}]
    return {"curves": curves, "equilibria": equilibria, ...}

def build_monopoly(D_intercept=9, MC_slope=0.8):
    """AR=D, MR=2×AR slope, MC"""
    AR_intercept = D_intercept
    AR_slope = -1.0
    MR_intercept = D_intercept       # Same intercept
    MR_slope = 2 * AR_slope          # = -2.0 ← THIS IS THE FIX
    
def build_externality(D_intercept=7, D_slope=-1, external_cost=1.5):
    """MSC = MPC + external_cost"""
    MPC_intercept = 1.5
    MPC_slope = 0.6
    MSC_intercept = MPC_intercept + external_cost  # ← FIX
    MSC_slope = MPC_slope                           # ← FIX
```

### Step 2: 更新 LLM prompt

不再让 LLM 写完整 JSON spec，只写类型引用：

```
经济图类型：
- `demand_supply` (elasticity: elastic/normal/inelastic)
- `demand_shift` (direction: right/left, amount: +N/-N)
- `externality` (type: negative/positive, external_cost: N)
- `tax` (amount: N, on: consumer/producer)
- `monopoly` (D_intercept: N)
- `ad_as` (gap: recessionary/inflationary)
...
```

LLM 输出：`` ```plot {"type": "monopoly", "D_intercept": 9} ``

### Step 3: 更新 render_all_diagrams

```python
def extract_and_render_plot(content):
    # Parse {"type": "monopoly", ...}
    # Call spec_builder.build_monopoly(...)
    # Render the built spec
```

### Step 4: 测试

每个类型测试：
- 默认参数 → 图生成正确
- 弹性变化 → 斜率正确
- 平移变化 → 新曲线位置正确
- 交点计算 → 手动验算 5 个关键图的交点

---

## 3. 优先级

| 优先级 | 图类型 | 原因 |
|--------|--------|------|
| P0 | demand_supply + shift | 基础图的平移必须有正确交点 |
| P0 | externality | MSC=MPC+external_cost 必须保证 |
| P0 | monopoly | MR=2×AR 是核心特征 |
| P0 | tax | S+tax=S+amount 是核心特征 |
| P1 | AD-AS | AD/SRAS 交点 + LRAS 位置 |
| P1 | monopsony | MCL=2×ACL |
| P2 | others | tariff, subsidy, price controls |
