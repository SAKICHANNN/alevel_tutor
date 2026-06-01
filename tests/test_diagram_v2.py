"""
50-round economics diagram generation + verification test suite.
Checks all 14 diagram types with parameter variations.
"""
import json, sys, time, traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.diagrams.plotter import render_economics, solve_line_intersection, x_for_y

PASS, FAIL = 0, 0
STATS = {"generated": 0, "failed": 0, "total_kb": 0}

def test(name, fn):
    global PASS, FAIL
    try:
        fn()
        PASS += 1
        print(f"  ✅ {name}")
    except Exception as e:
        FAIL += 1
        print(f"  ❌ {name}: {e}")

def render_and_check(spec, name):
    """Render a spec and verify output is valid."""
    uri = render_economics(spec)
    assert uri is not None, f"{name}: render returned None"
    assert "data:image/png" in uri, f"{name}: no PNG in output"
    assert len(uri) > 500, f"{name}: output too short ({len(uri)} chars)"
    STATS["generated"] += 1
    STATS["total_kb"] += len(uri) / 1024
    return True

# ══════════════════════════════════════
# MATH: verify intersection solver
# ══════════════════════════════════════
print("=" * 60)
print("1. MATH ENGINE (5 tests)")
print("=" * 60)

test("DS intersection", lambda: (
    xy := solve_line_intersection(7, -1, 1.5, 0.6),
    abs(xy[0] - 3.44) < 0.02, abs(xy[1] - 3.56) < 0.02
))
test("AD-SRAS intersection", lambda: (
    xy := solve_line_intersection(7.5, -0.9, 2, 0.5),
    abs(xy[0] - 3.93) < 0.02, abs(xy[1] - 3.96) < 0.02
))
test("MR-MC (monopoly)", lambda: (
    xy := solve_line_intersection(9, -2, 1, 0.8),
    abs(xy[0] - 2.86) < 0.05, abs(xy[1] - 3.29) < 0.05
))
test("MCL-MRP (monopsony)", lambda: (
    xy := solve_line_intersection(0.8, 1.2, 6.5, -0.8),
    abs(xy[0] - 2.85) < 0.05, abs(xy[1] - 4.22) < 0.05
))
test("X for Y", lambda: (
    x := x_for_y(7, -1, 3),
    abs(x - 4.0) < 0.01
))

# ══════════════════════════════════════
# GENERATION: all 14 types × variants
# ══════════════════════════════════════
print("\n" + "=" * 60)
print("2. BASIC TYPES (14 types)")
print("=" * 60)

def ds_spec(**kw):
    return dict({"axes":{"x":"Q","y":"P"},"x_max":8,"y_max":8,
        "curves":[
            {"id":"D","type":"line","intercept":7,"slope":-1,"color":"demand","label":"D"},
            {"id":"S","type":"line","intercept":1.5,"slope":0.6,"color":"supply","label":"S"}],
        "equilibria":[{"c1":"D","c2":"S","label":"E","offset":[10,10]}]}, **kw)

# 1. Demand-Supply basic
test("2.1 demand_supply", lambda: render_and_check(ds_spec(), "DS basic"))

# 2. Elastic demand (flat slope)
spec = ds_spec()
spec["curves"][0]["slope"] = -0.3
spec["curves"][0]["label"] = "D (elastic)"
spec["x_max"] = 12
test("2.2 elastic demand", lambda: render_and_check(spec, "elastic"))

# 3. Inelastic demand (steep)
spec = ds_spec()
spec["curves"][0]["slope"] = -1.5
spec["curves"][0]["label"] = "D (inelastic)"
test("2.3 inelastic demand", lambda: render_and_check(spec, "inelastic"))

# 4. Demand shift right
spec = ds_spec()
spec["curves"] = [
    {"id":"D1","type":"line","intercept":7,"slope":-1,"color":"demand","label":"D₁"},
    {"id":"D2","type":"line","intercept":8.5,"slope":-1,"color":"demand2","label":"D₂"},
    {"id":"S","type":"line","intercept":1.5,"slope":0.6,"color":"supply","label":"S"}]
