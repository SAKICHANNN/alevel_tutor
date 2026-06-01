# 经济学图表 — 学习计划 v3

> 日期：2026-06-02
> 状态：研究阶段，尚未实现
> 目标：让每张图达到 Cambridge 9708 评分标准

---

## 0. 问题诊断（为什么现在的图不对）

### 剑桥评分标准（来自官方 MS）
| 要求 | 我们的现状 | 差距 |
|------|-----------|------|
| "accurately labeled axes" | 标了但可能不对（"Real GDP" vs "Price Level"） | 需要对照官方 specimen |
| "correctly drawn diagram" | 曲线斜率对，但形状/比例不标准 | VLM 能看出问题 |
| "clearly labeled equilibrium" | 有点，但投影线太淡 | 需要更粗的虚线 |
| "diagram not too small" | 55 DPI 太模糊 | 至少 100 DPI |
| "axes labeled price level and real GDP" | 只写了 "Real GDP" | 必须写 "Real GDP (Y)" |

### 根本问题
1. **我不知道真实的 Cambridge 图是什么样子** — 我的知识来自 LLM 记忆，不是实际教材
2. **参数是猜测的** — intercept=7, slope=-1 是随手写的，没有参照真实数据
3. **图太小/太模糊** — 55 DPI 无法展示细节

---

## 1. 学习阶段（Research Only）

### 1.1 获取参考材料
- [ ] 下载 Cambridge 9708 教材 PDF（已在 data/textbooks/）
- [ ] 从教材中提取所有标准图（用 PyMuPDF 渲染）
- [ ] 从 past papers 和 mark schemes 中提取 specimen 答案的图
- [ ] 收集 tutor2u Diagram Bank 2024/25（免费资源）

### 1.2 学习每种图
对每种经济图，从教材中学习：
- 标准坐标轴标签（精确文字）
- 曲线标注格式（D, S, AD, SRAS 等的字体位置）
- 均衡点标注（E₁, E₂，是否用圆圈）
- 投影线样式（虚线实线？到轴还是只到边？）
- 填色区域标注（DWL、消费者剩余等的文字位置）
- 箭头标注（平移方向、税收楔子等）

### 1.3 使用 VLM 对比
- 渲染我们的图 + 教材原图 → VLM 逐项对比
- 记录每项偏差
- 修正后重新对比

---

## 2. 实现阶段（After Learning）

### 2.1 重建 plotter.py
- 图尺寸：至少 100 DPI
- 轴标签：严格使用 Cambridge 标准文字
- 曲线粗细：3px（更清晰）
- 投影线：更粗的虚线（1px）
- 标签字体：更大（14pt+）
- 填色：更明显的透明度

### 2.2 参数模板
每种图保存一个"黄金参数"模板，来自教材：
```json
{
  "type": "demand_supply",
  "source": "Cambridge Economics Coursebook 4th Ed, Ch 3",
  "params": {
    "D": {"intercept": 7, "slope": -1},
    "S": {"intercept": 1.5, "slope": 0.6}
  }
}
```

### 2.3 验证流程
每修改一种图 → 跑 48 项测试 → VLM 检查 → 记录 Grade

---

## 3. 需要确认的决策

| 决策 | 选项 | 推荐 |
|------|------|------|
| 图格式 | PNG vs SVG | **SVG**（矢量清晰，虽大但可接受） |
| 嵌入方式 | base64 inline vs 文件 URL | **文件 URL 优先**（base64 太大） |
| 尺寸 | 8×6 vs 10×8 | **10×8**（考官说"diagram not too small"） |
| DPI | 55 vs 100 vs 150 | **100**（平衡清晰度和体积） |

---

## 4. 实施顺序

```
Phase A: 学习（只看不做）
  A1: 从教材提取参考图（PyMuPDF 渲染）
  A2: 从 past papers 提取 specimen 答案图
  A3: 收集 tutor2u Diagram Bank
  
Phase B: 对比（VLM 辅助）
  B1: 渲染我们的图 + 教材参考图 → VLM 对比
  B2: 逐一记录偏差
  
Phase C: 重建（逐个修理）
  C1: 修复 demand_supply → VLM Grade A
  C2: 修复 externality → VLM Grade A
  C3: 修复 AD-AS → VLM Grade A
  C4: ... 逐个完成全部 14 种
  
Phase D: 验证
  D1: 48 项测试全部通过
  D2: 所有图 VLM Grade A 或 B
  D3: 用户验收
```
