"""
Multi-engine OCR Pipeline — handles ALL content types across 4 A-Level subjects.

Pipeline architecture:
Image → Preprocessor → Content Router → Specialized Extractors → Result Merger → CanonicalQuestion

Supported content types: text, math formulas, chemical equations, structural formulas,
reaction mechanisms, tables, graphs, circuit diagrams, force diagrams, wave diagrams,
energy cycles, economic graphs, statistical tables, handwriting.
"""
import base64
import io
import json
import re
import hashlib
from enum import Enum
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass, field

import requests
from rich.console import Console

from agent.config import CHROMA_DIR

console = Console()

# ── Result Models ──

class ExtractionStatus(Enum):
    SUCCESS = "success"
    LOW_CONFIDENCE = "low_confidence"
    FAILED = "failed"
    NEEDS_HUMAN = "needs_human"


@dataclass
class TextRegion:
    bbox: list            # [x, y, w, h]
    text: str
    confidence: float
    region_type: str      # "paragraph", "title", "caption", "label"


@dataclass
class FormulaRegion:
    bbox: list
    latex: str
    confidence: float
    formula_type: str     # "inline_math", "display_math", "chemical_eq"


@dataclass
class TableRegion:
    bbox: list
    html: str
    markdown: str
    rows: int
    cols: int
    confidence: float


@dataclass
class DiagramRegion:
    bbox: list
    diagram_type: str     # "circuit", "force", "wave", "mechanism", "energy_cycle", etc.
    description: str      # VLM-generated description
    structured_data: dict  # Extracted structured info
    original_image: Optional[bytes] = None
    confidence: float = 0.0


@dataclass
class GraphRegion:
    bbox: list
    graph_type: str       # "demand_supply", "ad_as", "coordinate", "trig", "data_plot"
    axes: dict            # {x_label, y_label, x_unit, y_unit}
    description: str
    data_points: list     # [{x, y}]
    confidence: float


@dataclass
class HandwritingRegion:
    bbox: list
    raw_ocr_text: str
    corrected_text: str
    latex_equations: list
    confidence: float
    needs_manual_review: bool


@dataclass
class PageExtractionResult:
    page_number: int
    text_regions: list = field(default_factory=list)
    formula_regions: list = field(default_factory=list)
    table_regions: list = field(default_factory=list)
    diagram_regions: list = field(default_factory=list)
    graph_regions: list = field(default_factory=list)
    handwriting_regions: list = field(default_factory=list)
    full_text: str = ""
    overall_confidence: float = 0.0
    processing_time_ms: float = 0.0


# ── Image Preprocessing ──

class ImagePreprocessor:
    """Classical CV preprocessing without any ML models."""

    @staticmethod
    def preprocess(image_data: bytes, is_document: bool = True) -> bytes:
        """Apply preprocessing pipeline."""
        try:
            import numpy as np
            from PIL import Image, ImageEnhance, ImageFilter

            img = Image.open(io.BytesIO(image_data))

            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Resize if too large (long edge to 1600px)
            w, h = img.size
            max_dim = 1600
            if max(w, h) > max_dim:
                ratio = max_dim / max(w, h)
                img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

            if is_document:
                # Convert to grayscale for document processing
                gray = img.convert('L')
                arr = np.array(gray)

                # Adaptive-like thresholding for text clarity
                # Simple Otsu-like approach
                mean_val = np.mean(arr)
                if mean_val < 128:  # Dark background?
                    arr = 255 - arr  # Invert
                threshold = np.percentile(arr, 50)
                arr = ((arr > threshold) * 255).astype(np.uint8)

                img = Image.fromarray(arr).convert('RGB')

            # Slight contrast enhancement
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.2)

            # Sharpen
            img = img.filter(ImageFilter.SHARPEN)

            output = io.BytesIO()
            img.save(output, format='PNG', optimize=True)
            return output.getvalue()

        except ImportError:
            console.print("[yellow]PIL/Pillow not available. Skipping image preprocessing.[/yellow]")
            return image_data

    @staticmethod
    def compute_hash(image_data: bytes) -> str:
        return hashlib.sha256(image_data).hexdigest()[:16]


# ── OCR Cache ──

