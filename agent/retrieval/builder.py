"""
Knowledge base builder: extract text from PDFs, chunk, embed, store in ChromaDB.
Supports: textbooks, past papers.
"""
import json
import re
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

console = Console()

HAS_CHROMA = False
HAS_FITZ = False
HAS_OPENAI = False

try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMA = True
except ImportError:
    pass

try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    pass

try:
    from chromadb.utils import embedding_functions
    HAS_OPENAI = True
except ImportError:
    pass


from agent.config import CHROMA_DIR, TEXTBOOK_DIR, PAPERS_DIR, GUIDES_DIR


CHUNK_SIZE = 800
CHUNK_OVERLAP = 150


def _get_client():
    if not HAS_CHROMA:
        raise ImportError("chromadb not installed. Run: pip install chromadb")
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def _get_embedding_fn():
    """Try to get an embedding function. Falls back to chroma's default."""
    import os
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
    if api_key and HAS_OPENAI:
        try:
            return embedding_functions.OpenAIEmbeddingFunction(
                api_key=api_key,
                model_name="text-embedding-3-small",
            )
        except Exception:
            pass
    # Fallback: use sentence-transformers if available
    try:
        return embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
    except Exception:
        pass
    # Last resort: chroma default
    return None


def _extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from a PDF file using PyMuPDF."""
    if not HAS_FITZ:
        # Fallback: just note the file exists
        return f"[PDF: {pdf_path.name}] (Install PyMuPDF for text extraction: pip install PyMuPDF)"

    try:
        doc = fitz.open(str(pdf_path))
        full_text = []
        for page in doc:
            text = page.get_text()
            if text.strip():
                full_text.append(text)
        doc.close()
        return "\n\n".join(full_text)
    except Exception as e:
        return f"[Error reading {pdf_path.name}: {e}]"


def _chunk_text(text: str, metadata: dict, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list:
    """Split text into overlapping chunks with metadata. Filters low-quality chunks."""
    chunks = []
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]{3,}', '  ', text)
    # Clean PDF artifacts
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)

    sentences = re.split(r'(?<=[.!?])\s+', text)
    current = ""
    for sent in sentences:
        if len(current) + len(sent) < chunk_size:
            current += sent + " "
        else:
            if current.strip() and _is_quality_chunk(current, metadata.get("type", "")):
                chunks.append({
                    "content": current.strip(),
                    "metadata": {**metadata, "chunk_length": len(current.strip())},
                })
            current = current[-overlap:] if len(current) > overlap else ""
            current += sent + " "
    if current.strip() and _is_quality_chunk(current, metadata.get("type", "")):
        chunks.append({
            "content": current.strip(),
            "metadata": {**metadata, "chunk_length": len(current.strip())},
        })
    return chunks


def _is_quality_chunk(text: str, paper_type: str = "") -> bool:
    """Filter low-quality chunks: too short, mark-scheme-only codes, garbled text."""
    # Minimum length
    if len(text) < 80:
        return False
    # For mark schemes: filter annotation-heavy chunks
    if paper_type == "ms":
        code_lines = len(re.findall(r'(?:^|\s)[AMEBP]\d{1,2}\b', text))
        mark_lines = len(re.findall(r'\[\d+\]', text))
        alpha_ratio = sum(1 for c in text if c.isalpha()) / max(len(text), 1)
        garbage_ratio = sum(1 for c in text if c in '\b') / max(len(text), 1)
        # Reject if: too many scoring codes, too little alpha, garbled
        if alpha_ratio < 0.40 or garbage_ratio > 0.01:
            return False
        if (code_lines + mark_lines) > 3 and alpha_ratio < 0.60:
            return False
    # Too much whitespace or non-printable chars
    printable_ratio = sum(1 for c in text if c.isprintable() or c in '\n\t ') / max(len(text), 1)
    if printable_ratio < 0.85:
        return False
    if len(text.strip()) / max(len(text), 1) < 0.3:
        return False
    return True


def build_textbook_kb(subject_code: Optional[str] = None):
    """Index textbook PDFs into ChromaDB."""
    client = _get_client()
    embedding_fn = _get_embedding_fn()

    # Get or create collection
    try:
        client.delete_collection("textbooks")
    except Exception:
        pass

    collection = client.create_collection(
        name="textbooks",
        embedding_function=embedding_fn,
        metadata={"description": "Cambridge A-Level textbook content"},
    )

    subject_map = {
        "9701_chemistry": "9701",
        "9702_physics": "9702",
        "9708_economics": "9708",
        "9709_mathematics": "9709",
    }

    total_chunks = 0
    for subj_dir in TEXTBOOK_DIR.iterdir():
        if not subj_dir.is_dir():
            continue
        subj_code = subject_map.get(subj_dir.name, subj_dir.name[:4])
        if subject_code and subj_code != subject_code:
            continue

        for pdf_file in subj_dir.glob("*.pdf"):
            if pdf_file.stat().st_size < 50000:
                continue

            console.print(f"  [cyan]Processing: {pdf_file.name}[/cyan]")
            text = _extract_text_from_pdf(pdf_file)
            if text.startswith("[PDF:") or text.startswith("[Error"):
                console.print(f"    [yellow]Skipping (no extraction): {text[:80]}[/yellow]")
                continue

            metadata = {
                "subject": subj_code,
                "filename": pdf_file.name,
                "source": "textbook",
                "directory": subj_dir.name,
            }

            chunks = _chunk_text(text, metadata)
            for i, chunk in enumerate(chunks):
                chunk_id = f"{subj_code}_{pdf_file.stem}_{i}"
                collection.add(
                    ids=[chunk_id],
                    documents=[chunk["content"]],
                    metadatas=[chunk["metadata"]],
                )
                total_chunks += 1

            console.print(f"    [green]Indexed {len(chunks)} chunks[/green]")

    console.print(f"\n[bold green]Textbook KB built: {total_chunks} chunks total[/bold green]")
    return total_chunks


def build_paper_kb(max_per_type: int = 10):
    """Index past paper content into ChromaDB (balanced across qp/ms/er/gt/ci types).
    
    Args:
        max_per_type: max PDFs per paper type per subject (e.g. 10 qp + 10 ms = 20 per subject)
    """
    client = _get_client()
    embedding_fn = _get_embedding_fn()

    try:
        client.delete_collection("past_papers")
    except Exception:
        pass

    collection = client.create_collection(
        name="past_papers",
        embedding_function=embedding_fn,
        metadata={"description": "Cambridge A-Level past paper content"},
    )

    manifest_path = PAPERS_DIR / "manifest.json"
    if not manifest_path.exists():
        console.print("[yellow]No manifest found. Build past papers first.[/yellow]")
        return 0

    with open(manifest_path) as f:
        manifest = json.load(f)

    total_chunks = 0
    for code, info in manifest.items():
        subject_dir = PAPERS_DIR / f"{code}_{info['name'].lower()}"
        if not subject_dir.exists():
            continue

        # Count per type, not total — ensures qp, ms, er all get indexed
        type_counts = {}
        paper_count = 0

        for year_dir in sorted(subject_dir.iterdir(), reverse=True):
            if not year_dir.is_dir():
                continue
            for type_dir in year_dir.iterdir():
                if not type_dir.is_dir():
                    continue
                type_name = type_dir.name
                if type_name not in type_counts:
                    type_counts[type_name] = 0

                for pdf_file in type_dir.glob("*.pdf"):
                    if type_counts[type_name] >= max_per_type:
                        break
                    if pdf_file.stat().st_size < 10000:
                        continue

                    text = _extract_text_from_pdf(pdf_file)
                    if not text or text.startswith("[PDF:") or text.startswith("[Error"):
                        continue

                    metadata = {
                        "subject": code,
                        "year": year_dir.name,
                        "type": type_dir.name,
                        "filename": pdf_file.name,
                        "source": "past_paper",
                    }

                    chunks = _chunk_text(text, metadata, chunk_size=600)
                    for i, chunk in enumerate(chunks):
                        chunk_id = f"{code}_{year_dir.name}_{type_dir.name}_{pdf_file.stem}_{i}"
                        collection.add(
                            ids=[chunk_id],
                            documents=[chunk["content"]],
                            metadatas=[chunk["metadata"]],
                        )
                        total_chunks += 1

                    type_counts[type_name] += 1
                    paper_count += 1
                    if total_chunks % 100 == 0:
                        console.print(f"  [dim]...{total_chunks} chunks indexed[/dim]")

            if all(v >= max_per_type for v in type_counts.values()) and len(type_counts) >= 3:
                break

        type_breakdown = ", ".join(f"{t}:{c}" for t, c in sorted(type_counts.items()))
        console.print(f"  [green]{code}: {paper_count} papers ({type_breakdown})[/green]")

    console.print(f"\n[bold green]Past Paper KB built: {total_chunks} chunks total[/bold green]")
    return total_chunks


def build_technique_kb():
    """Index study guides (markdown + techniques) into ChromaDB."""
    client = _get_client()
    embedding_fn = _get_embedding_fn()

    try:
        client.delete_collection("techniques")
    except Exception:
        pass

    collection = client.create_collection(
        name="techniques",
        embedding_function=embedding_fn,
        metadata={"description": "Exam technique guides and patterns"},
    )

    total = 0
    for md_file in GUIDES_DIR.glob("*.md"):
        if md_file.name == "index.md":
            continue
        text = md_file.read_text()
        subject_code = md_file.stem.replace(".md", "")
        if "_" in subject_code:
            subject_code = subject_code.split("_")[0]

        metadata = {
            "subject": subject_code,
            "filename": md_file.name,
            "source": "study_guide",
        }

        chunks = _chunk_text(text, metadata, chunk_size=600)
        for i, chunk in enumerate(chunks):
            chunk_id = f"guide_{md_file.stem}_{i}"
            collection.add(
                ids=[chunk_id],
                documents=[chunk["content"]],
                metadatas=[chunk["metadata"]],
            )
            total += 1

    console.print(f"[green]Techniques KB built: {total} chunks[/green]")
    return total


def build_all(subject_code: Optional[str] = None, max_per_type: int = 10):
    """Build all knowledge bases."""
    console.print("[bold]Building Knowledge Bases...[/bold]\n")
    console.print("[cyan]1/3[/cyan] Indexing textbooks...")
    tb = build_textbook_kb(subject_code)
    console.print("\n[cyan]2/3[/cyan] Indexing past papers (balanced: qp/ms/er/gt)...")
    pp = build_paper_kb(max_per_type)
    console.print("\n[cyan]3/3[/cyan] Indexing exam techniques...")
    te = build_technique_kb()
    console.print(f"\n[bold green]Done! {tb} textbook + {pp} paper + {te} technique chunks indexed.[/bold green]")
