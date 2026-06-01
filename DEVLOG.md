# DevLog — A-Level Tutor Assistant

## 2025-06-01: Layout & Rendering Fixes

### Problem 1: SVG Diagrams Garbled
LLM-generated SVG had mangled text (chart titles, labels unreadable).
**Root cause**: LLM writes Chinese text into SVG `<text>` elements without proper font/encoding.
**Fix**: Switched from PNG to SVG output (16KB vs 50KB per diagram, 3x smaller).
Updated system prompt with explicit SVG template (axes, colors, annotations) so LLM produces
consistent, valid SVGs that render correctly in Gradio's Chatbot.

### Problem 2: 8 Diagrams Flood Response
LLM generated 8 full SVG diagrams in one reply (~128KB base64), maxing out token budget.
**Fix**: System prompt now limits to max 2 diagrams per response.  
`prompts.py:18` — `每次回复最多 2 张图`

### Problem 3: KaTeX Parse Error
Gradio's KaTeX renderer threw parse errors because:
1. LLM used `$` as currency symbol (e.g. `$10`) → unpaired LaTeX delimiters
2. `&` inside `$...$` blocks (KaTeX alignment character)
3. `\ce{H2O}` commands (KaTeX doesn't support mhchem)

**Fix** (two layers):
- **Prompt layer** (`prompts.py:77-101`): Explicit KaTeX rules — no `$` for currency,
  no `&` in math, no `\ce`, must pair all delimiters.
- **Post-processing** (`core.py:_fix_katex`): Character-level scanner that:
  - Replaces currency `$10` → `10元` (before LaTeX block scanning)
  - Escapes stray `$` → `＄` (full-width, not a delimiter)
  - Converts `&` → `\text{ and }` inside math blocks
  - Converts `\ce{...}` → `\text{...}` inside math blocks
  - Correctly handles nesting: `$$a = $b$ + c$$`

### Problem 4: Debugging Was Blind
Every bug required guessing the LLM output from user screenshots.
**Fix**: Added `data/gui_debug.log` — JSON-lines log (last 500 entries) of every GUI interaction:
```json
{
  "session": "abc12345",
  "subject": "9708",
  "model": "deepseek-v3",
  "conv_len": 12,
  "svg_count": 2,
  "raw_len": 3240,
  "response_len": 3512,
  "katex_fixes": {"currency": 1, "stray_dollar": 0, "ampersand": 1, "ce_command": 0},
  "tool_calls": [{"tool": "search_textbook", "args": {...}, "result_len": 800}],
  "elapsed_s": 4.32,
  "error": null,
  "response": "<first 5000 chars of LLM output>"
}
```

### Related Changes
- `max_tokens`: 8192 → 20480 (avoids truncation for long economics responses)
- Conversation history: SVG base64 blobs stripped before re-insertion to prevent context pollution
- `.gitignore`: Added `data/rendered/` (SVG cache) and `data/gui_debug.log`