class OCRCache:
    """Simple file-based cache for OCR results."""

    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or (CHROMA_DIR.parent / "ocr_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, image_hash: str) -> Optional[dict]:
        cache_file = self.cache_dir / f"{image_hash}.json"
        if cache_file.exists():
            with open(cache_file) as f:
                return json.load(f)
        return None

    def set(self, image_hash: str, result: dict):
        cache_file = self.cache_dir / f"{image_hash}.json"
        with open(cache_file, "w") as f:
            json.dump(result, f, ensure_ascii=False)


# ── PaddleOCR Engine ──

class PaddleOCREngine:
    """PaddleOCR wrapper for Chinese + English text OCR (v3.x API)."""

    def __init__(self):
        self._ocr = None

    @property
    def ocr(self):
        if self._ocr is None:
            try:
                from paddleocr import PaddleOCR
                self._ocr = PaddleOCR(lang='en')
            except ImportError:
                console.print("[yellow]PaddleOCR not installed. pip install paddleocr[/yellow]")
                self._ocr = None
        return self._ocr

    def extract_text(self, image_data: bytes) -> list:
        """Extract text regions using PaddleOCR 3.x predict API."""
        if self.ocr is None:
            return [{"bbox": [0, 0, 0, 0], "text": "[PaddleOCR not available]", "confidence": 0}]
        import numpy as np
        from PIL import Image
        img = Image.open(io.BytesIO(image_data))
        arr = np.array(img)
        results = self.ocr.predict(arr)
        if not results:
            return []
        regions = []
        for page_result in results:
            texts = page_result.get('rec_texts', []) if isinstance(page_result, dict) else getattr(page_result, 'rec_texts', [])
            scores = page_result.get('rec_scores', []) if isinstance(page_result, dict) else getattr(page_result, 'rec_scores', [])
            polys = page_result.get('dt_polys', []) if isinstance(page_result, dict) else getattr(page_result, 'dt_polys', [])
            for i, text in enumerate(texts):
                bbox = [0, 0, 0, 0]
                if i < len(polys) and len(polys[i]) >= 4:
                    poly = polys[i]
                    bbox = [int(poly[0][0]), int(poly[0][1]),
                            int(poly[2][0]), int(poly[2][1])]
                conf = float(scores[i]) if i < len(scores) else 0.0
                regions.append({
                    "bbox": bbox,
                    "text": str(text),
                    "confidence": conf,
                })
        return regions

    def detect_formula_regions(self, image_data: bytes) -> list:
        """Detect potential formula regions by low-confidence + math symbol heuristics.
        Returns list of tight bounding boxes suitable for PP-FormulaNet cropping."""
        regions = self.extract_text(image_data)
        formula_boxes = []
        math_pattern = re.compile(r'[=+\-×÷∫∑√∞∂Δπθ≤≥±→←↑↓⇒]|\\frac|\\int|\\sum|[a-z]=|=[a-z]')
        for r in regions:
            conf = r["confidence"]
            text = r["text"]
            score = 0
            if conf < 0.95:
                score += 2
            if math_pattern.search(text):
                score += 3
            if len(text) < 15 and any(c.isdigit() for c in text):
                score += 1
            if score >= 3:
                bbox = r["bbox"]
                # Add small padding
                pad = 5
                formula_boxes.append([
                    max(0, bbox[0] - pad),
                    max(0, bbox[1] - pad),
                    bbox[2] + pad,
                    bbox[3] + pad,
                ])
        return formula_boxes

    def extract_tables(self, image_data: bytes) -> list:
        """Extract tables using PPStructureV3 (PaddleOCR 3.x)."""
        try:
            from paddleocr import PPStructureV3
            engine = PPStructureV3()
            import numpy as np
            from PIL import Image
            img = Image.open(io.BytesIO(image_data))
            arr = np.array(img)
            results = engine.predict(arr)
            tables = []
            for item in results:
                item_type = item.get('type', '')
                if 'table' in str(item_type).lower():
                    tables.append({
                        "bbox": list(item.get('bbox', [0, 0, 0, 0])),
                        "html": item.get('res', {}).get('html', ''),
                        "markdown": item.get('res', {}).get('markdown', ''),
                        "confidence": float(item.get('confidence', 0)),
                    })
            return tables
        except ImportError:
            return []
        except Exception as e:
            console.print(f"[dim]PPStructureV3 failed: {e}[/dim]")
            return []


# ── Formula / LaTeX OCR Engines ──

class FormulaOCREngine:
    """Formula OCR: delegates to Qwen VLM (local, accurate, free). 
    PP-FormulaNet retained only as fast fallback if VLM unavailable."""

    def __init__(self):
        self._pp_ocr = None
        self._init_attempted = False

    def extract_formulas(self, image_data: bytes) -> list:
        # Primary: Qwen VLM (most accurate)
        try:
            from agent.config import get_active_vision_model
            config = get_active_vision_model()
            if config and config.api_key:
                b64 = base64.b64encode(image_data).decode()
                resp = requests.post(
                    f"{config.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {config.api_key}", "Content-Type": "application/json"},
                    json={
                        "model": config.model,
                        "messages": [{"role": "user", "content": [
                            {"type": "text", "text": "Extract the mathematical formula as LaTeX. Output ONLY the LaTeX, no markdown, no $$."},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                        ]}],
                        "temperature": 0.1, "max_tokens": 400,
                    },
                    timeout=120,
                )
                data = resp.json()
                tex = data["choices"][0]["message"]["content"].strip()
                tex = tex.removeprefix("```latex").removesuffix("```")
                tex = re.sub(r'^\$\$?\s*', '', tex)
                tex = re.sub(r'\s*\$\$?$', '', tex)
                if tex:
                    console.print("[dim]Qwen VLM formula extracted[/dim]")
                    return [{"latex": tex, "confidence": 0.90}]
        except Exception as e:
            console.print(f"[dim]VLM formula failed: {e}[/dim]")

        # Fallback: PP-FormulaNet (fast, less accurate, free)
        return self._try_pp_formulanet(image_data) or self._try_mathpix(image_data)

    def _init_pp_formulanet(self) -> bool:
        if self._init_attempted:
            return self._formula_ocr is not None
        self._init_attempted = True
        try:
            from paddleocr import FormulaRecognition
            self._formula_ocr = FormulaRecognition(
                model_name="PP-FormulaNet-S"
            )
            console.print("[dim]PP-FormulaNet-S loaded[/dim]")
            return True
        except ImportError:
            console.print("[yellow]paddleocr not installed. pip install paddleocr[/yellow]")
        except Exception as e:
            console.print(f"[dim]PP-FormulaNet init skipped: {e}[/dim]")
        return False

    def _try_pp_formulanet(self, image_data: bytes) -> list:
        if not self._init_pp_formulanet() or self._formula_ocr is None:
            return []
        try:
            import numpy as np
            from PIL import Image
            img = Image.open(io.BytesIO(image_data))
            arr = np.array(img)
            result = self._formula_ocr.predict(arr)
            if isinstance(result, list) and len(result) > 0:
                r = result[0]
                tex = r.get("rec_formula", "") if isinstance(r, dict) else str(r)
                if tex and len(tex) > 5:
                    return [{"latex": tex, "confidence": 0.85}]
        except Exception as e:
            console.print(f"[dim]PP-FormulaNet OCR failed: {e}[/dim]")
        return []
    
    def _try_vlm_ocr(self, image_data: bytes) -> list:
        """Use local Qwen VLM via LM Studio as OCR fallback for formulas."""
        try:
            from agent.config import get_active_vision_model
            config = get_active_vision_model()
            if not config or not config.api_key or config.provider == "zhipu":
                return []  # Only use local VLM, not cloud

            b64 = base64.b64encode(image_data).decode()
            resp = requests.post(
                f"{config.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {config.api_key}", "Content-Type": "application/json"},
                json={
                    "model": config.model,
                    "messages": [{"role": "user", "content": [
                        {"type": "text", "text": "Extract ONLY the mathematical formula as LaTeX. Output nothing else. No markdown, no $$."},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                    ]}],
                    "temperature": 0.1,
                    "max_tokens": 400,
                },
                timeout=120,
            )
            data = resp.json()
            tex = data["choices"][0]["message"]["content"].strip()
            tex = tex.removeprefix("```latex").removesuffix("```").strip()
            # Remove $$ wrappers if present
            tex = re.sub(r'^\$\$?\s*', '', tex)
            tex = re.sub(r'\s*\$\$?$', '', tex)
            if tex and not self._is_garbled_formula(tex):
                console.print(f"[dim]Qwen VLM OCR fallback succeeded[/dim]")
                return [{"latex": tex, "confidence": 0.90}]
        except Exception as e:
            console.print(f"[dim]VLM OCR fallback failed: {e}[/dim]")
        return []

    def extract_formulas(self, image_data: bytes) -> list:
        """Extract LaTeX formulas. PP-FormulaNet first, Qwen VLM fallback if garbled."""
        results = self._try_pp_formulanet(image_data)
        if results and not self._is_garbled_formula(results[0].get("latex", "")):
            return results
        vlm_results = self._try_vlm_ocr(image_data)
        if vlm_results:
            return vlm_results
        if results:
            results[0]["confidence"] = 0.3
            return results
        return self._try_mathpix(image_data)

    def _try_mathpix(self, image_data: bytes) -> list:
        import os
        api_key = os.getenv("MATHPIX_API_KEY") or os.getenv("MATHPIX_APP_KEY")
        if not api_key:
            return []
        try:
            resp = requests.post(
                "https://api.mathpix.com/v3/text",
                json={
                    "src": f"data:image/png;base64,{base64.b64encode(image_data).decode()}",
                    "formats": ["latex"],
                },
                headers={
                    "app_id": os.getenv("MATHPIX_APP_ID", ""),
                    "app_key": api_key,
                },
                timeout=30,
            )
            data = resp.json()
            if data.get("text"):
                return [{"latex": data["text"], "confidence": data.get("confidence", 0.9)}]
        except Exception as e:
            console.print(f"[dim]MathPix API failed: {e}[/dim]")
        return []