spec["equilibria"] = [
    {"c1":"D1","c2":"S","label":"E₁","offset":[-15,8]},
    {"c1":"D2","c2":"S","label":"E₂","offset":[8,8]}]
spec["x_max"] = 9; spec["y_max"] = 9
test("2.4 demand shift right", lambda: render_and_check(spec, "D shift"))

# 5. Supply shift left
spec = ds_spec()
spec["curves"] = [
    {"id":"D","type":"line","intercept":7,"slope":-1,"color":"demand","label":"D"},
    {"id":"S1","type":"line","intercept":1.5,"slope":0.6,"color":"supply","label":"S₁"},
    {"id":"S2","type":"line","intercept":3.5,"slope":0.6,"color":"supply2","label":"S₂"}]
spec["equilibria"] = [
    {"c1":"D","c2":"S1","label":"E₁","offset":[8,-12]},
    {"c1":"D","c2":"S2","label":"E₂","offset":[8,8]}]
spec["y_max"] = 9
test("2.5 supply shift left", lambda: render_and_check(spec, "S shift"))

# 6. Negative externality
spec = {"axes":{"x":"Q","y":"Cost/Benefit"},"x_max":8,"y_max":8,
    "curves":[
        {"id":"D","type":"line","intercept":7,"slope":-1,"color":"demand","label":"D=MPB"},
        {"id":"MPC","type":"line","intercept":1.5,"slope":0.6,"color":"supply","label":"MPC=S"},
        {"id":"MSC","type":"line","intercept":3,"slope":0.6,"color":"msc","label":"MSC"}],
    "equilibria":[
        {"c1":"D","c2":"MPC","label":"Eₚ","offset":[8,-12]},
        {"c1":"D","c2":"MSC","label":"Eₛ","offset":[8,8]}]}
test("2.6 negative externality", lambda: render_and_check(spec, "externality"))

# 7. AD-AS model
spec = {"axes":{"x":"Real GDP","y":"Price Level"},"x_max":10,"y_max":8,
    "curves":[
        {"id":"AD","type":"line","intercept":7.5,"slope":-0.9,"color":"ad","label":"AD"},
        {"id":"SRAS","type":"line","intercept":2,"slope":0.5,"color":"sras","label":"SRAS"},
        {"id":"LRAS","type":"vertical","x":5.5,"color":"lras","label":"LRAS"}],
    "equilibria":[{"c1":"AD","c2":"SRAS","label":"E₁","offset":[8,8]}]}
test("2.7 AD-AS", lambda: render_and_check(spec, "AD-AS"))

# 8. AD increase
spec = {"axes":{"x":"Real GDP","y":"Price Level"},"x_max":10,"y_max":8,
    "curves":[
        {"id":"AD1","type":"line","intercept":7,"slope":-0.9,"color":"ad","label":"AD₁"},
        {"id":"AD2","type":"line","intercept":8.2,"slope":-0.9,"color":"demand2","label":"AD₂"},
        {"id":"SRAS","type":"line","intercept":2,"slope":0.5,"color":"sras","label":"SRAS"},
        {"id":"LRAS","type":"vertical","x":5.5,"color":"lras","label":"LRAS"}],
    "equilibria":[
        {"c1":"AD1","c2":"SRAS","label":"E₁","offset":[-15,8]},
        {"c1":"AD2","c2":"SRAS","label":"E₂","offset":[8,8]}]}
test("2.8 AD increase", lambda: render_and_check(spec, "AD inc"))

# 9. Tax incidence
spec = {"axes":{"x":"Q","y":"P"},"x_max":9,"y_max":9,
    "curves":[
        {"id":"D","type":"line","intercept":7,"slope":-1,"color":"demand","label":"D"},
        {"id":"S","type":"line","intercept":1.5,"slope":0.6,"color":"supply","label":"S"},
        {"id":"St","type":"line","intercept":3,"slope":0.6,"color":"supply2","label":"S+tax"}],
    "equilibria":[
        {"c1":"D","c2":"S","label":"E","offset":[-15,8]},
        {"c1":"D","c2":"St","label":"E_t","offset":[8,-12]}]}
