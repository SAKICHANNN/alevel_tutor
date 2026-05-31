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

# ── W5.8: Chemistry (9701) ──

CHEMISTRY_CASES = [
    {
        "id": "CH-01", "subject": "9701",
        "question": "State Le Chatelier's principle and explain what happens to the equilibrium position of N2 + 3H2 ⇌ 2NH3 (ΔH = -92 kJ/mol) when the temperature is increased.",
        "mark_scheme": "Le Chatelier's principle: if a system at equilibrium is subjected to a change, the position of equilibrium shifts to oppose the change [1]. Since forward reaction is exothermic (ΔH < 0), increasing temperature shifts equilibrium to the left (endothermic direction) to absorb heat [1].",
        "student_answer": "Le Chatelier's principle says the equilibrium shifts to oppose changes. Increasing temperature favours the endothermic reaction. Since the forward reaction is exothermic, equilibrium shifts left, producing less NH3.",
        "gold_score": 2, "gold_max": 2,
    },
    {
        "id": "CH-02", "subject": "9701",
        "question": "State Le Chatelier's principle and explain what happens to the equilibrium position of N2 + 3H2 ⇌ 2NH3 (ΔH = -92 kJ/mol) when the temperature is increased.",
        "mark_scheme": "Le Chatelier's principle: if a system at equilibrium is subjected to a change, the position of equilibrium shifts to oppose the change [1]. Since forward reaction is exothermic (ΔH < 0), increasing temperature shifts equilibrium to the left (endothermic direction) to absorb heat [1].",
        "student_answer": "Le Chatelier's principle is about equilibrium shifting. Higher temperature means more NH3 because reactions go faster.",
        "gold_score": 0, "gold_max": 2,
    },
    {
        "id": "CH-03", "subject": "9701",
        "question": "Calculate the number of moles in 4.0 g of NaOH. (Na = 23, O = 16, H = 1)",
        "mark_scheme": "Mr(NaOH) = 23 + 16 + 1 = 40 g/mol [1]. n = m/Mr = 4.0/40 = 0.10 mol [1].",
        "student_answer": "Mr = 23 + 16 + 1 = 40\nn = 4.0 ÷ 40 = 0.1 mol",
        "gold_score": 2, "gold_max": 2,
    },
    {
        "id": "CH-04", "subject": "9701",
        "question": "Calculate the number of moles in 4.0 g of NaOH. (Na = 23, O = 16, H = 1)",
        "mark_scheme": "Mr(NaOH) = 23 + 16 + 1 = 40 g/mol [1]. n = m/Mr = 4.0/40 = 0.10 mol [1].",
        "student_answer": "4.0 / 40 = 0.1 mol",
        "gold_score": 1, "gold_max": 2,
    },
    {
        "id": "CH-05", "subject": "9701",
        "question": "Draw the displayed formula of ethene (C2H4) and state the type of bond between the carbon atoms.",
        "mark_scheme": "H2C=CH2 with correct double bond shown [1]. The bond is a double bond / σ + π bond [1].",
        "student_answer": "H H\n \\ /\n  C=C\n / \\\nH H\n\nIt's a double covalent bond.",
        "gold_score": 2, "gold_max": 2,
    },
    {
        "id": "CH-06", "subject": "9701",
        "question": "Explain why the first ionisation energy of magnesium (738 kJ/mol) is higher than that of sodium (496 kJ/mol).",
        "mark_scheme": "Mg has a greater nuclear charge (12 protons vs 11) [1]. Both have electrons removed from the 3s subshell, but Mg's smaller atomic radius / greater nuclear attraction makes the electron harder to remove [1].",
        "student_answer": "Magnesium has more protons than sodium, so the nuclear charge is greater. This means the outer electron is held more strongly and needs more energy to remove.",
        "gold_score": 2, "gold_max": 2,
    },
    {
        "id": "CH-07", "subject": "9701",
        "question": "Explain why the first ionisation energy of magnesium (738 kJ/mol) is higher than that of sodium (496 kJ/mol).",
        "mark_scheme": "Mg has a greater nuclear charge (12 protons vs 11) [1]. Both have electrons removed from the 3s subshell, but Mg's smaller atomic radius / greater nuclear attraction makes the electron harder to remove [1].",
        "student_answer": "Mg is heavier than Na so it has higher ionisation energy.",
        "gold_score": 0, "gold_max": 2,
    },
    {
        "id": "CH-08", "subject": "9701",
        "question": "In a titration, 25.0 cm³ of HCl of unknown concentration required 20.0 cm³ of 0.100 mol/dm³ NaOH for neutralisation. Calculate the concentration of HCl.",
        "mark_scheme": "HCl + NaOH → NaCl + H2O (1:1 ratio) [1]. n(NaOH) = 0.100 × 20.0/1000 = 0.00200 mol [1]. n(HCl) = n(NaOH) = 0.00200 mol [1]. c(HCl) = 0.00200 / (25.0/1000) = 0.0800 mol/dm³ [1].",
        "student_answer": "n(NaOH) = 0.100 × 0.020 = 0.002 mol\nSince 1:1, n(HCl) = 0.002 mol\nc(HCl) = 0.002 / 0.025 = 0.08 mol/dm³",
        "gold_score": 4, "gold_max": 4,
    },
    {
        "id": "CH-09", "subject": "9701",
        "question": "In a titration, 25.0 cm³ of HCl of unknown concentration required 20.0 cm³ of 0.100 mol/dm³ NaOH for neutralisation. Calculate the concentration of HCl.",
        "mark_scheme": "HCl + NaOH → NaCl + H2O (1:1 ratio) [1]. n(NaOH) = 0.100 × 20.0/1000 = 0.00200 mol [1]. n(HCl) = n(NaOH) = 0.00200 mol [1]. c(HCl) = 0.00200 / (25.0/1000) = 0.0800 mol/dm³ [1].",
        "student_answer": "20 × 0.1 = 2\n2 / 25 = 0.08 M",
        "gold_score": 1, "gold_max": 4,
    },
    {
        "id": "CH-10", "subject": "9701",
        "question": "Identify the functional group in CH3COOH and name the homologous series it belongs to.",
        "mark_scheme": "Functional group: carboxyl / -COOH [1]. Homologous series: carboxylic acids [1].",
        "student_answer": "Functional group: COOH (carboxyl group)\nHomologous series: carboxylic acids",
        "gold_score": 2, "gold_max": 2,
    },
]