# ── Chemistry Structure OCR ──

class ChemistryOCREngine:
    """Chemistry structure recognition using DECIMER. Falls back gracefully."""

    def __init__(self):
        self._decimer = None
        self._init_attempted = False

    def _init_decimer(self) -> bool:
        if self._init_attempted:
            return self._decimer is not None
        self._init_attempted = True
        # DECIMER can be imported in different casing
        for mod_name in ["DECIMER", "decimer"]:
            try:
                mod = __import__(mod_name, fromlist=["predict_SMILES"])
                self._decimer = mod.predict_SMILES
                console.print(f"[dim]DECIMER loaded via '{mod_name}'[/dim]")
                return True
            except ImportError:
                continue
        console.print("[yellow]DECIMER not installed. Chemistry OCR disabled.[/yellow]")
        return False

    def extract_structure(self, image_data: bytes) -> Optional[dict]:
        if not self._init_decimer() or self._decimer is None:
            return None
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(image_data))
            smiles = self._decimer(img)
            if smiles and isinstance(smiles, str) and len(smiles) > 1:
                return {
                    "smiles": str(smiles),
                    "method": "decimer",
                    "confidence": 0.70
                }
        except Exception as e:
            console.print(f"[dim]DECIMER failed: {e}[/dim]")
        return None


