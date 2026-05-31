"""
Reranker module: second-stage relevance scoring using Qwen3-Reranker-0.6B.
Takes top-K results from embedding search → re-scores with cross-encoder → returns top-N.

Architecture: embedding (Ollama, fast) → ChromaDB (top-K) → Reranker (accurate) → LLM
The reranker compensates for weak embeddings with precise query-document scoring.
"""
import time

from rich.console import Console

console = Console()

_reranker = None
_reranker_loaded = False


def _load_reranker():
    """Lazy-load Qwen3-Reranker-0.6B. Tries ModelScope cache, then HF, then HF mirror."""
    global _reranker, _reranker_loaded
    if _reranker_loaded:
        return _reranker
    _reranker_loaded = True
    try:
        from sentence_transformers import CrossEncoder
        import os

        # Try ModelScope cache first (downloaded via modelscope)
        ms_cache = os.path.expanduser(
            "~/.cache/modelscope/hub/models/Qwen/Qwen3-Reranker-0___6B"
        )
        model_path = None
        if os.path.isdir(ms_cache) and os.path.exists(os.path.join(ms_cache, "model.safetensors")):
            model_path = ms_cache
            console.print(f"[dim]Loading from ModelScope cache: {model_path}[/dim]")
        else:
            model_path = "Qwen/Qwen3-Reranker-0.6B"
            console.print("[dim]Loading Qwen3-Reranker-0.6B from HF (first time, ~1.2GB)...[/dim]")

        t0 = time.time()
        _reranker = CrossEncoder(
            model_path,
            trust_remote_code=True,
            local_files_only=model_path != "Qwen/Qwen3-Reranker-0.6B",
        )
        # Fix missing pad token (required for batch prediction)
        if _reranker.tokenizer.pad_token is None:
            _reranker.tokenizer.pad_token = _reranker.tokenizer.eos_token
        console.print(f"[dim]Reranker loaded in {time.time()-t0:.0f}s[/dim]")
        return _reranker
    except ImportError:
        console.print("[yellow]sentence-transformers not installed. pip install sentence-transformers[/yellow]")
    except Exception as e:
        console.print(f"[yellow]Reranker load failed: {e}[/yellow]")
    return None


def rerank(query: str, documents: list, top_n: int = 3) -> list:
    """Rerank documents by cross-encoder relevance to query.

    Args:
        query: User's question
        documents: List of dicts with 'content' and 'metadata' keys
        top_n: Number of results to return after reranking

    Returns:
        Reranked list of dicts with added 'rerank_score' field
    """
    model = _load_reranker()
    if model is None:
        return documents[:top_n]

    if not documents:
        return []

    # Create query-document pairs
    pairs = [(query, doc["content"][:2000]) for doc in documents]

    try:
        scores = model.predict(pairs, show_progress_bar=False, batch_size=1)
        for doc, score in zip(documents, scores):
            doc["rerank_score"] = float(score)
        # Sort by score descending (higher = more relevant)
        documents.sort(key=lambda x: x.get("rerank_score", -999), reverse=True)
        return documents[:top_n]
    except Exception as e:
        console.print(f"[dim]Rerank failed: {e}, returning unranked top-{top_n}[/dim]")
        return documents[:top_n]


def is_available() -> bool:
    """Check if reranker can be loaded."""
    return _load_reranker() is not None