# ── W5.8: Physics (9702) ──

PHYSICS_CASES = [
    {
        "id": "PH-01", "subject": "9702",
        "question": "A car accelerates from rest to 20 m/s in 5 seconds. Calculate the acceleration.",
        "mark_scheme": "a = (v - u) / t = (20 - 0) / 5 [1] = 4 m/s² [1].",
        "student_answer": "a = v / t = 20 / 5 = 4 m/s²",
        "gold_score": 2, "gold_max": 2,
    },
    {
        "id": "PH-02", "subject": "9702",
        "question": "A car accelerates from rest to 20 m/s in 5 seconds. Calculate the acceleration.",
        "mark_scheme": "a = (v - u) / t = (20 - 0) / 5 [1] = 4 m/s² [1].",
        "student_answer": "a = 20 × 5 = 100 m/s²",
        "gold_score": 0, "gold_max": 2,
    },
    {
        "id": "PH-03", "subject": "9702",
        "question": "State Ohm's law and calculate the current through a 10 Ω resistor connected to a 5 V battery.",
        "mark_scheme": "Ohm's law: V = IR (current is proportional to voltage at constant temperature) [1]. I = V/R = 5/10 = 0.5 A [1].",
        "student_answer": "Ohm's law: V = IR\nI = 5 / 10 = 0.5 A",
        "gold_score": 2, "gold_max": 2,
    },
    {
        "id": "PH-04", "subject": "9702",
        "question": "State Ohm's law and calculate the current through a 10 Ω resistor connected to a 5 V battery.",
        "mark_scheme": "Ohm's law: V = IR (current is proportional to voltage at constant temperature) [1]. I = V/R = 5/10 = 0.5 A [1].",
        "student_answer": "I = 5/10 = 0.5 A",
        "gold_score": 1, "gold_max": 2,
    },
    {
        "id": "PH-05", "subject": "9702",
        "question": "A wave has a frequency of 50 Hz and a wavelength of 6.8 m. Calculate its speed.",
        "mark_scheme": "v = fλ = 50 × 6.8 [1] = 340 m/s [1].",
        "student_answer": "v = 50 × 6.8 = 340 m/s",
        "gold_score": 2, "gold_max": 2,
    },
    {
        "id": "PH-06", "subject": "9702",
        "question": "A wave has a frequency of 50 Hz and a wavelength of 6.8 m. Calculate its speed.",
        "mark_scheme": "v = fλ = 50 × 6.8 [1] = 340 m/s [1].",
        "student_answer": "The speed is 340 m/s.",
        "gold_score": 0.5, "gold_max": 2,
    },
    {
        "id": "PH-07", "subject": "9702",
        "question": "Define the moment of a force and calculate the moment when a 10 N force is applied perpendicularly at a distance of 0.5 m from a pivot.",
        "mark_scheme": "Moment = force × perpendicular distance from pivot [1]. Moment = 10 × 0.5 = 5 Nm [1].",
        "student_answer": "Moment = F × d = 10 × 0.5 = 5 Nm",
        "gold_score": 2, "gold_max": 2,
    },
    {
        "id": "PH-08", "subject": "9702",
        "question": "Define the moment of a force and calculate the moment when a 10 N force is applied perpendicularly at a distance of 0.5 m from a pivot.",
        "mark_scheme": "Moment = force × perpendicular distance from pivot [1]. Moment = 10 × 0.5 = 5 Nm [1].",
        "student_answer": "5",
        "gold_score": 0.5, "gold_max": 2,
    },
    {
        "id": "PH-09", "subject": "9702",
        "question": "Calculate the kinetic energy of a 2 kg mass moving at 3 m/s.",
        "mark_scheme": "KE = 1/2 mv² = 1/2 × 2 × 3² [1] = 1/2 × 2 × 9 = 9 J [1].",
        "student_answer": "KE = 1/2 × 2 × 9 = 9 J",
        "gold_score": 2, "gold_max": 2,
    },
    {
        "id": "PH-10", "subject": "9702",
        "question": "Calculate the kinetic energy of a 2 kg mass moving at 3 m/s.",
        "mark_scheme": "KE = 1/2 mv² = 1/2 × 2 × 3² [1] = 1/2 × 2 × 9 = 9 J [1].",
        "student_answer": "KE = 2 × 9 = 18 J",
        "gold_score": 0, "gold_max": 2,
    },
]