# ── Vision Model (VLM) for complex understanding ──

class VisionAnalyzer:
    """Qwen3-VL (LM Studio local) handles all structural OCR: formulas, diagrams, tables, handwriting.
    PaddleOCR only does plain English text extraction. Everything difficult → Qwen."""

    def __init__(self):
        from agent.config import get_active_vision_model
        self.config = get_active_vision_model()

    @property
    def available(self) -> bool:
        return bool(self.config and self.config.api_key)

    def _call_vision(self, image_data: bytes, prompt: str, max_tokens: int = 1024) -> str:
        if not self.available:
            return ""

        img_b64 = base64.b64encode(image_data).decode()
        try:
            resp = requests.post(
                f"{self.config.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.config.model,
                    "messages": [{"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
                    ]}],
                    "temperature": 0.1,
                    "max_tokens": max_tokens,
                },
                timeout=120,
            )
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            console.print(f"[dim]VLM: {e}[/dim]")
            return ""

    def _page_type_prompt(self, subject_code: str) -> str:
        """Build a comprehensive prompt based on subject."""
        base = "Analyze this A-Level exam page. Extract everything:"
        prompts = {
            "9701": base + "\n- All text (question numbers, instructions)\n- Chemical equations as LaTeX (e.g. \\ce{2H2 + O2 -> 2H2O})\n- Organic structures (describe functional groups, bonds)\n- Tables (as markdown)\n- Graphs (describe axes, trends, key points)\n- Spectra (IR/NMR/MS — identify peaks)\n- If a reaction mechanism is shown, describe the arrow movement step-by-step",
            "9702": base + "\n- All text\n- Mathematical formulas as LaTeX\n- Circuit diagrams (list components and connections)\n- Force/free-body diagrams (describe forces and directions)\n- Wave diagrams\n- Graphs (describe axes, data, trends)\n- Tables (as markdown)",
            "9708": base + "\n- All text, especially the extract/data passage\n- Economic diagrams (demand/supply, AD/AS, elasticity, PPC, externality)\n- Tables (as markdown with headers)\n- Graphs and charts",
            "9709": base + "\n- All text and question numbers\n- ALL mathematical formulas as LaTeX (use $$ for display, $ for inline)\n- Coordinate geometry diagrams (describe curves, intersections)\n- Mechanics diagrams (forces, pulleys, inclines)\n- Tables (as markdown)\n- Statistical graphs and charts",
        }
        return prompts.get(subject_code, base + "\n- All text\n- Formulas as LaTeX\n- Diagrams\n- Tables\n- Graphs")

    def extract_formulas(self, image_data: bytes) -> str:
        return self._call_vision(
            image_data,
            "Extract ALL mathematical formulas from this image as LaTeX. Use $$ for display math, $ for inline. Include chemical equations as \\ce{}. Output only the formulas, one per line.",
            max_tokens=800,
        )

    def analyze_diagram(self, image_data: bytes, subject_code: str, diagram_type: str) -> dict:
        prompts = {
            "circuit": "Describe this circuit diagram. List all components, their connections, and values shown.",
            "force": "Describe this force/free-body diagram. What objects, forces, and directions are shown?",
            "wave": "Describe this wave diagram. What type, what measurements are shown?",
            "mechanism": "Describe this organic mechanism. What reaction type, what happens to electrons in each step?",
            "economic_graph": "Describe this economic diagram. What model, what curves shift, what outcome?",
        }
        prompt = prompts.get(diagram_type, f"Describe this {diagram_type} in detail.")
        desc = self._call_vision(image_data, prompt)
        return {"type": diagram_type, "description": desc}

    def extract_table(self, image_data: bytes) -> str:
        return self._call_vision(
            image_data,
            "Extract this table as a markdown table. Include all headers and data values. Output ONLY the markdown table.",
            max_tokens=600,
        )

    def read_handwriting(self, image_data: bytes) -> dict:
        text = self._call_vision(
            image_data,
            "Transcribe all handwritten text. Identify math symbols/formulas as LaTeX. Note unclear parts with [?]. Do not correct errors.",
            max_tokens=800,
        )
        return {"transcription": text}

    def full_page_parse(self, image_data: bytes, subject_code: str) -> str:
        """Comprehensive page parsing — text + formulas + tables + diagrams."""
        prompt = self._page_type_prompt(subject_code)
        return self._call_vision(image_data, prompt, max_tokens=1500)


