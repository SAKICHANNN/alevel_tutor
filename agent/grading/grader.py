"""
PedCoT (Pedagogical Chain-of-Thought) Two-Stage Grader.

Based on Jiang et al. (IJCAI 2024): "LLMs can Find Mathematical Reasoning Mistakes
by Pedagogical Chain-of-Thought."

Architecture:
  Stage 1 (Regenerate): LLM solves the problem BLIND to student's answer →
    generates expected concepts, method, calculations, and M-A-B mark allocation.
  Stage 2 (Extract-Compare-Grade): LLM sees student's answer + Stage-1 output →
    extracts student's steps, compares with expected, awards M/A/B marks.

Why two-stage (not one-stage):
  - If LLM sees student answer before regenerating, it suffers "conformity bias"
    — it lazily agrees with the student's approach even if wrong.
  - Regenerating blind forces independent judgment first, then objective comparison.
"""
import json
import re
import time
from typing import Optional

from rich.console import Console

from agent.config import MODELS
from agent.database import log_error, save_grading_result, check_budget

console = Console()

# ── Stage 1 Prompt: Regenerate Expected Solution ──

SUBJECT_NAMES = {
    "9701": "Chemistry",
    "9702": "Physics",
    "9708": "Economics",
    "9709": "Mathematics",
}


def _subject_name(code: Optional[str]) -> str:
    return SUBJECT_NAMES.get(code or "9709", "Mathematics")


STAGE1_REGENERATE_PROMPT = """You are a Cambridge A-Level {subject} examiner. Solve the following problem step by step. You do NOT see the student's answer yet — this is just you solving the problem independently.

## Step 1: List the mathematical concepts involved (Remember level)
- What topics/skills does this problem test?

## Step 2: Describe the solution method (Understand level)
- What is the overall approach? What formulas/theorems apply?
- Break it down into numbered solution steps.

## Step 3: Execute calculations (Apply level)
- Work through each step with actual numbers.
- Show intermediate results.
- Give the final answer.

## Step 4: Allocate M-A-B marks
Using Cambridge M1/A1/B1 conventions:
- M marks: valid method applied (not lost for arithmetic slips)
- A marks: correct answer (only awarded if M mark earned)
- B marks: independent correct statement

For each numbered step, specify:
  step|mark_type|points|what_earns_the_mark
Example:
  1|M1|1|Correctly differentiate: dy/dx = 3x^2 - 6x + 2
  2|A1|1|Correct gradient: substitute x=2, get 2

Problem: {question}
"""

# ── Stage 2 Prompt: Extract-Compare-Grade ──

STAGE2_GRADE_PROMPT = """You are a Cambridge A-Level {subject} examiner. You now grade the student's answer against the expected solution generated earlier.

## Expected Solution & Mark Allocation
{expected_solution}

## Cambridge Marking Rules
- M marks: Award for valid method, even if arithmetic wrong. Do NOT require the exact wording — just that the method is correctly applied.
- A marks: Award only if the associated M mark was earned AND the answer is correct. 
- B marks: Independent correct statement. Can award even without M marks.
- FT (Follow-Through): If student made an error earlier but used the correct method thereafter, award the later M marks. Only deduct the A mark for the wrong value.
- Marks are awarded POSITIVELY. Do not deduct for missing steps.
- Method must be APPLIED to the problem. Just quoting a formula is NOT enough for M mark.
- If student writes the final answer with NO working: award ONLY the final A1 if correct, ZERO otherwise (no M marks without working).
- Ignore minor notation issues unless they change the meaning (e.g., dx instead of dy).

## Grading Task
Compare the student's answer against the expected mark points:

1. For EACH mark point in the allocation, determine if the student earned it.
2. Apply M→A dependency: if an M mark was not earned, its dependent A mark cannot be awarded.
3. Apply Follow-Through: if the student used a correct method on wrong numbers from a prior error, award the M mark.
4. Count total marks awarded.

## Student's Answer
{student_answer}

## Output Format
Return ONLY valid JSON:
{{
  "score_awarded": <total marks earned>,
  "score_max": <total marks available>,
  "confidence": <0.0-1.0 — how confident are you in this grade? Lower if student's approach differs significantly from expected>,
  "verdict": "<one-line summary in Chinese>",
  "mark_points": [
    {{"step": <number>, "type": "M1|A1|B1", "points": <max>, "awarded": <earned>, "reason": "<why awarded or not>"}},
    ...
  ],
  "rubric": {{
    "correctness": <0-1 proportion of A marks earned>,
    "method": <0-1 proportion of M marks earned>,
    "representation": <0-1 — notation, units, significant figures>,
    "communication": <0-1 — clarity, step structure>
  }},
  "strengths": ["<what student did right>"],
  "mistakes": [{{"location": "<where>", "error": "<what>", "fix": "<correction>"}}],
  "misconception_tags": ["<from: concept, method, algebra, units, carelessness>"],
  "next_step": "<concrete suggestion in Chinese>",
  "citations": ["Cambridge A-Level 9709 syllabus topic reference"]
}}
"""


