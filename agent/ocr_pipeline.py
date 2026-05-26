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

from .config import CHROMA_DIR

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
    """PaddleOCR wrapper for Chinese + English text OCR."""

    def __init__(self):
        self._ocr = None

    @property
    def ocr(self):
        if self._ocr is None:
            try:
                from paddleocr import PaddleOCR
                self._ocr = PaddleOCR(lang='en', use_angle_cls=True, show_log=False)
            except ImportError:
                console.print("[yellow]PaddleOCR not installed. pip install paddleocr[/yellow]")
                self._ocr = None
        return self._ocr

    def extract_text(self, image_data: bytes) -> list:
        """Extract text regions from image. Returns [{bbox, text, confidence}]."""
        if self.ocr is None:
            return [{"bbox": [0, 0, 0, 0], "text": "[PaddleOCR not available]", "confidence": 0}]
        img = io.BytesIO(image_data)
        results = self.ocr.ocr(img.read(), cls=True)
        if not results or not results[0]:
            return []
        return [
            {
                "bbox": [int(line[0][0][0]), int(line[0][0][1]),
                         int(line[0][2][0]), int(line[0][2][1])],
                "text": line[1][0],
                "confidence": float(line[1][1]),
            }
            for line in results[0]
        ]

    def extract_tables(self, image_data: bytes) -> list:
        """Extract tables using PP-StructureV3."""
        try:
            from paddleocr import PPStructure
            engine = PPStructure(table=True, layout=False, show_log=False)
            img = io.BytesIO(image_data)
            results = engine(img.read())
            tables = []
            for item in results:
                if item.get('type') == 'table':
                    tables.append({
                        "bbox": item.get('bbox', [0, 0, 0, 0]),
                        "html": item.get('res', {}).get('html', ''),
                        "confidence": item.get('confidence', 0),
                    })
            return tables
        except ImportError:
            return []


# ── Formula / LaTeX OCR Engines ──

class FormulaOCREngine:
    """Formula OCR using Surya LaTeX + MathPix API fallback."""

    def __init__(self):
        self._surya = None

    def extract_formulas(self, image_data: bytes) -> list:
        """Extract LaTeX formulas from image. Falls back to MathPix if available."""
        results = self._try_surya(image_data)
        if not results:
            results = self._try_mathpix(image_data)
        return results

    def _try_surya(self, image_data: bytes) -> list:
        try:
            # Only import and initialize on first use
            if self._surya is None:
                from PIL import Image
                from surya.texify import TexifyPredictor
                self._surya = TexifyPredictor()

            img = io.BytesIO(image_data)
            result = self._surya(img)
            if result and hasattr(result, 'text'):
                return [{"latex": result.text, "confidence": getattr(result, 'confidence', 0.8)}]
        except ImportError:
            pass
        except Exception as e:
            console.print(f"[dim]Surya formula OCR failed: {e}[/dim]")
        return []

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
    """Chemistry structure recognition using DECIMER."""

    def __init__(self):
        self._decimer_loaded = False

    def extract_structure(self, image_data: bytes) -> Optional[dict]:
        """Extract SMILES from chemical structure image."""
        try:
            from DECIMER import predict_SMILES
            from PIL import Image

            img = Image.open(io.BytesIO(image_data))
            smiles = predict_SMILES(img)
            if smiles:
                return {
                    "smiles": smiles,
                    "method": "decimer",
                    "confidence": 0.75  # DECIMER doesn't provide confidence
                }
        except ImportError:
            pass
        except Exception as e:
            console.print(f"[dim]DECIMER failed: {e}[/dim]")
        return None


# ── Vision Model (VLM) for complex understanding ──

