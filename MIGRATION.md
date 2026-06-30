# A-Level Tutor Agent — Complete Project Context for Migration

## Project Overview

An AI tutoring agent for Cambridge A-Level (CAIE) students. Supports 4 subjects via multi-model LLM routing, ChromaDB vector search, SQLite persistence, Gradio web UI + CLI. Built on Python 3.9.

**4 CAIE subjects**: 9701 Chemistry, 9702 Physics, 9708 Economics, 9709 Mathematics

**Architecture**: Single Agent class with DeepSeek V4-Flash function calling (6 tools), local LM Studio/Qwen3-VL for vision, Ollama qwen3-embedding for vectors, Qwen3-Reranker for two-stage retrieval.

**Budget**: Designed for ~¥5/month/student. Budget guard (¥50/month, ¥2/day) with toggle in UI.

---

## File Structure

```
alevel_assistant/
├── agent/
│   ├── config.py              # Model routing, subjects, API keys, paths
│   ├── database.py            # SQLite 6 tables, cost/budget logging
│   ├── security.py            # Prompt injection, file validation, EXIF stripping
│   ├── tutoring/
│   │   ├── core.py            # Agent class — chat(), tool calling, output sanitization
│   │   ├── prompts.py         # System prompt — teaching style, tools, LaTeX rules
│   │   └── patterns.py        # Exam pattern templates from JSON files
│   ├── diagrams/
│   │   ├── renderer.py        # Kroki API (mermaid/tikz/vegalite/graphviz) + plot extraction
│   │   ├── spec_builder.py    # 14 economic diagram types → exact math specs
│   │   └── plotter.py         # matplotlib → SVG with staggered curve labels
│   ├── retrieval/
│   │   ├── builder.py         # ChromaDB KB builder (Ollama embedding + text chunking)
│   │   ├── search.py          # Vector search (3 collections: textbooks/past_papers/techniques)
│   │   └── reranker.py        # Qwen3-Reranker-0.6B for two-stage retrieval
│   ├── ocr/
│   │   ├── pipeline.py        # 6-engine OCR (PaddleOCR + Qwen VLM + FormulaNet)
│   │   ├── vision.py          # LM Studio Qwen3-VL for grading + diagram analysis
│   │   └── content_types.py   # 30 content types across 4 subjects
│   └── grading/
│       └── grader.py          # PedCoT two-stage grading (blind solve → compare → M/A/B marks)
├── web/app.py                 # Gradio 4.44.1 Web — chat, status matrix, image upload, cost panel
├── chat.py                    # CLI cmd.Cmd interface
├── build_kb.py                # KB build entry point
├── tests/                     # 5 test suites (~300 tests)
├── tools/crawler/             # Past paper downloader, resource index
├── tools/scripts/             # Backup/restore, textbook download
└── docs/
    ├── plans/                 # Development plans, diagram system v2 plan
    └── log/
        ├── w1.md~w5.md        # Weekly development logs (w5.md covers ALL changes)
        └── diagram_v2.md      # Diagram rendering system log
```

## DIAGRAM: Project Architecture
```
User (CLI/Gradio) → Agent.chat() → security.detect_injection()
    → _detect_subject() → _call_llm(DeepSeek V4-Flash, thinking=True)
    → Tool calling loop (max 20 rounds, consecutive dup detection):
        search_textbook(P0), search_past_papers, get_exam_pattern, search_exam_techniques
    → _sanitize_output:
        render_all_diagrams(plot→mermaid→tikz→vegalite) → _fix_katex → ASCII detection
    → Return response
```

## Model Routing

| Role | Model | Provider | Cost |
|------|-------|----------|------|
| Tutor text | deepseek-v4-flash | DeepSeek API | $0.14/$0.28 per 1M tokens |
| Vision/grading | qwen/qwen3-vl-8b | LM Studio local | Free |
| Embedding | qwen3-embedding:0.6b | Ollama local | Free |
| Reranker | Qwen3-Reranker-0.6B | ModelScope cache | Free |

**DeepSeek config**: thinking=True, max_tokens=8192 configured but toggleable via UI. V4 thinking mode does NOT support tool_choice="required", only "auto". This means tool calls are not guaranteed — the system prompt tries to force them but LLM sometimes ignores.

## 6 Tool Definitions

| Tool | Description | Trigger |
|------|-------------|---------|
| search_textbook | ChromaDB search | **Mandatory every query** |
| search_past_papers | Past papers qp/ms/er | Problem-solving, formula questions, "make me a question" |
| get_exam_pattern | JSON pattern templates | Essay structure, mark schemes, exam techniques |
| search_exam_techniques | Study guides | Revision, common mistakes, command words |
| grade_homework_image | Vision grading | Image upload |
| get_subject_info | Subject metadata | Not commonly used |

## Key Features

### 1. Smart n_results (LLM-controlled, 1-50)
LLM decides how many results to fetch based on semantic complexity. No manual slider. Parameter `n_results` on search_textbook and search_past_paper.

### 2. Parallel Tool Calling
System prompt tells LLM: "match multiple conditions → call multiple tools in one function_call". Tools called simultaneously, not sequentially.

### 3. Consecutive Duplicate Detection
If tool call (name + arguments) matches the LAST executed call exactly → skip it. If ALL calls in a round are duplicates → stop and tell user. (NOT full-history tracking, only consecutive.)

### 4. Status Matrix (Gradio UI)
5-cell grid always visible: [🧠思考] [📚教材] [📝真题] [🎯套路] [💡技巧]
Active cells glow with color gradient, inactive dimmed at 35% opacity with grayscale.
Implementation: `web/app.py STATUS_MATRIX → _render_matrix(active_keys)`.