def _clean_json(content: str) -> str:
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    return content.strip()


def _parse_float(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _fallback_result(total_marks: int = 4) -> dict:
    return {
        "score_awarded": 0,
        "score_max": total_marks,
        "confidence": 0.0,
        "verdict": "评分系统出错，请重试",
        "rubric": {"correctness": 0, "method": 0, "representation": 0, "communication": 0},
        "strengths": [],
        "mistakes": [],
        "misconception_tags": ["system_error"],
        "next_step": "请重新提交批改",
        "citations": [],
    }


def grade(question: str, student_answer: str,
          mark_scheme: Optional[str] = None,
          conv_id: Optional[int] = None,
          subject_code: Optional[str] = None) -> dict:
    """
    Grade a student's answer using PedCoT two-stage process.

    If mark_scheme is provided (matched from database), uses it directly.
    Otherwise, uses Stage-1 to regenerate the expected solution.

    Args:
        question: The problem statement
        student_answer: Student's written answer
        mark_scheme: Optional — real mark scheme if available from search
        conv_id: DB conversation ID for persistence
        subject_code: e.g. "9709"

    Returns:
        Grading result dict with score_awarded, score_max, rubric, mistakes, etc.
    """
    config = MODELS["tutor"]
    if not config.api_key:
        return _fallback_result()

    # ── Stage 0: Match mark scheme from database ──
    matched_ms = mark_scheme
    if not matched_ms:
        try:
            from agent.retrieval.search import search_past_papers
            ms_results = search_past_papers(
                question[:200],  # Use first 200 chars as query
                subject_code or "9709",
                paper_type="ms",
                n_results=1,
                use_rerank=True,
            )
            if ms_results and ms_results[0].get("rerank_score", 0) > 0.75:
                matched_ms = ms_results[0]["content"][:1500]
                console.print(f"[dim]Matched mark scheme: "
                             f"{ms_results[0].get('metadata', {}).get('filename', '?')} "
                             f"(score={ms_results[0].get('rerank_score', 0):.2f})[/dim]")
        except Exception as e:
            console.print(f"[dim]Mark scheme search failed: {e}[/dim]")

    total_marks = 0

    if matched_ms:
        # ── Direct grading with matched mark scheme ──
        prompt = _build_direct_grade_prompt(question, matched_ms, student_answer, subject_code)
        try:
            resp_raw = _call_api(config, prompt, temperature=0.3, max_tokens=2048)
            result = _parse_grading_response(resp_raw)
            total_marks = result.get("score_max", 0)
            if conv_id:
                save_grading_result(conv_id, result, question=question,
                                    mark_scheme=matched_ms, student_answer=student_answer)
            return result
        except Exception as e:
            log_error("grading_fail", "grading/grader.py:direct", str(e),
                      conv_id, subject_code,
                      misconception_tags=["system_error"])
            console.print(f"[yellow]Direct grading failed, falling back to PedCoT: {e}[/yellow]")

    # ── PedCoT: Stage 1 — Regenerate Expected Solution ──
    stage1_prompt = STAGE1_REGENERATE_PROMPT.format(
        subject=_subject_name(subject_code),
        question=question,
    )
    try:
        expected_solution = _call_api(config, stage1_prompt, temperature=0.3, max_tokens=2048)
        # Extract mark allocation from Stage-1 output to determine total_marks
        marks_found = re.findall(r'(\d+)\|(?:M|A|B)\d*\|\s*(\d+)', expected_solution)
        total_marks = sum(int(p) for _, p in marks_found) if marks_found else 4
    except Exception as e:
        log_error("grading_fail", "grading/grader.py:stage1", str(e),
                  conv_id, subject_code)
        expected_solution = f"Unable to generate expected solution: {e}"
        total_marks = 4

    # ── PedCoT: Stage 2 — Extract-Compare-Grade ──
    stage2_prompt = STAGE2_GRADE_PROMPT.format(
        subject=_subject_name(subject_code),
        expected_solution=expected_solution,
        student_answer=student_answer,
    )
    try:
        resp_raw = _call_api(config, stage2_prompt, temperature=0.3, max_tokens=2048)
        result = _parse_grading_response(resp_raw)
        # Override total_marks from Stage-1 allocation
        if result.get("score_max", 0) == 0 or result.get("score_max") != total_marks:
            result["score_max"] = total_marks
        if conv_id:
            save_grading_result(conv_id, result, question=question,
                                mark_scheme=expected_solution[:1000],
                                student_answer=student_answer)
        return result
    except Exception as e:
        log_error("grading_fail", "grading/grader.py:stage2", str(e),
                  conv_id, subject_code,
                  misconception_tags=["system_error"])
        console.print(f"[yellow]PedCoT grading failed: {e}[/yellow]")
        return _fallback_result(total_marks)


def _build_direct_grade_prompt(question: str, mark_scheme: str, student_answer: str,
                              subject_code: Optional[str] = None) -> str:
    subj = _subject_name(subject_code)
    return f"""You are a Cambridge A-Level {subj} examiner. Grade this student's answer against the EXACT mark scheme provided below.

## Cambridge M-A-B Marking Rules
- M marks: Award for valid method applied (not lost for arithmetic slips)
- A marks: Award only if associated M mark earned AND answer correct
- B marks: Independent correct statements. Can award without M marks.
- FT (Follow-Through): Award M marks for correct method on wrong numbers from prior error
- Award marks POSITIVELY. Do not penalize extra correct work.
- Whole marks only.

## Question
{question}

## Mark Scheme
{mark_scheme}

## Student Answer
{student_answer}

## Output (JSON only, no markdown)
Return JSON with: score_awarded, score_max, confidence, verdict (Chinese), rubric (correctness/method/representation/communication: 0-1), strengths[], mistakes[], misconception_tags[], next_step (Chinese), citations[]"""


def _call_api(config, prompt: str, temperature: float, max_tokens: int) -> str:
    import requests

    # BudgetGuard check
    ok, budget_msg = check_budget()
    if not ok:
        raise RuntimeError(f"预算限制: {budget_msg}")

    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": "You are a Cambridge A-Level examiner. "
             "Answer concisely and accurately. Follow the format instructions exactly."},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    t0 = time.time()
    resp = requests.post(
        f"{config.base_url}/chat/completions",
        headers=headers,
        json=payload,
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    latency_ms = int((time.time() - t0) * 1000)
    usage = data.get("usage", {})
    if usage:
        from agent.database import log_cost
        log_cost(
            model_key="tutor",
            model_name=config.model,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            reasoning_tokens=usage.get("completion_tokens_details", {}).get("reasoning_tokens", 0),
            latency_ms=latency_ms,
        )
    return data["choices"][0]["message"]["content"]


def _parse_grading_response(content: str) -> dict:
    content = _clean_json(content)
    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        # Try to find first complete JSON object (non-greedy)
        match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content)
        if match:
            try:
                result = json.loads(match.group())
            except json.JSONDecodeError:
                return _fallback_result()
        else:
            return _fallback_result()

    # Normalize and validate
    result.setdefault("score_awarded", 0)
    result.setdefault("score_max", 0)
    result.setdefault("confidence", 0.5)
    result.setdefault("verdict", "评分完成")
    rubric = result.setdefault("rubric", {})
    for k in ["correctness", "method", "representation", "communication"]:
        rubric.setdefault(k, 0.0)
    result.setdefault("strengths", [])
    result.setdefault("mistakes", [])
    result.setdefault("misconception_tags", [])
    result.setdefault("next_step", "")
    result.setdefault("citations", [])

    # Ensure numeric types
    result["score_awarded"] = _parse_float(result["score_awarded"])
    result["score_max"] = _parse_float(result["score_max"])
    result["confidence"] = _parse_float(result["confidence"])

    # Apply Cambridge rule: whole marks only
    result["score_awarded"] = round(result["score_awarded"])
    result["score_max"] = round(result["score_max"])

    return result
