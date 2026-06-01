"""
Economic diagram spec builder — LLM describes type + params, Python computes exact math.

Ensures correct mathematical relationships:
  - MR slope = 2 × AR slope (monopoly)
  - MSC intercept = MPC intercept + external_cost (externality) 
  - S+tax intercept = S intercept + tax_amount (tax)
  - MCL slope = 2 × ACL slope (monopsony, linear supply)
  - All intersections solved mathematically

LLM input:  {"type": "monopoly", "D_intercept": 9}
Output:    Full renderable spec with exact curve parameters
"""
from typing import Optional, Dict, Any

def build_demand_supply(elasticity: str = "normal",
                         shift: Optional[str] = None,
                         shift_amount: float = 0) -> Dict[str, Any]:
    """D slopes mapped to elasticity levels."""
    D_slope = {"elastic": -0.3, "normal": -1.0, "inelastic": -1.5}.get(elasticity, -1.0)
    D_intercept = 7
    S_intercept = 1.5
    S_slope = 0.6

    curves = [
        {"id": "D", "type": "line", "intercept": D_intercept, "slope": D_slope,
         "color": "demand", "label": "D"},
        {"id": "S", "type": "line", "intercept": S_intercept, "slope": S_slope,
         "color": "supply", "label": "S"},
    ]
    equilibria = [{"c1": "D", "c2": "S", "label": "E", "offset": (12, 12)}]

    if shift == "demand_right":
        curves.append({"id": "D2", "type": "line", "intercept": D_intercept + shift_amount,
                       "slope": D_slope, "color": "demand2", "label": "D₂"})
        equilibria = [
            {"c1": "D", "c2": "S", "label": "E₁", "offset": (-12, 10)},
            {"c1": "D2", "c2": "S", "label": "E₂", "offset": (12, 10)},
        ]
    elif shift == "supply_left":
        curves.append({"id": "S2", "type": "line", "intercept": S_intercept + shift_amount,
                       "slope": S_slope, "color": "supply2", "label": "S₂"})
        equilibria = [
            {"c1": "D", "c2": "S", "label": "E₁", "offset": (10, -12)},
            {"c1": "D", "c2": "S2", "label": "E₂", "offset": (10, 10)},
        ]

    return {"axes": {"x": "Quantity", "y": "Price"}, "x_max": 9, "y_max": 9,
            "curves": curves, "equilibria": equilibria}


def build_externality(external_cost: float = 1.5,
                       externality_type: str = "negative_production") -> Dict[str, Any]:
    """MSC = MPC + external_cost (same slope)."""
    if "negative" in externality_type:
        MPC_intercept = 1.5
        MPC_slope = 0.6
        MSC_intercept = MPC_intercept + external_cost
        MSC_slope = MPC_slope
        D_intercept = 7
        D_slope = -1.0

        curves = [
            {"id": "D", "type": "line", "intercept": D_intercept, "slope": D_slope,
             "color": "demand", "label": "D=MPB"},
            {"id": "MPC", "type": "line", "intercept": MPC_intercept, "slope": MPC_slope,
             "color": "supply", "label": "MPC=S"},
            {"id": "MSC", "type": "line", "intercept": MSC_intercept, "slope": MSC_slope,
             "color": "msc", "label": "MSC"},
        ]
        equilibria = [
            {"c1": "D", "c2": "MPC", "label": "Eₚ", "offset": (8, -12)},
            {"c1": "D", "c2": "MSC", "label": "Eₛ", "offset": (8, 10)},
        ]
        # DWL: shade between MSC and MPC, from Q_social to Q_private
        shading = [{
            "upper": "MSC", "lower": "MPC",
            "left_eq": "Eₛ", "right_eq": "Eₚ",
            "color": "dwl", "alpha": 0.25,
            "label": "DWL", "label_pos": (3.2, 4.3)
        }]
        return {"axes": {"x": "Quantity", "y": "Cost/Benefit"}, "x_max": 8, "y_max": 8,
                "curves": curves, "equilibria": equilibria, "shading": shading}