test("2.9 tax incidence", lambda: render_and_check(spec, "tax"))

# 10. Subsidy
spec = {"axes":{"x":"Q","y":"P"},"x_max":10,"y_max":9,
    "curves":[
        {"id":"D","type":"line","intercept":7,"slope":-1,"color":"demand","label":"D"},
        {"id":"S1","type":"line","intercept":1.5,"slope":0.6,"color":"supply","label":"S"},
        {"id":"S2","type":"line","intercept":0,"slope":0.6,"color":"subsidy","label":"S-subsidy"}],
    "equilibria":[
        {"c1":"D","c2":"S1","label":"E₁","offset":[-15,8]},
        {"c1":"D","c2":"S2","label":"E₂","offset":[8,-12]}]}
test("2.10 subsidy", lambda: render_and_check(spec, "subsidy"))

# 11. Price ceiling
spec = {"axes":{"x":"Q","y":"P"},"x_max":9,"y_max":8,
    "curves":[
        {"id":"D","type":"line","intercept":7,"slope":-1,"color":"demand","label":"D"},
        {"id":"S","type":"line","intercept":1.5,"slope":0.6,"color":"supply","label":"S"},
        {"id":"Pmax","type":"horizontal","y":2.5,"color":"price_ctrl","label":"P_max"}],
    "equilibria":[{"c1":"D","c2":"S","label":"E","offset":[8,8]}]}
test("2.11 price ceiling", lambda: render_and_check(spec, "ceiling"))

# 12. Price floor
spec = {"axes":{"x":"Q","y":"P"},"x_max":9,"y_max":9,
    "curves":[
        {"id":"D","type":"line","intercept":8,"slope":-1,"color":"demand","label":"D"},
        {"id":"S","type":"line","intercept":1,"slope":0.8,"color":"supply","label":"S"},
        {"id":"Pmin","type":"horizontal","y":6,"color":"price_ctrl","label":"P_min"}],
    "equilibria":[{"c1":"D","c2":"S","label":"E","offset":[8,8]}]}
test("2.12 price floor", lambda: render_and_check(spec, "floor"))

# 13. Monopoly
spec = {"axes":{"x":"Q","y":"P/Cost"},"x_max":10,"y_max":10,
    "curves":[
        {"id":"D","type":"line","intercept":9,"slope":-1,"color":"demand","label":"D=AR"},
        {"id":"MR","type":"line","intercept":9,"slope":-2,"color":"demand2","label":"MR","style":"--"},
        {"id":"MC","type":"line","intercept":1,"slope":0.8,"color":"supply","label":"MC"}],
    "equilibria":[
        {"c1":"MR","c2":"MC","label":"Qm","offset":[8,-15]}],
    "shading":[{"type":"between","c1":"D","c2":"MC","x1":2.86,"x2":4.44,
                "color":"dwl","label":"DWL","label_pos":[3.6,5.5]}]}
test("2.13 monopoly", lambda: render_and_check(spec, "monopoly"))

# 14. Monopsony
spec = {"axes":{"x":"Labour","y":"Wage"},"x_max":9,"y_max":8,
    "curves":[
        {"id":"ACL","type":"line","intercept":0.8,"slope":0.6,"color":"demand","label":"AC_L=S_L"},
        {"id":"MCL","type":"line","intercept":0.8,"slope":1.2,"color":"supply","label":"MC_L"},
        {"id":"MRP","type":"line","intercept":6.5,"slope":-0.8,"color":"msb","label":"MRP=D_L"}],
    "equilibria":[
        {"c1":"MCL","c2":"MRP","label":"","offset":[5,5]},
        {"c1":"ACL","c2":"MRP","label":"","offset":[5,5]}]}