class VisionAnalyzer:
    """Use Qwen3-VL or GLM-4V for complex diagram/chart/graph understanding."""

    def __init__(self):
        from .config import get_active_vision_model
        self.config = get_active_vision_model()

    def _call_vision(self, image_data: bytes, prompt: str) -> str:
        if not self.config.api_key:
            console.print("[yellow]No vision API key configured.[/yellow]")
            return ""

        img_b64 = base64.b64encode(image_data).decode()

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.config.model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{img_b64}"},
                    },
                ],
            }],
            "temperature": 0.2,
            "max_tokens": 1024,
        }

        try:
            resp = requests.post(
                f"{self.config.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            console.print(f"[dim]Vision API failed: {e}[/dim]")
            return ""

    def analyze_diagram(self, image_data: bytes, subject_code: str, diagram_type: str) -> dict:
        """Analyze any diagram type and return structured understanding."""
        prompts = {
            "circuit": "Describe this circuit diagram. List all components, their connections, and values shown.",
            "force": "Describe this force/free-body diagram. What objects, forces, and directions are shown?",
            "wave": "Describe this wave diagram. What type of waves, what patterns/measurements are shown?",
            "mechanism": "Describe this organic reaction mechanism. What reaction type, what happens to electrons?",
            "energy_cycle": "Describe this energy cycle/enthalpy diagram. What substances and energy changes are shown?",
            "molecule_3d": "Describe this molecular geometry diagram. What shape, bond angles, and atom arrangement?",
            "spectrum": "Describe this spectrum/chromatogram. What type, key peaks/features shown?",
            "economic_graph": "Describe this economic diagram. What curves are shown, what economic situation does it depict?",
            "coordinate_graph": "Describe this mathematical graph. What function/curve, key points, axes labels?",
            "experiment": "Describe this experimental setup. What equipment is shown, what is being measured?",
        }
        prompt = prompts.get(diagram_type, f"Describe this {diagram_type} diagram in detail.")
        if subject_code:
            prompt += f" This is from Cambridge A-Level subject {subject_code}."

        description = self._call_vision(image_data, prompt)
        return {
            "type": diagram_type,
            "subject": subject_code,
            "description": description,
            "raw_response": description,
        }

    def extract_graph_data(self, image_data: bytes, subject_code: str) -> dict:
        """Extract semantic understanding of a graph (not numerical data)."""
        prompt = """Analyze this graph/chart:
1. What is plotted on each axis (label + unit)?
2. What type of graph is this (line, scatter, bar, curve)?
3. What is the overall trend or relationship shown?
4. Are there any key points (intercepts, maxima, minima, thresholds)?
5. If this is an economic graph, what economic model does it depict?"""

        description = self._call_vision(image_data, prompt)
        return {"description": description, "type": "graph_analysis"}

    def analyze_handwriting(self, image_data: bytes) -> dict:
        """Analyze handwritten content and attempt to interpret meaning."""
        prompt = """This image shows handwritten student work for an A-Level exam.
1. Transcribe ALL visible text and numbers you can read
2. Identify any mathematical symbols, formulas, or equations
3. Note any parts that are unclear or ambiguous
4. Do NOT correct errors - just transcribe what you see"""

        description = self._call_vision(image_data, prompt)
        return {"transcription": description}


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
        expected_types: Optional[list] = None,
    ) -> PageExtractionResult:
        """Process a page image and extract all content types."""
        import time
        start = time.time()

        # 1. Preprocess
        processed = self.preprocessor.preprocess(image_data)
        img_hash = self.preprocessor.compute_hash(processed)

        # 2. Check cache
        cached = self.cache.get(img_hash)
        if cached:
            console.print("[dim]OCR cache hit[/dim]")
            result = PageExtractionResult(**cached)
            return result

        result = PageExtractionResult(page_number=0)

        # 3. Text OCR (always run first - gives us layout understanding)
        console.print("[dim]PaddleOCR text extraction...[/dim]")
        text_regions = self.text_ocr.extract_text(processed)
        for r in text_regions:
            result.text_regions.append(TextRegion(
                bbox=r["bbox"], text=r["text"], confidence=r["confidence"],
                region_type="paragraph"
            ))
        result.full_text = " ".join(r.text for r in result.text_regions)

        # 4. Table extraction
        console.print("[dim]Table extraction...[/dim]")
        tables = self.text_ocr.extract_tables(processed)
        for t in tables:
            result.table_regions.append(TableRegion(
                bbox=t["bbox"], html=t["html"], markdown="",
                rows=0, cols=0, confidence=t["confidence"]
            ))

        # 5. Formula extraction (math + chemistry)
        console.print("[dim]Formula extraction...[/dim]")
        formulas = self.formula_ocr.extract_formulas(processed)
        for f in formulas:
            result.formula_regions.append(FormulaRegion(
                bbox=[0, 0, 0, 0], latex=f["latex"],
                confidence=f["confidence"],
                formula_type="display_math"
            ))

        # 6. Chemistry-specific: structure extraction
        if subject_code == "9701":
            console.print("[dim]Chemistry structure extraction...[/dim]")
            struct = self.chemo_ocr.extract_structure(processed)
            if struct:
                result.formula_regions.append(FormulaRegion(
                    bbox=[0, 0, 0, 0],
                    latex=f"\\ce{{{struct['smiles']}}}",
                    confidence=struct["confidence"],
                    formula_type="chemical_eq"
                ))

        # 7. Vision model for complex understanding (diagrams, graphs, mechanisms)
        if self.vision.config.api_key:
            console.print("[dim]Vision model analysis...[/dim]")
            # Classify what's in the image
            text_lower = result.full_text.lower()

            if subject_code == "9702" and any(w in text_lower for w in ["circuit", "resistor", "voltage"]):
                diag = self.vision.analyze_diagram(processed, subject_code, "circuit")
                result.diagram_regions.append(DiagramRegion(
                    bbox=[0, 0, 0, 0], diagram_type="circuit",
                    description=diag["description"], structured_data=diag,
                ))

            if subject_code == "9701" and any(w in text_lower for w in ["mechanism", "curly", "nucleophil"]):
                diag = self.vision.analyze_diagram(processed, subject_code, "mechanism")
                result.diagram_regions.append(DiagramRegion(
                    bbox=[0, 0, 0, 0], diagram_type="mechanism",
                    description=diag["description"], structured_data=diag,
                    original_image=processed,
                ))

            if subject_code == "9708":
                graph = self.vision.extract_graph_data(processed, subject_code)
                result.graph_regions.append(GraphRegion(
                    bbox=[0, 0, 0, 0], graph_type="economic_graph",
                    axes={}, description=graph["description"],
                    data_points=[], confidence=0.7,
                ))

        # 8. Handwriting detection and handling
        if self._likely_handwriting(result):
            console.print("[dim]Handwriting analysis...[/dim]")
            hw = self.vision.analyze_handwriting(processed)
            confidence = 0.5  # Default moderate for handwriting
            result.handwriting_regions.append(HandwritingRegion(
                bbox=[0, 0, 0, 0],
                raw_ocr_text=result.full_text,
                corrected_text=hw.get("transcription", ""),
                latex_equations=[],
                confidence=confidence,
                needs_manual_review=confidence < 0.6,
            ))

        # 9. Calculate overall confidence
        all_confs = [r.confidence for r in result.text_regions]
        if all_confs:
            result.overall_confidence = sum(all_confs) / len(all_confs)
        else:
            result.overall_confidence = 0.5

        result.processing_time_ms = (time.time() - start) * 1000

        # 10. Cache result
        self.cache.set(img_hash, {
            "page_number": result.page_number,
            "text_regions": [{"bbox": t.bbox, "text": t.text, "confidence": t.confidence, "region_type": t.region_type} for t in result.text_regions],
            "table_regions": [{"bbox": t.bbox, "html": t.html, "confidence": t.confidence} for t in result.table_regions],
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
        """Process a single question image and return CanonicalQuestion-like structure."""
        result = self.process_page(image_data, subject_code)

        return {
            "status": "success" if result.overall_confidence > 0.6 else "low_confidence",
            "subject": subject_code,
            "full_text": result.full_text,
            "tables": [
                {"html": t.html, "confidence": t.confidence}
                for t in result.table_regions
            ],
            "formulas": [
                {"latex": f.latex, "type": f.formula_type, "confidence": f.confidence}
                for f in result.formula_regions
            ],
            "diagrams": [
                {"type": d.diagram_type, "description": d.description}
                for d in result.diagram_regions
            ],
            "graphs": [
                {"type": g.graph_type, "description": g.description}
                for g in result.graph_regions
            ],
            "handwriting": [
                {
                    "raw_text": h.raw_ocr_text,
                    "corrected_text": h.corrected_text,
                    "confidence": h.confidence,
                    "needs_manual_review": h.needs_manual_review,
                }
                for h in result.handwriting_regions
            ],
            "overall_confidence": result.overall_confidence,
            "processing_time_ms": result.processing_time_ms,
        }


# ── Singleton ──

_pipeline_instance = None

def get_pipeline() -> OCRPipeline:
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = OCRPipeline()
    return _pipeline_instance