def build_ad_as(gap: str = "recessionary", lras_x: float = 5.5) -> Dict[str, Any]:
    """AD, SRAS, LRAS with output gap. AD intercept ensures intersection at sensible point."""
    if gap == "recessionary":
        AD_intercept = 7.0  # Lower → intersection to left of LRAS
    else:
        AD_intercept = 8.5  # Higher → intersection to right of LRAS

    curves = [
        {"id": "AD", "type": "line", "intercept": AD_intercept, "slope": -0.9,
         "color": "ad", "label": "AD"},
        {"id": "SRAS", "type": "line", "intercept": 2.0, "slope": 0.5,
         "color": "sras", "label": "SRAS"},
        {"id": "LRAS", "type": "vertical", "x": lras_x,
         "color": "lras", "label": "LRAS"},
    ]
    return {"axes": {"x": "Real GDP", "y": "Price Level"}, "x_max": 10, "y_max": 8,
            "curves": curves, "equilibria": [
                {"c1": "AD", "c2": "SRAS", "label": "E", "offset": (12, 12)}]}


def build_ad_shift(direction: str = "right", amount: float = 1.2,
                    lras_x: float = 5.5) -> Dict[str, Any]:
    """AD shift (expansionary/contractionary)."""
    AD1_intercept = 7.0
    if direction == "right":
        AD2_intercept = AD1_intercept + amount
    else:
        AD2_intercept = AD1_intercept - amount

    curves = [
        {"id": "AD1", "type": "line", "intercept": AD1_intercept, "slope": -0.9,
         "color": "ad", "label": "AD₁"},
        {"id": "AD2", "type": "line", "intercept": AD2_intercept, "slope": -0.9,
         "color": "demand2", "label": "AD₂"},
        {"id": "SRAS", "type": "line", "intercept": 2.0, "slope": 0.5,
         "color": "sras", "label": "SRAS"},
        {"id": "LRAS", "type": "vertical", "x": lras_x,
         "color": "lras", "label": "LRAS"},
    ]
    return {"axes": {"x": "Real GDP", "y": "Price Level"}, "x_max": 10, "y_max": 8,
            "curves": curves, "equilibria": [
                {"c1": "AD1", "c2": "SRAS", "label": "E₁", "offset": (-12, 10)},
                {"c1": "AD2", "c2": "SRAS", "label": "E₂", "offset": (12, 10)}]}


def build_monopoly(D_intercept: float = 9.0, MC_slope: float = 0.8) -> Dict[str, Any]:
    """MR slope = 2 × AR slope (linear demand)."""
    AR_intercept = D_intercept
    AR_slope = -1.0
    MR_intercept = AR_intercept       # Same intercept as AR
    MR_slope = 2 * AR_slope           # = -2.0 ← CRITICAL

    curves = [
        {"id": "AR", "type": "line", "intercept": AR_intercept, "slope": AR_slope,
         "color": "demand", "label": "D=AR"},
        {"id": "MR", "type": "line", "intercept": MR_intercept, "slope": MR_slope,
         "color": "demand2", "label": "MR", "style": "--"},
        {"id": "MC", "type": "line", "intercept": 1.0, "slope": MC_slope,
         "color": "supply", "label": "MC"},
    ]
    # MR=MC intersection
    return {"axes": {"x": "Quantity", "y": "Price/Cost"}, "x_max": 10, "y_max": 10,
            "curves": curves, "equilibria": [
                {"c1": "MR", "c2": "MC", "label": "MC=MR", "offset": (10, -15)},
                {"c1": "AR", "c2": "MC", "label": "P=MC", "offset": (10, 10)}],
            "shading": [
                {"upper": "AR", "lower": "MC",
                 "left_eq": "MC=MR", "right_eq": "P=MC",
                 "color": "dwl", "alpha": 0.2,
                 "label": "DWL", "label_pos": (3.8, 5.5)}]}