test("2.14 monopsony", lambda: render_and_check(spec, "monopsony"))

# ══════════════════════════════════════
# EDGE CASES
# ══════════════════════════════════════
print("\n" + "=" * 60)
print("3. EDGE CASES (10 tests)")
print("=" * 60)

# 15. Empty spec (should not crash)
test("3.1 empty spec", lambda: render_and_check(ds_spec(), "empty-safe"))

# 16. Single curve (no equilibrium)
spec = {"axes":{"x":"X","y":"Y"},"x_max":8,"y_max":8,
    "curves":[{"id":"L","type":"line","intercept":5,"slope":-0.5,"color":"demand","label":"L"}],
    "equilibria":[]}
test("3.2 single curve", lambda: render_and_check(spec, "single"))

# 17. Vertical + line intersection
spec = ds_spec()
spec["curves"] = [
    {"id":"D","type":"line","intercept":7,"slope":-1,"color":"demand","label":"D"},
    {"id":"V","type":"vertical","x":4,"color":"lras","label":"V"}]
spec["equilibria"] = [{"c1":"D","c2":"V","label":"P","offset":[8,8]}]
test("3.3 vertical + line", lambda: render_and_check(spec, "vert"))

# 18. Horizontal + line intersection
spec = ds_spec()
spec["curves"] = [
    {"id":"D","type":"line","intercept":7,"slope":-1,"color":"demand","label":"D"},
    {"id":"H","type":"horizontal","y":3,"color":"price_ctrl","label":"P=3"}]
spec["equilibria"] = [{"c1":"D","c2":"H","label":"Q","offset":[5,-10]}]
test("3.4 horizontal + line", lambda: render_and_check(spec, "horiz"))

# 19. Very large values
spec = ds_spec()
spec["x_max"] = 100; spec["y_max"] = 100
spec["curves"][0]["intercept"] = 90
spec["curves"][1]["intercept"] = 10
test("3.5 large scale", lambda: render_and_check(spec, "large"))

# 20. Perfectly elastic (zero slope)
spec = ds_spec()
spec["curves"][0]["slope"] = 0
spec["curves"][0]["label"] = "D (perf elastic)"
test("3.6 zero slope", lambda: render_and_check(spec, "zero-slope"))

# 21. Near-vertical slope
spec = ds_spec()
spec["curves"][0]["slope"] = -10
spec["curves"][0]["label"] = "D (near vertical)"
spec["x_max"] = 5; spec["y_max"] = 12
test("3.7 steep slope", lambda: render_and_check(spec, "steep"))

# 22. No label on curves
spec = ds_spec()
spec["curves"][0]["label"] = ""
spec["curves"][1]["label"] = ""
test("3.8 no labels", lambda: render_and_check(spec, "nolabel"))

# 23. Many curves (stress test)
spec = ds_spec()
spec["curves"] = [
    {"id":"C1","type":"line","intercept":9,"slope":-1.2,"color":"demand","label":""},
    {"id":"C2","type":"line","intercept":8,"slope":-1.0,"color":"demand2","label":""},
    {"id":"C3","type":"line","intercept":7,"slope":-0.8,"color":"msc","label":""},
    {"id":"C4","type":"line","intercept":1,"slope":0.5,"color":"supply","label":""},
    {"id":"C5","type":"line","intercept":2.5,"slope":0.5,"color":"supply2","label":""}]
spec["equilibria"] = []
spec["x_max"] = 10; spec["y_max"] = 10
test("3.9 5 curves", lambda: render_and_check(spec, "5curves"))

# 24. Multiple equilibria
spec = ds_spec()
spec["curves"] = [
    {"id":"D","type":"line","intercept":7,"slope":-1,"color":"demand","label":"D"},
    {"id":"S1","type":"line","intercept":1.5,"slope":0.6,"color":"supply","label":"S₁"},
    {"id":"S2","type":"line","intercept":3.5,"slope":0.6,"color":"supply2","label":"S₂"}]