# ── Main OCR Pipeline ──

class OCRPipeline:
    """Complete OCR pipeline handling all content types."""

    def __init__(self):
        self.preprocessor = ImagePreprocessor()
        self.cache = OCRCache()
        self.text_ocr = PaddleOCREngine()
        self.formula_ocr = FormulaOCREngine()
        self.chemo_ocr = ChemistryOCREngine()
        self.vision = VisionAnalyzer()

    def process_page(
        self,
        image_data: bytes,
        subject_code: str,
    ) -> PageExtractionResult:
        """Process a page image.
        PaddleOCR → plain text (fast). Qwen VLM → everything structural (formulas, tables, diagrams).
        """
        import time
        start = time.time()

        processed = self.preprocessor.preprocess(image_data, is_document=False)
        img_hash = self.preprocessor.compute_hash(image_data)

        # Cache check
        cached = self.cache.get(img_hash)
        if cached:
            console.print("[dim]OCR cache hit[/dim]")
            return PageExtractionResult(**cached)

        result = PageExtractionResult(page_number=0)

        # Step 1: PaddleOCR plain text (always, fast)
        console.print("[dim]PaddleOCR text...[/dim]")
        text_regions = self.text_ocr.extract_text(processed)
        for r in text_regions:
            result.text_regions.append(TextRegion(
                bbox=r["bbox"], text=r["text"], confidence=r["confidence"],
                region_type="paragraph"
            ))
        result.full_text = " ".join(r.text for r in result.text_regions)

        # Step 2: Qwen VLM handles everything structural
        if self.vision.available:
            console.print("[dim]Qwen VLM full-page parse...[/dim]")
            parsed = self.vision.full_page_parse(image_data, subject_code)  # Original image for VLM
            if parsed:
                result.diagram_regions.append(DiagramRegion(
                    bbox=[0, 0, 0, 0],
                    diagram_type="full_page",
                    description=parsed,
                    structured_data={"full_parse": parsed},
                    confidence=0.85,
                ))

            # Handwriting check
            if self._likely_handwriting(result):
                console.print("[dim]Handwriting analysis...[/dim]")
                hw = self.vision.read_handwriting(processed)
                confidence = 0.5
                result.handwriting_regions.append(HandwritingRegion(
                    bbox=[0, 0, 0, 0],
                    raw_ocr_text=result.full_text,
                    corrected_text=hw.get("transcription", ""),
                    latex_equations=[],
                    confidence=confidence,
                    needs_manual_review=confidence < 0.6,
                ))
        else:
            # Fallback: multi-engine approach (same as before, PaddleOCR only)
            console.print("[dim]VLM unavailable, PaddleOCR-only mode[/dim]")

        # Final confidence
        all_confs = [r.confidence for r in result.text_regions]
        result.overall_confidence = sum(all_confs) / len(all_confs) if all_confs else 0.5
        result.processing_time_ms = (time.time() - start) * 1000

        # Cache
        self.cache.set(img_hash, {
            "page_number": result.page_number,
            "text_regions": [{"bbox": t.bbox, "text": t.text, "confidence": t.confidence, "region_type": t.region_type} for t in result.text_regions],
            "full_text": result.full_text,
            "overall_confidence": result.overall_confidence,
        })

        return result

    def _likely_handwriting(self, result: PageExtractionResult) -> bool:
        """Heuristic: detect if image contains handwritten content."""
        if not result.text_regions:
            return False
        low_conf_count = sum(1 for r in result.text_regions if r.confidence < 0.7)
        total = len(result.text_regions)
        return total > 0 and (low_conf_count / total) > 0.3

    def process_question(
        self,
        image_data: bytes,
        subject_code: str,
    ) -> dict:
        """Process a question image. Returns text + VLM parsed content + confidence tier + user message."""
        result = self.process_page(image_data, subject_code)
        vlm_description = ""
        if result.diagram_regions:
            vlm_description = result.diagram_regions[0].description

        confidence = result.overall_confidence
        tier, user_message = self._degradation_tier(confidence)

        return {
            "status": "success" if confidence > 0.4 else "low_confidence",
            "confidence_tier": tier,
            "user_message": user_message,
            "subject": subject_code,
            "paddle_text": result.full_text,
            "vlm_parse": vlm_description,
            "overall_confidence": confidence,
            "processing_time_ms": result.processing_time_ms,
        }

    @staticmethod
    def _degradation_tier(confidence: float) -> tuple:
        """Return (tier_label, user_facing_message) based on OCR confidence."""
        if confidence >= 0.7:
            return ("clear", "")
        elif confidence >= 0.4:
            return ("unclear", "⚠️ 图片质量一般，OCR 可能不完整。请确认识别结果是否正确，如有错误可手动修正后继续。")
        else:
            return ("unreadable", "❌ 图片不清晰，无法准确识别。请重新拍照（光线充足、平铺拍摄）或手动输入题目内容。")