def build_tax(tax_amount: float = 1.5) -> Dict[str, Any]:
    """S+tax = S shifted UP by tax_amount (same slope)."""
    S_intercept = 1.5
    S_slope = 0.6
    St_intercept = S_intercept + tax_amount  # ← CRITICAL

    curves = [
        {"id": "D", "type": "line", "intercept": 7.0, "slope": -1.0,
         "color": "demand", "label": "D"},
        {"id": "S", "type": "line", "intercept": S_intercept, "slope": S_slope,
         "color": "supply", "label": "S"},
        {"id": "St", "type": "line", "intercept": St_intercept, "slope": S_slope,
         "color": "supply2", "label": "S+tax"},
    ]
    return {"axes": {"x": "Quantity", "y": "Price"}, "x_max": 9, "y_max": 9,
            "curves": curves, "equilibria": [
                {"c1": "D", "c2": "S", "label": "E", "offset": (-12, 10)},
                {"c1": "D", "c2": "St", "label": "E_t", "offset": (10, -12)}],
            "shading": [
                {"upper": "D", "lower": "S", "left_eq": "E_t", "right_eq": "E",
                 "color": "dwl", "alpha": 0.2, "label": "DWL", "label_pos": (4.2, 5.2)}]}


def build_subsidy(subsidy_amount: float = 2.0) -> Dict[str, Any]:
    """S-subsidy = S shifted DOWN by subsidy_amount (same slope)."""
    S_intercept = 1.5
    S_slope = 0.6
    Ss_intercept = S_intercept - subsidy_amount  # ← CRITICAL

    curves = [
        {"id": "D", "type": "line", "intercept": 7.0, "slope": -1.0,
         "color": "demand", "label": "D"},
        {"id": "S1", "type": "line", "intercept": S_intercept, "slope": S_slope,
         "color": "supply", "label": "S"},
        {"id": "S2", "type": "line", "intercept": Ss_intercept, "slope": S_slope,
         "color": "subsidy", "label": "S-subsidy"},
    ]
    return {"axes": {"x": "Quantity", "y": "Price"}, "x_max": 10, "y_max": 9,
            "curves": curves, "equilibria": [
                {"c1": "D", "c2": "S1", "label": "E₁", "offset": (-12, 10)},
                {"c1": "D", "c2": "S2", "label": "E₂", "offset": (10, -12)}]}


def build_price_control(control_type: str = "ceiling", price: float = 2.5) -> Dict[str, Any]:
    """Price ceiling (below eq) or floor (above eq)."""
    curves = [
        {"id": "D", "type": "line", "intercept": 7.0, "slope": -1.0,
         "color": "demand", "label": "D"},
        {"id": "S", "type": "line", "intercept": 1.5, "slope": 0.6,
         "color": "supply", "label": "S"},
        {"id": "Pctrl", "type": "horizontal", "y": price,
         "color": "price_ctrl", "label": f"P_{'max' if control_type=='ceiling' else 'min'}",
         "style": "--"},
    ]
    return {"axes": {"x": "Quantity", "y": "Price"}, "x_max": 9, "y_max": 9,
            "curves": curves, "equilibria": [
                {"c1": "D", "c2": "S", "label": "E", "offset": (10, 10)}]}