# ── W5.8: Economics (9708) ──

ECONOMICS_CASES = [
    {
        "id": "EC-01", "subject": "9708",
        "question": "Define price elasticity of demand (PED) and state the formula.",
        "mark_scheme": "PED measures the responsiveness of quantity demanded to a change in price [1]. Formula: PED = % change in quantity demanded / % change in price [1].",
        "student_answer": "PED measures how much demand changes when price changes.\nPED = %ΔQD / %ΔP",
        "gold_score": 2, "gold_max": 2,
    },
    {
        "id": "EC-02", "subject": "9708",
        "question": "Define price elasticity of demand (PED) and state the formula.",
        "mark_scheme": "PED measures the responsiveness of quantity demanded to a change in price [1]. Formula: PED = % change in quantity demanded / % change in price [1].",
        "student_answer": "PED = % change in demand / % change in price",
        "gold_score": 1, "gold_max": 2,
    },
    {
        "id": "EC-03", "subject": "9708",
        "question": "Explain the difference between a movement along the demand curve and a shift of the demand curve.",
        "mark_scheme": "A movement along the demand curve is caused by a change in price of the good itself [1]. A shift of the demand curve is caused by changes in other factors (income, tastes, prices of related goods, etc.) [1].",
        "student_answer": "Movement along: caused by price change of the good.\nShift: caused by changes in other factors like income, preferences, or related goods.",
        "gold_score": 2, "gold_max": 2,
    },
    {
        "id": "EC-04", "subject": "9708",
        "question": "Explain the difference between a movement along the demand curve and a shift of the demand curve.",
        "mark_scheme": "A movement along the demand curve is caused by a change in price of the good itself [1]. A shift of the demand curve is caused by changes in other factors (income, tastes, prices of related goods, etc.) [1].",
        "student_answer": "Movement is when price changes. Shift is when the curve moves.",
        "gold_score": 1, "gold_max": 2,
    },
    {
        "id": "EC-05", "subject": "9708",
        "question": "Define inflation and state one cause of cost-push inflation.",
        "mark_scheme": "Inflation is a sustained increase in the general price level [1]. Cost-push inflation is caused by rising costs of production (e.g., higher wages, raw material prices, energy costs) [1].",
        "student_answer": "Inflation is when prices keep going up over time. Cost-push inflation happens when production costs rise, like when oil prices increase.",
        "gold_score": 2, "gold_max": 2,
    },
    {
        "id": "EC-06", "subject": "9708",
        "question": "Define inflation and state one cause of cost-push inflation.",
        "mark_scheme": "Inflation is a sustained increase in the general price level [1]. Cost-push inflation is caused by rising costs of production (e.g., higher wages, raw material prices, energy costs) [1].",
        "student_answer": "Inflation = prices going up. Caused by printing too much money.",
        "gold_score": 0.5, "gold_max": 2,
    },
    {
        "id": "EC-07", "subject": "9708",
        "question": "Explain how interest rate changes affect aggregate demand through the monetary transmission mechanism.",
        "mark_scheme": "Lower interest rates reduce the cost of borrowing [1], encouraging consumption and investment [1]. This increases aggregate demand (AD shifts right) [1].",
        "student_answer": "When interest rates go down, borrowing becomes cheaper. People and firms borrow more and spend more, which increases AD.",
        "gold_score": 3, "gold_max": 3,
    },
    {
        "id": "EC-08", "subject": "9708",
        "question": "Explain how interest rate changes affect aggregate demand through the monetary transmission mechanism.",
        "mark_scheme": "Lower interest rates reduce the cost of borrowing [1], encouraging consumption and investment [1]. This increases aggregate demand (AD shifts right) [1].",
        "student_answer": "Lower rates = more spending = higher AD.",
        "gold_score": 1, "gold_max": 3,
    },
    {
        "id": "EC-09", "subject": "9708",
        "question": "Using a diagram, explain the effect of a subsidy on a market. State the impact on consumer and producer surplus.",
        "mark_scheme": "A subsidy shifts the supply curve to the right / downwards by the amount of the subsidy [1]. Equilibrium quantity increases, price paid by consumers decreases, price received by producers increases [1]. Both consumer and producer surplus increase [1].",
        "student_answer": "A subsidy shifts supply right, lowering consumer price and increasing producer revenue. Both surpluses increase.",
        "gold_score": 3, "gold_max": 3,
    },
    {
        "id": "EC-10", "subject": "9708",
        "question": "Using a diagram, explain the effect of a subsidy on a market. State the impact on consumer and producer surplus.",
        "mark_scheme": "A subsidy shifts the supply curve to the right / downwards by the amount of the subsidy [1]. Equilibrium quantity increases, price paid by consumers decreases, price received by producers increases [1]. Both consumer and producer surplus increase [1].",
        "student_answer": "Subsidy = supply moves right. Consumers pay less.",
        "gold_score": 1, "gold_max": 3,
    },
]