# ── Singleton ──

_pipeline_instance = None

def get_pipeline() -> OCRPipeline:
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = OCRPipeline()
    return _pipeline_instance


def extract_images_from_pdf(pdf_path: str, subject_code: str, page_range: tuple = None, min_drawings: int = 0) -> list:
    """Extract and analyze ALL images/charts/diagrams from any PDF.
    
    Handles:
    - Vector graphics (Cambridge past papers, syllabus) → renders page as high-res PNG
    - Embedded raster images (textbooks, study guides) → extracts and analyzes directly
    Both analyzed by Qwen VLM.
    
    Args:
        pdf_path: Path to PDF file
        subject_code: '9701'-'9709' for context-aware prompts
        page_range: (start, end) page range, defaults to all pages
        min_drawings: skip pages with fewer vector elements (0=analyze all non-text pages)
    
    Returns list of {page, type, description, text_ratio}.
    """
    import fitz

    doc = fitz.open(pdf_path)
    if page_range:
        start, end = page_range
    else:
        start, end = 0, len(doc)

    vision = VisionAnalyzer()
    if not vision.available:
        doc.close()
        return [{"error": "VLM not available. Start LM Studio with qwen/qwen3-vl-8b."}]

    results = []
    total = end - start

    for pg in range(start, min(end, len(doc))):
        page = doc[pg]
        text = page.get_text()
        text_len = len(text.strip())
        drawings = page.get_drawings()
        imgs = page.get_images(full=True)
        n_visual = len(drawings) + len(imgs)

        # Skip text-only pages (adjust threshold based on content)
        is_text_only = text_len > 100 and n_visual == 0
        if is_text_only:
            continue
        
        # Skip pages with too few visual elements
        if n_visual <= min_drawings:
            continue

        page_result = {"page": pg + 1, "text_chars": text_len, "drawings": len(drawings), "images": len(imgs)}

        # 1. Extract and analyze embedded raster images (textbooks)
        for img_idx, img_info in enumerate(imgs):
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            img_bytes = base_image["image"]
            ext = base_image["ext"]

            if len(img_bytes) > 5000:
                console.print(f"[dim]  Page {pg+1}, embedded {ext} ({len(img_bytes)/1024:.0f}KB)...[/dim]")
                desc = vision._call_vision(
                    img_bytes,
                    f"Analyze this image from a Cambridge A-Level {subject_code} document. "
                    "Describe any diagrams, charts, chemical structures, photos, or graphs. "
                    "Extract labels, data values, and key concepts.",
                    max_tokens=500,
                )
                page_result[f"embedded_{img_idx}"] = desc

        # 2. Render full page for vector graphics analysis (past papers, syllabus)
        if len(drawings) >= min_drawings or len(imgs) > 0:
            pix = page.get_pixmap(dpi=200)
            page_img = pix.tobytes("png")
            text_ratio = text_len / max(len(page_img), 1)
            
            console.print(f"[dim]  Page {pg+1}/{start+total}: {len(drawings)} vectors, {len(imgs)} imgs...[/dim]")
            desc = vision._call_vision(
                page_img,
                f"Analyze this page from Cambridge A-Level {subject_code} (page {pg+1}). "
                "Focus ONLY on visual content: diagrams, graphs, charts, chemical structures, "
                "circuit diagrams, force diagrams, economic models, or images. "
                "For each visual element: describe what it shows, identify the topic, "
                "and extract key labels, axes, values, or data points.",
                max_tokens=600,
            )
            page_result["page_analysis"] = desc
            page_result["text_ratio"] = round(text_ratio, 4)

        if len(page_result) > 3:  # has actual analysis beyond metadata
            results.append(page_result)

    doc.close()
    console.print(f"[green]Extracted visual content from {len(results)}/{total} pages[/green]")
    return results


def analyze_image_file(image_path: str, subject_code: str = "") -> dict:
    """Analyze any image file (PNG, JPG, etc.) for charts, diagrams, formulas.
    Routes to Qwen VLM for comprehensive understanding."""
    vision = VisionAnalyzer()
    if not vision.available:
        return {"error": "VLM not available. Start LM Studio with qwen/qwen3-vl-8b."}

    with open(image_path, "rb") as f:
        img_data = f.read()

    desc = vision.full_page_parse(img_data, subject_code) if subject_code else vision._call_vision(
        img_data,
        "Analyze this image in detail. Extract all text, formulas (as LaTeX), tables (as markdown), "
        "diagrams, charts, and graphs. Describe what each element shows.",
        max_tokens=1200,
    )
    return {"path": image_path, "subject": subject_code, "description": desc}
