"""
Grading calibration: compare Agent scoring against ground truth (mark schemes).
Computes MAE, Pearson correlation, and per-dimension errors.

Requirements: MAE < 0.5/4 total marks, Pearson r > 0.85

Because we lack human-scored student work, this pilot calibration uses:
  - Known mark-scheme answers as "correct" (full marks)
  - Deliberate error variants as "partial/wrong" (computed from mark scheme)
  - Agent grading compared against mark-scheme-derived ground truth
"""
import json
import math
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.tutoring.core import Agent
from agent.database import create_conversation

PROJECT_ROOT = Path(__file__).parent.parent
EVAL_DIR = PROJECT_ROOT / "data" / "eval"

CALIBRATION_CASES = [
    # ── Pure Mathematics 1 ──
    {
        "id": "P1-01",
        "question": "Find the gradient of the curve y = x^3 - 3x^2 + 2x at the point where x = 2.",
        "mark_scheme": "dy/dx = 3x^2 - 6x + 2 [1]\nAt x=2: 3(4) - 6(2) + 2 = 12 - 12 + 2 = 2 [1]\nGradient = 2",
        "student_answer": "dy/dx = 3x^2 - 6x + 2\nAt x=2: 3(4) - 6(2) + 2 = 12 - 12 + 2 = 2\nGradient = 2",
        "gold_score": 2,
        "gold_max": 2,
        "subject": "9709",
    },
    {
        "id": "P1-02",
        "question": "Find the gradient of the curve y = x^3 - 3x^2 + 2x at the point where x = 2.",
        "mark_scheme": "dy/dx = 3x^2 - 6x + 2 [1]\nAt x=2: 3(4) - 6(2) + 2 = 12 - 12 + 2 = 2 [1]\nGradient = 2",
        "student_answer": "dy/dx = 3x^2 - 6x + 2\nAt x=2: 3(4) - 6(2) + 2 = 12 - 12 + 2 = 3\nGradient = 3",
        "gold_score": 1,
        "gold_max": 2,
        "subject": "9709",
    },
    {
        "id": "P1-03",
        "question": "Find the gradient of the curve y = x^3 - 3x^2 + 2x at the point where x = 2.",
        "mark_scheme": "dy/dx = 3x^2 - 6x + 2 [1]\nAt x=2: 3(4) - 6(2) + 2 = 12 - 12 + 2 = 2 [1]\nGradient = 2",
        "student_answer": "gradient = 3",
        "gold_score": 0,
        "gold_max": 2,
        "subject": "9709",
    },
    {
        "id": "P1-04",
        "question": "Solve the equation 2x^2 + 5x - 3 = 0, giving your answers exactly.",
        "mark_scheme": "Factorise: (2x - 1)(x + 3) = 0 [1]\nor quadratic formula: x = [-5 ± sqrt(25+24)] / 4 = [-5 ± 7] / 4 [1]\nx = 1/2 and x = -3 [1]",
        "student_answer": "(2x - 1)(x + 3) = 0\nx = 1/2, x = -3",
        "gold_score": 3,
        "gold_max": 3,
        "subject": "9709",
    },
    {
        "id": "P1-05",
        "question": "Solve the equation 2x^2 + 5x - 3 = 0, giving your answers exactly.",
        "mark_scheme": "Factorise: (2x - 1)(x + 3) = 0 [1]\nor quadratic formula: x = [-5 ± sqrt(25+24)] / 4 = [-5 ± 7] / 4 [1]\nx = 1/2 and x = -3 [1]",
        "student_answer": "Using formula: a=2, b=5, c=-3\nx = [-5 ± sqrt(25 - 4*2*(-3))] / (2*2)\nx = [-5 ± sqrt(25 + 24)] / 4\nx = (-5 ± 7)/4\nx = 1/2, x = -3",
        "gold_score": 3,
        "gold_max": 3,
        "subject": "9709",
    },
    {
        "id": "P1-06",
        "question": "Solve the equation 2x^2 + 5x - 3 = 0, giving your answers exactly.",
        "mark_scheme": "Factorise: (2x - 1)(x + 3) = 0 [1]\nor quadratic formula: x = [-5 ± sqrt(25+24)] / 4 = [-5 ± 7] / 4 [1]\nx = 1/2 and x = -3 [1]",
        "student_answer": "x = -3 or x = 0.5",
        "gold_score": 1.5,
        "gold_max": 3,
        "subject": "9709",
    },
    # ── Integration ──
    {
        "id": "INT-01",
        "question": "Find the integral of f(x) = 3x^2 + 4x - 1 with respect to x.",
        "mark_scheme": "∫ 3x^2 dx = x^3 [1]\n∫ 4x dx = 2x^2 [1]\n∫ -1 dx = -x [1]\nF(x) = x^3 + 2x^2 - x + C [1]",
        "student_answer": "∫(3x^2 + 4x - 1)dx = x^3 + 2x^2 - x + C",
        "gold_score": 4,
        "gold_max": 4,
        "subject": "9709",
    },
    {
        "id": "INT-02",
        "question": "Find the integral of f(x) = 3x^2 + 4x - 1 with respect to x.",
        "mark_scheme": "∫ 3x^2 dx = x^3 [1]\n∫ 4x dx = 2x^2 [1]\n∫ -1 dx = -x [1]\nF(x) = x^3 + 2x^2 - x + C [1]",
        "student_answer": "x^3 + 2x^2 - x",
        "gold_score": 3,
        "gold_max": 4,
        "subject": "9709",
    },
    {
        "id": "INT-03",
        "question": "Find the integral of f(x) = 3x^2 + 4x - 1 with respect to x.",
        "mark_scheme": "∫ 3x^2 dx = x^3 [1]\n∫ 4x dx = 2x^2 [1]\n∫ -1 dx = -x [1]\nF(x) = x^3 + 2x^2 - x + C [1]",
        "student_answer": "= 3x^3 + 4x^2 - x",
        "gold_score": 0,
        "gold_max": 4,
        "subject": "9709",
    },
    # ── Derivative / Chain Rule ──
    {
        "id": "DIF-01",
        "question": "Differentiate y = (2x + 1)^5 with respect to x.",
        "mark_scheme": "Let u = 2x + 1, du/dx = 2 [1]\ny = u^5, dy/du = 5u^4 [1]\ndy/dx = 5(2x+1)^4 × 2 = 10(2x+1)^4 [1]",
        "student_answer": "dy/dx = 5(2x+1)^4 × 2 = 10(2x+1)^4",
        "gold_score": 3,
        "gold_max": 3,
        "subject": "9709",
    },
    {
        "id": "DIF-02",
        "question": "Differentiate y = (2x + 1)^5 with respect to x.",
        "mark_scheme": "Let u = 2x + 1, du/dx = 2 [1]\ny = u^5, dy/du = 5u^4 [1]\ndy/dx = 5(2x+1)^4 × 2 = 10(2x+1)^4 [1]",
        "student_answer": "dy/dx = 10(2x+1)^4",
        "gold_score": 3,
        "gold_max": 3,
        "subject": "9709",
    },
    {
        "id": "DIF-03",
        "question": "Differentiate y = (2x + 1)^5 with respect to x.",
        "mark_scheme": "Let u = 2x + 1, du/dx = 2 [1]\ny = u^5, dy/du = 5u^4 [1]\ndy/dx = 5(2x+1)^4 × 2 = 10(2x+1)^4 [1]",
        "student_answer": "5(2x+1)^4",
        "gold_score": 1.5,
        "gold_max": 3,
        "subject": "9709",
    },
    # ── Mechanics ──
    {
        "id": "MEC-01",
        "question": "A particle moves along a straight line. Its velocity v ms^{-1} at time t seconds is given by v = 3t^2 - 4t + 1. Find the acceleration at t = 2.",
        "mark_scheme": "a = dv/dt = 6t - 4 [1]\nAt t=2: a = 6(2) - 4 = 12 - 4 = 8 ms^{-2} [1]",
        "student_answer": "a = dv/dt = 6t - 4\nAt t=2: a = 12 - 4 = 8 ms^{-2}",
        "gold_score": 2,
        "gold_max": 2,
        "subject": "9709",
    },
    {
        "id": "MEC-02",
        "question": "A particle moves along a straight line. Its velocity v ms^{-1} at time t seconds is given by v = 3t^2 - 4t + 1. Find the acceleration at t = 2.",
        "mark_scheme": "a = dv/dt = 6t - 4 [1]\nAt t=2: a = 6(2) - 4 = 12 - 4 = 8 ms^{-2} [1]",
        "student_answer": "a = 3t^2 - 4t + 1\n= 3(4) - 4(2) + 1 = 12 - 8 + 1 = 5 ms^{-2}",
        "gold_score": 0,
        "gold_max": 2,
        "subject": "9709",
    },
    {
        "id": "MEC-03",
        "question": "A particle moves along a straight line. Its velocity v ms^{-1} at time t seconds is given by v = 3t^2 - 4t + 1. Find the acceleration at t = 2.",
        "mark_scheme": "a = dv/dt = 6t - 4 [1]\nAt t=2: a = 6(2) - 4 = 12 - 4 = 8 ms^{-2} [1]",
        "student_answer": "a = 6t - 4 = 8",
        "gold_score": 1.5,
        "gold_max": 2,
        "subject": "9709",
    },
]