### 5. KaTeX Fixer (_fix_katex)
Post-processing that fixes common KaTeX errors:
- Currency `$10` → `10元` (only outside code blocks)
- Stray `$` → `＄` (full-width, not a delimiter)
- `&` in math → `\text{ and }`
- `\ce{...}` → `\text{...}` (KaTeX lacks mhchem)
- **Code blocks (```...```) are EXTRACTED, protected from fixing, then restored** — critical fix

### 6. Self-Correction Detection
Patterns detect LLM self-correction artifacts ("等一下，不对", "让我重新", "重新算"). Detected content gets a warning banner. Code blocks excluded from detection.

### 7. Debug Logging (data/gui_debug.log)
Every interaction logged as JSON lines (last 500 entries). SVG base64 stripped before storing (replaced with [SVG] placeholder). Fields: session, model, conv_len, elapsed_s, svg_count, tool_calls, katex_fixes, response (text only).

### 8. GUI Toggles (Web sidebar)
- Token limit on/off (default on, 8192)
- Budget on/off (default on, ¥50/month)

## Critical Bug Fixes Applied (commit range 642e387 → 493d272, ~110 commits)

### Import Rebinding Bug (Bug A)
`from agent.tutoring.core import _last_model` created a local reference in web/app.py. When chat() rebinds `_last_model = "deepseek-v4-flash"`, app.py didn't see the change. Fixed: `import agent.tutoring.core as _core`, access `_core._last_model` directly.

### SVG Rendering Pipeline Broken (Bug C)
`extract_and_render_plot/mermaid/tikz/vegalite` functions were DELETED during refactoring. `render_all_diagrams` called undefined functions, all diagram rendering silently failed. Fixed: re-implemented all 4 extraction functions with code-block fallback.

### Currency $ Destroying TikZ (Bug G)
`_fix_katex` currency fixer ran BEFORE code block protection. `$12` inside ```tikz blocks was converted to `12元`. Fixed: extract+protect code blocks before any fixer operations.

### Self-Correction False Negatives (Bug H)
Patterns missed "等一下，画法不对" and "嗯，让我重新". Fixed: added patterns for these variants.

### ASCII Art False Positives
TikZ code arrows/coordinates triggered ASCII art warning. Fixed: exclude code blocks from ASCII detection.

### Debug Log SVG Truncation
34KB base64 SVGs filled the log, leaving no room for text analysis. Fixed: strip SVG data URIs before logging.

## Current Known Issues

1. **TikZ circuit rendering unreliable**: Kroki public API has 5-second timeout. Complex circuits fail. schemdraw (local) was tested but incompatible with matplotlib 3.5.1. TikZ code blocks preserved as fallback.
2. **LLM sometimes ignores tool call requirement**: DeepSeek V4 thinking mode doesn't support tool_choice="required". System prompt tries to enforce but not 100% reliable.
3. **Table LaTeX rendering**: Markdown tables with inline `$...$` formulas sometimes fail in Gradio. System prompt tells LLM to avoid LaTeX in tables.
4. **Base64 SVG bloat**: Diagrams rendered as inline base64 (~16KB each). Should be served as files with URLs instead.
5. **Single-threaded web app**: Gradio with `concurrency_limit=1`.
6. **Kroki public service unreliable**: Frequent outages for tikz rendering.

## Devlog Convention
- All changes MUST be logged in `docs/log/w5.md` (current week). Earlier weeks: w1.md~w4.md.
- Format: numbered sections (§1, §2...), commit hashes, bullet-point details, tables for file changes and bug tracking.
- After every conversation: update devlog → git add → git commit → git push → restart webapp (`nohup python3 web/app.py > /tmp/gradio.log 2>&1 &`).
- Commit format: `type: short description` where type is feat/fix/docs/test/security.
- **CRITICAL**: NEVER commit real API keys. Never put real keys in log files.

## Diagram Rendering Pipeline

```
```plot JSON → build_spec() → render_economics() → SVG
```circuit → NOT IMPLEMENTED (schemdraw failed)
```mermaid → Kroki API → SVG (or code block fallback)
```tikz template=X → Kroki API → SVG (or code block fallback)
```vega-lite → Kroki API → SVG (or code block fallback)
```

Economic diagrams: 14 types via matplotlib plotter with staggered curve labels (fontsize 14, demand labels left-above curve, supply labels right-below).

## Running the Project

```bash
# Start webapp
python3 web/app.py  # → http://127.0.0.1:7860

# CLI
python3 chat.py

# Build KB
python3 build_kb.py --subject 9702

# Tests
python3 tests/test_diagram_v2.py  # 48 diagram tests
python3 tests/test_w5_debug.py    # ~80 security tests
```

## .env Requirements
```
DEEPSEEK_API_KEY=sk-xxx
LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1
LMSTUDIO_VLM_MODEL=qwen/qwen3-vl-8b
BUDGET_MONTHLY_CNY=50
BUDGET_DAILY_CNY=2
```

## Migration Tasks (for next agent)

1. Read ALL of `docs/log/w5.md` for complete change history
2. Run `python3 web/app.py` to start the webapp → test at localhost:7860
3. Check `data/gui_debug.log` for latest interactions
4. Circuit diagram rendering: try upgrading matplotlib to fix schemdraw, or find alternative
5. Base64 bloat: implement file-based SVG serving (save to data/rendered/, serve via Gradio static mount)
6. Multi-process: ChromaDB needs single-process, but webapp could use queue for concurrent requests
7. Improve TikZ fallback: better error messages when Kroki fails