ALL_CASES = CALIBRATION_CASES + CHEMISTRY_CASES + PHYSICS_CASES + ECONOMICS_CASES
    """Run all calibration cases and compute metrics."""
    agent = Agent(conv_id=create_conversation(title="Calibration Run"))
    results = []

    for case in cases if cases else ALL_CASES:
        try:
            subj = case.get("subject", "9709")
            if subj and subj != agent.current_subject:
                agent.set_subject(subj)

            grading = agent.grade(
                question=case["question"],
                mark_scheme=case.get("mark_scheme", "auto"),
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
    subjects = {
        "9709 Math": CALIBRATION_CASES,
        "9701 Chemistry": CHEMISTRY_CASES,
        "9702 Physics": PHYSICS_CASES,
        "9708 Economics": ECONOMICS_CASES,
    }
    all_reports = {}

    for label, cases in subjects.items():
        print(f"\nRunning {label} Calibration ({len(cases)} cases)...")
        print("-" * 60)
        report = run_calibration(cases, label=label)
        print(f"  MAE: {report['mae']:.3f} | r: {report['pearson_r']:.3f} | "
              f"MAE pass: {report['pass_mae']} | r pass: {report['pass_correlation']}")
        all_reports[label] = report

    # Overall
    print(f"\n{'='*60}")
    print("Overall Summary")
    print(f"{'='*60}")
    all_pass = True
    for label, r in all_reports.items():
        ok = "✅" if r['pass_mae'] and r['pass_correlation'] else "❌"
        print(f"  {ok} {label}: MAE={r['mae']:.3f}, r={r['pearson_r']:.3f}")
        if not (r['pass_mae'] and r['pass_correlation']):
            all_pass = False

    print(f"\nOverall: {'ALL PASS' if all_pass else 'SOME FAIL'}")

    out_path = EVAL_DIR / "calibration_report.json"
    with open(out_path, "w") as f:
        json.dump(all_reports, f, indent=2, ensure_ascii=False)
    print(f"\nReport saved to: {out_path}")