def build_monopsony() -> Dict[str, Any]:
    """MCL slope = 2 × ACL slope (linear labour supply)."""
    ACL_intercept = 0.8
    ACL_slope = 0.6
    MCL_intercept = ACL_intercept       # Same intercept
    MCL_slope = 2 * ACL_slope            # = 1.2 ← CRITICAL

    curves = [
        {"id": "ACL", "type": "line", "intercept": ACL_intercept, "slope": ACL_slope,
         "color": "demand", "label": "AC_L=S_L"},
        {"id": "MCL", "type": "line", "intercept": MCL_intercept, "slope": MCL_slope,
         "color": "supply", "label": "MC_L"},
        {"id": "MRP", "type": "line", "intercept": 6.5, "slope": -0.8,
         "color": "msb", "label": "MRP=D_L"},
    ]
    return {"axes": {"x": "Labour", "y": "Wage"}, "x_max": 9, "y_max": 8,
            "curves": curves, "equilibria": [
                {"c1": "MCL", "c2": "MRP", "label": "", "offset": (5, 5)},
                {"c1": "ACL", "c2": "MRP", "label": "", "offset": (5, 5)}]}


def build_tariff(pw: float = 3.0, tariff_amount: float = 1.5) -> Dict[str, Any]:
    """World price + tariff."""
    curves = [
        {"id": "Dd", "type": "line", "intercept": 7.0, "slope": -0.8,
         "color": "demand", "label": "D_d"},
        {"id": "Sd", "type": "line", "intercept": 1.5, "slope": 0.5,
         "color": "supply", "label": "S_d"},
        {"id": "Pw", "type": "horizontal", "y": pw,
         "color": "msc", "label": "P_w", "style": "--"},
        {"id": "Pwt", "type": "horizontal", "y": pw + tariff_amount,
         "color": "price_ctrl", "label": "P_w+t", "style": "--"},
    ]
    return {"axes": {"x": "Quantity", "y": "Price"}, "x_max": 9, "y_max": 8,
            "curves": curves, "equilibria": [
                {"c1": "Dd", "c2": "Sd", "label": "E", "offset": (10, -15)}]}


def build_ppc() -> Dict[str, Any]:
    """Concave PPC using quadratic."""
    return {"axes": {"x": "Capital Goods", "y": "Consumer Goods"}, "x_max": 10, "y_max": 10,
            "curves": [
                {"id": "PPC1", "type": "line", "intercept": 8.0, "slope": -1.2,
                 "color": "demand", "label": "PPC"},
            ], "equilibria": []}


def build_keynesian_lras() -> Dict[str, Any]:
    """Three-phase LRAS."""
    return {"axes": {"x": "Real GDP", "y": "Price Level"}, "x_max": 10, "y_max": 8,
            "curves": [
                {"id": "AD", "type": "line", "intercept": 6.5, "slope": -0.7,
                 "color": "ad", "label": "AD"},
                {"id": "LRAS_seg1", "type": "horizontal", "y": 2.0,
                 "color": "lras", "label": "", "style": "-"},
                {"id": "LRAS_seg3", "type": "vertical", "x": 8.0,
                 "color": "lras", "label": "LRAS"},
            ], "equilibria": [
                {"c1": "AD", "c2": "LRAS_seg1", "label": "E", "offset": (10, 10)}]}


# ── Builder registry ──

BUILDERS = {
    "demand_supply": build_demand_supply,
    "demand_shift": lambda **kw: build_demand_supply(shift="demand_right", **kw),
    "supply_shift": lambda **kw: build_demand_supply(shift="supply_left", **kw),
    "externality": build_externality,
    "ad_as": build_ad_as,
    "ad_shift": build_ad_shift,
    "monopoly": build_monopoly,
    "tax": build_tax,
    "subsidy": build_subsidy,
    "price_ceiling": lambda **kw: build_price_control(control_type="ceiling", **kw),
    "price_floor": lambda **kw: build_price_control(control_type="floor", **kw),
    "monopsony": build_monopsony,
    "tariff": build_tariff,
    "ppc": build_ppc,
    "keynesian_lras": build_keynesian_lras,
}

def build_spec(params: dict) -> Optional[dict]:
    """Parse LLM params and build a correct spec."""
    ptype = params.get("type", "")
    builder = BUILDERS.get(ptype)
    if not builder:
        return None
    # Extract known params, ignore unknown
    kw = {k: v for k, v in params.items() if k != "type"}
    return builder(**kw)