def run_calibration() -> dict:
    """Run all calibration cases and compute metrics."""
    agent = Agent(conv_id=create_conversation(title="Calibration Run"))
    results = []

    for case in CALIBRATION_CASES:
        try:
            grading = agent.grade(
                question=case["question"],
                mark_scheme=case["mark_scheme"],
                student_answer=case["student_answer"],
            )
            agent_score = grading.get("score_awarded", 0)
            agent_max = grading.get("score_max", case["gold_max"])

            entry = {
                "id": case["id"],
                "question": case["question"],
                "student_answer": case["student_answer"][:100] + "...",
                "gold_score": case["gold_score"],
                "agent_score": agent_score,
                "max_marks": case["gold_max"],
                "error": case["gold_score"] - agent_score,
                "abs_error": abs(case["gold_score"] - agent_score),
                "verdict": grading.get("verdict", ""),
                "rubric": grading.get("rubric", {}),
                "tags": grading.get("misconception_tags", []),
            }
            results.append(entry)
            print(f"  [{case['id']}] Gold={case['gold_score']}/{case['gold_max']} "
                  f"Agent={agent_score}/{agent_max} Δ={case['gold_score'] - agent_score:+.1f}")
        except Exception as e:
            print(f"  [{case['id']}] ERROR: {e}")
            results.append({
                "id": case["id"],
                "gold_score": case["gold_score"],
                "agent_score": 0,
                "max_marks": case["gold_max"],
                "error": case["gold_score"],
                "abs_error": case["gold_score"],
                "error_msg": str(e),
            })

    # Compute metrics
    scores = [r["agent_score"] for r in results]
    golds = [r["gold_score"] for r in results]
    errors = [r["abs_error"] for r in results]
    n = len(results)

    mae = statistics.mean(errors) if errors else float("inf")
    mae_norm = mae / 4.0  # Normalize to [0,1] for 4-mark scale

    # Pearson correlation
    mean_g = statistics.mean(golds) if golds else 0
    mean_s = statistics.mean(scores) if scores else 0
    cov = sum((g - mean_g) * (s - mean_s) for g, s in zip(golds, scores)) / n
    std_g = math.sqrt(sum((g - mean_g)**2 for g in golds) / n)
    std_s = math.sqrt(sum((s - mean_s)**2 for s in scores) / n)
    r = cov / (std_g * std_s) if std_g > 0 and std_s > 0 else 0

    # Per-dimension rubric errors
    dim_errors = {"correctness": [], "method": [], "representation": [], "communication": []}
    for entry in results:
        rubric = entry.get("rubric", {})
        for dim in dim_errors:
            agent_v = rubric.get(dim)
            if agent_v is not None:
                # Gold rubric not available for individual dims, so we check consistency
                dim_errors[dim].append(agent_v)

    report = {
        "n_cases": n,
        "mae": round(mae, 3),
        "mae_normalised": round(mae_norm, 3),
        "pearson_r": round(r, 3),
        "pass_mae": mae < 0.5,
        "pass_correlation": r > 0.85,
        "cases": results,
        "rubric_means": {dim: round(statistics.mean(vals), 3) if vals else None
                         for dim, vals in dim_errors.items()},
    }
    return report


if __name__ == "__main__":
    print("Running Grading Calibration (15 cases)...")
    print("-" * 60)
    report = run_calibration()
    print("-" * 60)
    print(f"\nResults:")
    print(f"  Cases: {report['n_cases']}")
    print(f"  MAE:   {report['mae']:.3f} marks (needs < 0.5 → {'PASS' if report['pass_mae'] else 'FAIL'})")
    print(f"  r:     {report['pearson_r']:.3f} (needs > 0.85 → {'PASS' if report['pass_correlation'] else 'FAIL'})")
    print(f"  Rubric means: {report['rubric_means']}")

    # Save report
    out_path = EVAL_DIR / "calibration_report.json"
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nReport saved to: {out_path}")

    if report["pass_mae"] and report["pass_correlation"]:
        print("\nCALIBRATION PASSED")
    else:
        print("\nCALIBRATION NEEDS IMPROVEMENT")