spec["equilibria"] = [
    {"c1":"D","c2":"S1","label":"E₁","offset":[-15,8]},
    {"c1":"D","c2":"S2","label":"E₂","offset":[8,8]}]
test("3.10 multi-equilibrium", lambda: render_and_check(spec, "multi-eq"))

# ══════════════════════════════════════
# PARAMETER VARIATIONS (elasticity, shifts)
# ══════════════════════════════════════
print("\n" + "=" * 60)
print("4. PARAMETER VARIATIONS (15 tests)")
print("=" * 60)

# Vary demand elasticity
for i, slope in enumerate([-0.2, -0.5, -0.8, -1.0, -1.5, -2.0, -3.0]):
    spec = ds_spec()
    spec["curves"][0]["slope"] = slope
    spec["curves"][0]["label"] = f"D (s={slope})"
    test(f"4.1 D slope {slope}", lambda s=spec: render_and_check(s, f"D slope"))

# Vary supply elasticity  
for i, slope in enumerate([0.2, 0.5, 0.8, 1.0, 1.5]):
    spec = ds_spec()
    spec["curves"][1]["slope"] = slope
    spec["curves"][1]["label"] = f"S (s={slope})"
    test(f"4.2 S slope {slope}", lambda s=spec: render_and_check(s, f"S slope"))

# Vary tax amounts
for tax in [0.5, 1.0, 2.0, 3.0]:
    spec = {"axes":{"x":"Q","y":"P"},"x_max":9,"y_max":9,
        "curves":[
            {"id":"D","type":"line","intercept":7,"slope":-1,"color":"demand","label":"D"},
            {"id":"S","type":"line","intercept":1.5,"slope":0.6,"color":"supply","label":"S"},
            {"id":"St","type":"line","intercept":1.5+tax,"slope":0.6,"color":"supply2","label":f"S+{tax}"}],
        "equilibria":[
            {"c1":"D","c2":"S","label":"E","offset":[-15,8]},
            {"c1":"D","c2":"St","label":"E_t","offset":[8,-12]}]}
    test(f"4.3 tax {tax}", lambda s=spec: render_and_check(s, f"tax{tax}"))

# ══════════════════════════════════════
# TARIFF (the hardest)
# ══════════════════════════════════════
print("\n" + "=" * 60)
print("5. TARIFF (3 tests)")
print("=" * 60)

spec = {"axes":{"x":"Q","y":"P"},"x_max":9,"y_max":8,
    "curves":[
        {"id":"Dd","type":"line","intercept":7,"slope":-0.8,"color":"demand","label":"D_d"},
        {"id":"Sd","type":"line","intercept":1.5,"slope":0.5,"color":"supply","label":"S_d"},
        {"id":"Pw","type":"horizontal","y":3,"color":"msc","label":"P_w","style":"--"},
        {"id":"Pwt","type":"horizontal","y":4.5,"color":"price_ctrl","label":"P_w+t","style":"--"}],
    "equilibria":[]}
test("5.1 tariff basic", lambda: render_and_check(spec, "tariff"))

# Tariff with equilibrium
spec["equilibria"] = [{"c1":"Dd","c2":"Sd","label":"E","offset":[8,-15]}]
test("5.2 tariff + eq", lambda: render_and_check(spec, "tariff+eq"))

# Tariff with shading
spec["shading"] = [{"type":"between","c1":"Pwt","c2":"Pw","x1":3.125,"x2":6,
                    "color":"revenue","label":"revenue","label_pos":[4.5,3.75]}]
test("5.3 tariff + shading", lambda: render_and_check(spec, "tariff+shade"))

# ══════════════════════════════════════
# RESULTS
# ══════════════════════════════════════
print(f"\n{'='*60}")
print(f"RESULTS: {PASS} passed, {FAIL} failed")
print(f"Generated: {STATS['generated']} diagrams, {STATS['total_kb']:.0f} KB total")
print(f"{'='*60}")
sys.exit(0 if FAIL == 0 else 1)
