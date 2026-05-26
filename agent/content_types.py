"""
Content Type Registry — Complete catalog of ALL visual/textual content types
found in Cambridge A-Level papers, mark schemes, and textbooks across 4 subjects.

Based on analysis of actual past papers from 2019-2022 across all subjects.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict


class ContentCategory(Enum):
    TEXT = "text"                         # Plain text, paragraphs
    FORMULA = "formula"                   # Mathematical/chemical formula
    STRUCTURAL_FORMULA = "structural_formula"  # Displayed chemical structures
    CHEMICAL_EQUATION = "chemical_equation"    # Reaction equations with arrows
    REACTION_MECHANISM = "reaction_mechanism"  # Curly arrow mechanisms
    TABLE = "table"                       # Data tables (grid format)
    GRAPH = "graph"                       # Coordinate graphs with axes
    DIAGRAM = "diagram"                   # Schematic diagrams
    CIRCUIT = "circuit"                   # Electrical circuit diagrams
    SPECTRUM = "spectrum"                 # Spectroscopy charts (IR, NMR, MS)
    MOLECULE_3D = "molecule_3d"          # 3D molecular geometry drawings
    FORCE_DIAGRAM = "force_diagram"       # Free-body / force diagrams
    WAVE_DIAGRAM = "wave_diagram"         # Wave interference/diffraction
    ENERGY_CYCLE = "energy_cycle"         # Born-Haber, Hess cycles
    ECONOMIC_GRAPH = "economic_graph"     # Demand/supply, AD/AS etc
    DATA_TABLE = "data_table"             # Economics data tables
    STATISTICAL_TABLE = "statistical_table"  # Z-table, t-table, binomial
    HANDWRITING = "handwriting"           # Student handwritten answers
    PHOTO = "photo"                       # Real photograph (apparatus, etc)
    MARKING_ANNOTATION = "marking_annotation"  # MS annotations on answers


# ============================================================
# PER-SUBJECT CONTENT TYPE MAP
# All types confirmed from actual paper analysis
# ============================================================

SUBJECT_CONTENT_TYPES: Dict[str, List[Dict]] = {
    "9701": [  # Chemistry
        {
            "id": "chem_chemical_equation",
            "name": "化学方程式",
            "category": ContentCategory.CHEMICAL_EQUATION,
            "description": "Reaction equations with →, ⇌, state symbols (s/l/g/aq), stoichiometric coefficients",
            "examples": ["2H₂ + O₂ → 2H₂O", "N₂ + 3H₂ ⇌ 2NH₃", "CH₃COOH ⇌ CH₃COO⁻ + H⁺"],
            "paper_location": "All papers, especially P2/P4 structured questions",
            "ocr_strategy": "PaddleOCR text + LLM chemical formula parsing → structured JSON",
            "output_format": "LaTeX: \\ce{2H2 + O2 -> 2H2O}",
            "priority": "P0",
        },
        {
            "id": "chem_structural_formula",
            "name": "结构式/骨架式",
            "category": ContentCategory.STRUCTURAL_FORMULA,
            "description": "Displayed/skeletal formulas of organic molecules: benzene rings, functional groups, isomers",
            "examples": ["Benzene ring", "CH₃CH₂OH displayed", "Skeletal formula of aspirin"],
            "paper_location": "P2/P4 organic chemistry questions",
            "ocr_strategy": "DECIMER → SMILES + PaddleOCR for labels + Qwen3-VL for complex structures",
            "output_format": "SMILES + LaTeX chemfig",
            "priority": "P0",
        },
        {
            "id": "chem_reaction_mechanism",
            "name": "反应机理（卷曲箭头）",
            "category": ContentCategory.REACTION_MECHANISM,
            "description": "Organic reaction mechanisms with curly arrows, intermediates, transition states",
            "examples": ["SN1/SN2 mechanisms", "Electrophilic addition to C=C", "Nucleophilic substitution"],
            "paper_location": "P2/P4 organic questions, typically 4-6 marks",
            "ocr_strategy": "Qwen3-VL semantic understanding + preserve original image. NO auto-extraction of arrows. Mark for human review.",
            "output_format": "JSON {mechanism_type, steps[], original_image_ref}",
            "priority": "P0",
            "note": "⚠️ No tool can auto-extract curly arrows. Best approach: VLM describes + keep image."
        },
        {
            "id": "chem_energy_cycle",
            "name": "能量循环图",
            "category": ContentCategory.ENERGY_CYCLE,
            "description": "Born-Haber cycles, Hess's law cycles, enthalpy level diagrams",
            "examples": ["Born-Haber for NaCl", "Hess cycle with ΔH arrows", "Energy profile diagrams"],
            "paper_location": "P2/P4 thermodynamics questions",
            "ocr_strategy": "Qwen3-VL diagram understanding + PaddleOCR for labels",
            "output_format": "JSON {cycle_type, steps[], values{}}",
            "priority": "P0",
        },
        {
            "id": "chem_molecular_geometry",
            "name": "分子空间构型",
            "category": ContentCategory.MOLECULE_3D,
            "description": "3D representations: wedges/dashes, VSEPR shapes, bond angles",
            "examples": ["Tetrahedral CH₄ 109.5°", "Trigonal planar BF₃ 120°", "Octahedral SF₆ 90°"],
            "paper_location": "P2 chemical bonding questions",
            "ocr_strategy": "Qwen3-VL shape recognition + text for labels",
            "output_format": "JSON {shape, bond_angle, hybridization}",
            "priority": "P0",
        },
        {
            "id": "chem_spectrum",
            "name": "光谱图",
            "category": ContentCategory.SPECTRUM,
            "description": "IR spectra, NMR spectra, mass spectra, chromatograms",
            "examples": ["IR spectrum with peaks", "¹H NMR with splitting", "Mass spectrum with m/z"],
            "paper_location": "P2/P4 analytical chemistry questions",
            "ocr_strategy": "Qwen3-VL peak identification + numerical extraction",
            "output_format": "JSON {spectrum_type, peaks[{mz_or_wavenumber, intensity, assignment}]}",
            "priority": "P1",
        },
        {
            "id": "chem_data_graph",
            "name": "实验数据图表",
            "category": ContentCategory.GRAPH,
            "description": "Rate graphs, titration curves, pH curves, Maxwell-Boltzmann distributions",
            "examples": ["Concentration vs time", "pH titration curve", "Boltzmann distribution"],
            "paper_location": "P2/P4 kinetics, equilibria, acid-base questions",
            "ocr_strategy": "Qwen3-VL semantic + optional WebPlotDigitizer numerical",
            "output_format": "JSON {graph_type, axes_labels, trend_description}",
            "priority": "P1",
        },
        {
            "id": "chem_practical_table",
            "name": "实验数据表格",
            "category": ContentCategory.TABLE,
            "description": "Measurement tables for titrations, enthalpy, kinetics experiments",
            "examples": ["Titration results table", "Temperature vs time table"],
            "paper_location": "P3/P5 practical questions",
            "ocr_strategy": "PaddleOCR PP-StructureV3 table extraction",
            "output_format": "JSON/markdown table",
            "priority": "P0",
        },
    ],

    "9702": [  # Physics
        {
            "id": "phys_circuit_diagram",
            "name": "电路图",
            "category": ContentCategory.CIRCUIT,
            "description": "Electrical circuit schematics with standard symbols: battery, resistor, capacitor, diode, switch, ammeter, voltmeter",
            "examples": ["Series/parallel circuits", "Potential divider", "Wheatstone bridge"],
            "paper_location": "P2/P4 electricity questions",
            "ocr_strategy": "Qwen3-VL circuit analysis + PaddleOCR for labels/values",
            "output_format": "JSON {components[{type, value, connections}], netlist}",
            "priority": "P0",
        },
        {
            "id": "phys_force_diagram",
            "name": "受力分析图",
            "category": ContentCategory.FORCE_DIAGRAM,
            "description": "Free-body diagrams, force resolution, inclined planes, pulleys, connected masses",
            "examples": ["Block on incline", "Two masses over pulley", "Car rounding curve"],
            "paper_location": "P2/P4 mechanics questions",
            "ocr_strategy": "Qwen3-VL describe forces + PaddleOCR for labels",
            "output_format": "JSON {object, forces[{name, direction, magnitude?}], coordinate_system}",
            "priority": "P0",
        },
        {
            "id": "phys_wave_diagram",
            "name": "波动物理图",
            "category": ContentCategory.WAVE_DIAGRAM,
            "description": "Wave interference patterns, standing waves, diffraction patterns, Young's double slit, polarization",
            "examples": ["Two-source interference", "Standing wave on string", "Diffraction grating pattern"],
            "paper_location": "P2/P4 waves and superposition questions",
            "ocr_strategy": "Qwen3-VL wave description + numerical values from PaddleOCR",
            "output_format": "JSON {wave_type, parameters{wavelength, amplitude, frequency?}}",
            "priority": "P1",
        },
        {
            "id": "phys_data_graph",
            "name": "实验数据图",
            "category": ContentCategory.GRAPH,
            "description": "I-V characteristics, discharge curves, resonance curves, stress-strain, force-extension",
            "examples": ["I-V diode graph", "Capacitor discharge", "Spring force-extension"],
            "paper_location": "All papers, especially P2/P4/P5",
            "ocr_strategy": "Qwen3-VL graph understanding + optional WebPlotDigitizer",
            "output_format": "JSON {axes{x_label, y_label, units}, trend, key_points}",
            "priority": "P0",
        },
        {
            "id": "phys_field_diagram",
            "name": "场线图",
            "category": ContentCategory.DIAGRAM,
            "description": "Electric/magnetic/gravitational field lines, flux diagrams, solenoid fields",
            "examples": ["Electric field between plates", "Magnetic field around solenoid", "Flux linkage"],
            "paper_location": "P4 fields questions",
            "ocr_strategy": "Qwen3-VL field pattern description",
            "output_format": "JSON {field_type, pattern_description}",
            "priority": "P1",
        },
        {
            "id": "phys_experimental_setup",
            "name": "实验装置图",
            "category": ContentCategory.DIAGRAM,
            "description": "Apparatus diagrams: oscilloscopes, signal generators, light gates, interferometers",
            "examples": ["Young's double slit setup", "Terminal velocity apparatus", "Magnetic field measurement"],
            "paper_location": "P3/P5 practical questions",
            "ocr_strategy": "Qwen3-VL equipment identification + PaddleOCR for labels",
            "output_format": "JSON {equipment[{name, purpose}], measurement_method}",
            "priority": "P1",
        },
        {
            "id": "phys_graph_analysis_table",
            "name": "数据处理表格",
            "category": ContentCategory.TABLE,
            "description": "Results tables with uncertainties, log tables, processed data",
            "examples": ["Raw data + calculated values", "ln/linearized data tables"],
            "paper_location": "P3/P5 practical + P2/P4 data questions",
            "ocr_strategy": "PaddleOCR PP-StructureV3 table",
            "output_format": "Markdown/JSON table with uncertainties",
            "priority": "P0",
        },
    ],

    "9708": [  # Economics
        {
            "id": "econ_demand_supply",
            "name": "供需曲线图",
            "category": ContentCategory.ECONOMIC_GRAPH,
            "description": "Demand and supply curves, shifts, equilibrium price/quantity changes",
            "examples": ["Market equilibrium with tax", "Shift in demand curve", "Price floor/ceiling"],
            "paper_location": "All papers; core tool of 9708",
            "ocr_strategy": "Qwen3-VL diagram interpretation + PaddleOCR for axis labels",
            "output_format": "JSON {diagram_type, curves[{name, direction, shift?}], equilibrium}",
            "priority": "P0",
        },
        {
            "id": "econ_elasticity",
            "name": "弹性图",
            "category": ContentCategory.ECONOMIC_GRAPH,
            "description": "PED/PES/YED/XED diagrams showing different elasticity values on demand/supply curves",
            "examples": ["Perfectly elastic demand", "Inelastic supply", "Tax incidence with elastic demand"],
            "paper_location": "P2 data response, P4 essays",
            "ocr_strategy": "Qwen3-VL elasticity type identification",
            "output_format": "JSON {elasticity_type, value_range, tax_burden?}",
            "priority": "P1",
        },
        {
            "id": "econ_ad_as",
            "name": "AD-AS 宏观图",
            "category": ContentCategory.ECONOMIC_GRAPH,
            "description": "Aggregate demand/supply diagrams, LRAS/SRAS shifts, output gaps",
            "examples": ["AD increase → inflation", "LRAS shift right → growth", "Negative output gap"],
            "paper_location": "P2/P4 macroeconomics",
            "ocr_strategy": "Qwen3-VL macro diagram interpretation",
            "output_format": "JSON {axes{AD, price_level, real_GDP}, shifts[], outcome}",
            "priority": "P0",
        },
        {
            "id": "econ_externality",
            "name": "外部性图",
            "category": ContentCategory.ECONOMIC_GRAPH,
            "description": "MSC/MSB/MPC/MPB diagrams, deadweight loss triangles, Pigouvian tax/subsidy",
            "examples": ["Negative production externality", "Positive consumption externality", "Optimal tax"],
            "paper_location": "P2/P4 market failure",
            "ocr_strategy": "Qwen3-VL externality identification + DWL triangle recognition",
            "output_format": "JSON {externality_type, social_optimum, market_equilibrium, dwl}",
            "priority": "P1",
        },
        {
            "id": "econ_macro_other",
            "name": "其他宏观图",
            "category": ContentCategory.ECONOMIC_GRAPH,
            "description": "Phillips curve, Lorenz curve, Laffer curve, J-curve, Kuznets curve, business cycle",
            "examples": ["Short-run Phillips curve", "Lorenz curve for income inequality", "J-curve after depreciation"],
            "paper_location": "P4 macro sections",
            "ocr_strategy": "Qwen3-VL curve type identification",
            "output_format": "JSON {curve_type, axes_labels, interpretation}",
            "priority": "P1",
        },
        {
            "id": "econ_ppc",
            "name": "生产可能性曲线",
            "category": ContentCategory.ECONOMIC_GRAPH,
            "description": "PPC/PPF diagrams showing opportunity cost, economic growth, efficiency",
            "examples": ["PPC with outward shift", "Point inside/on/outside PPC"],
            "paper_location": "P1/P2 basic economic ideas",
            "ocr_strategy": "Qwen3-VL PPC interpretation",
            "output_format": "JSON {axes{g1, g2}, point_location, efficiency}",
            "priority": "P1",
        },
        {
            "id": "econ_data_table",
            "name": "经济数据表格",
            "category": ContentCategory.DATA_TABLE,
            "description": "GDP, inflation, unemployment, trade data tables, balance of payments",
            "examples": ["GDP growth rates by country", "CPI inflation table", "Current account data"],
            "paper_location": "P2 data response (extract)",
            "ocr_strategy": "PaddleOCR PP-StructureV3 table + LLM data interpretation",
            "output_format": "JSON/CSV with column headers and values",
            "priority": "P0",
        },
        {
            "id": "econ_written_data",
            "name": "文字资料/Extract",
            "category": ContentCategory.TEXT,
            "description": "Long text extracts providing economic context for data response questions",
            "examples": ["News article about inflation", "IMF country report excerpt"],
            "paper_location": "P2/P3 data response/case study",
            "ocr_strategy": "PaddleOCR text (pure text, no special handling needed)",
            "output_format": "Plain text",
            "priority": "P0",
        },
    ],

    "9709": [  # Mathematics
        {
            "id": "math_formula_block",
            "name": "数学公式",
            "category": ContentCategory.FORMULA,
            "description": "Mathematical expressions: integrals, derivatives, trig, vectors, series notation, algebraic fractions",
            "examples": ["∫₀¹ x² dx", "d/dx(sin x)", "Σ(r=1 to n) r²", "a·b = |a||b|cosθ"],
            "paper_location": "All papers; core math content",
            "ocr_strategy": "Surya LaTeX OCR for formula blocks + PaddleOCR for inline math text",
            "output_format": "LaTeX",
            "priority": "P0",
        },
        {
            "id": "math_coordinate_graph",
            "name": "坐标几何图",
            "category": ContentCategory.GRAPH,
            "description": "Coordinate geometry diagrams: circles, lines, parabolas, tangents, normals",
            "examples": ["Circle with tangent line", "Parabola with axis of symmetry", "Intersection of curves"],
            "paper_location": "P1/P3 pure mathematics",
            "ocr_strategy": "Qwen3-VL graph description + PaddleOCR for labeled points",
            "output_format": "JSON {geometric_objects[{type, equation?}], intersections}",
            "priority": "P0",
        },
        {
            "id": "math_trigonometric_graph",
            "name": "三角函数图",
            "category": ContentCategory.GRAPH,
            "description": "Graphs of sin, cos, tan and transformations: amplitude, period, phase shift",
            "examples": ["y = 2sin(3x - π/4)", "cos graph with amplitude change"],
            "paper_location": "P1/P3 trigonometry",
            "ocr_strategy": "Qwen3-VL trig graph parameter extraction",
            "output_format": "JSON {function, amplitude, period, phase_shift, vertical_shift}",
            "priority": "P1",
        },
        {
            "id": "math_mechanics_diagram",
            "name": "力学图",
            "category": ContentCategory.FORCE_DIAGRAM,
            "description": "Pulleys, inclined planes, connected particles, projectile paths, velocity-time graphs",
            "examples": ["Two particles connected by string over pulley", "Block on slope with friction", "Projectile trajectory"],
            "paper_location": "P4 mechanics",
            "ocr_strategy": "Qwen3-VL mechanics problem parsing + PaddleOCR for values",
            "output_format": "JSON {setup_type, given_values, unknown}",
            "priority": "P0",
        },
        {
            "id": "math_vector_diagram",
            "name": "向量图",
            "category": ContentCategory.DIAGRAM,
            "description": "3D vector diagrams, position vectors, lines and planes, geometric proofs",
            "examples": ["Vector parallelogram", "3D coordinate system with vectors"],
            "paper_location": "P3 vectors",
            "ocr_strategy": "Qwen3-VL vector visualization description",
            "output_format": "JSON {vectors[{name, components?}], geometric_relationship}",
            "priority": "P1",
        },
        {
            "id": "math_statistical_table",
            "name": "统计表",
            "category": ContentCategory.STATISTICAL_TABLE,
            "description": "Normal distribution table, binomial probability table, cumulative frequency, grouped data",
            "examples": ["Standard normal Z-table", "Grouped frequency distribution"],
            "paper_location": "P5/P6 probability and statistics",
            "ocr_strategy": "PaddleOCR PP-StructureV3 table + numerical validation",
            "output_format": "JSON/CSV table",
            "priority": "P1",
        },
        {
            "id": "math_written_solution",
            "name": "手写解答步骤",
            "category": ContentCategory.HANDWRITING,
            "description": "Student's handwritten working: algebraic manipulation, calculus steps, method marks demonstration",
            "examples": ["Student writes integration steps", "Handwritten quadratic formula"],
            "paper_location": "Student uploads for grading",
            "ocr_strategy": "PaddleOCR handwriting + Surya LaTeX + LLM semantic correction chain",
            "output_format": "LaTeX + confidence score + correction suggestions",
            "priority": "P0",
        },
    ],
}

# Also define shared types across all subjects
SHARED_CONTENT_TYPES = [
    {
        "id": "shared_handwriting",
        "name": "手写内容（通用）",
        "category": ContentCategory.HANDWRITING,
        "description": "Any handwritten student answer: calculations, explanations, essays, diagrams",
        "ocr_strategy": "PaddleOCR handwriting → LLM correction → confidence scoring → low confidence = ask user to retype",
        "priority": "P0",
    },
    {
        "id": "shared_table",
        "name": "通用表格",
        "category": ContentCategory.TABLE,
        "description": "Generic data tables with rows and columns",
        "ocr_strategy": "PaddleOCR PP-StructureV3 → HTML/Markdown",
        "priority": "P0",
    },
    {
        "id": "shared_photo",
        "name": "实物照片",
        "category": ContentCategory.PHOTO,
        "description": "Photos of lab equipment, real-world economics scenarios, experimental results",
        "ocr_strategy": "Qwen3-VL description + metadata extraction",
        "priority": "P2",
    },
    {
        "id": "shared_marking",
        "name": "批改标注",
        "category": ContentCategory.MARKING_ANNOTATION,
        "description": "Mark scheme annotations showing acceptable answers, method marks, ecf notes",
        "ocr_strategy": "PaddleOCR text + structured parsing of mark scheme format",
        "priority": "P1",
    },
]


def get_subject_types(subject_code: str) -> List[Dict]:
    """Get all content types for a subject."""
    return SUBJECT_CONTENT_TYPES.get(subject_code, [])


def get_p0_types(subject_code: str) -> List[Dict]:
    """Get priority-0 (blocking) content types."""
    types = get_subject_types(subject_code)
    return [t for t in types if t.get("priority") == "P0"]


def get_ocr_strategy(content_type_id: str) -> Optional[str]:
    """Get the OCR strategy for a content type."""
    for subject_types in SUBJECT_CONTENT_TYPES.values():
        for t in subject_types:
            if t["id"] == content_type_id:
                return t["ocr_strategy"]
    for t in SHARED_CONTENT_TYPES:
        if t["id"] == content_type_id:
            return t["ocr_strategy"]
    return None


def count_types_by_subject():
    """Statistics of content types per subject."""
    stats = {}
    for code, types in SUBJECT_CONTENT_TYPES.items():
        p0 = len([t for t in types if t.get("priority") == "P0"])
        stats[code] = {
            "total": len(types),
            "p0": p0,
            "ocr_strategies": list(set(t["ocr_strategy"].split("+")[0].strip() for t in types)),
        }
    return stats
