"""
Retriever module: ChromaDB vector search with subject/type filtering.
"""
import json
from pathlib import Path
from typing import List, Optional

from agent.config import CHROMA_DIR, PAPERS_DIR, TEXTBOOK_DIR

_RESULTS_CACHE: dict = {}

try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMA = True
except ImportError:
    HAS_CHROMA = False


def _get_or_create_db():
    if not HAS_CHROMA:
        raise ImportError("chromadb not installed. Run: pip install chromadb")
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client


_QUERY_EMBED_FN = None


def _get_query_embed_fn():
    """Get Ollama embedding function for search queries — matches builder."""
    global _QUERY_EMBED_FN
    if _QUERY_EMBED_FN is not None:
        return _QUERY_EMBED_FN
    try:
        import requests as _req
        _resp = _req.get("http://localhost:11434/api/tags", timeout=3)
        if _resp.status_code == 200:
            models = [m["name"] for m in _resp.json().get("models", [])]
            emb_models = [m for m in models if "embed" in m.lower()]
            if emb_models:
                from agent.retrieval.builder import OllamaEmbedFn
                emb_models.sort(key=lambda x: float(x.split(":")[-1].replace("b","")) if ":" in x else 999)
                _QUERY_EMBED_FN = OllamaEmbedFn(model_name=emb_models[0])
    except Exception:
        pass
    return _QUERY_EMBED_FN


def _query_with_ollama(collection, query: str, n_results: int, where_filter=None, include=None):
    """Query using Ollama embeddings directly — avoids ChromaDB's stored embedding fn."""
    ef = _get_query_embed_fn()
    if ef and include is None:
        include = ["documents", "metadatas", "distances"]
    if ef:
        emb = ef([query])[0]
        return collection.query(
            query_embeddings=[emb], n_results=n_results,
            where=where_filter, include=include,
        )
    return collection.query(
        query_texts=[query], n_results=n_results,
        where=where_filter, include=include,
    )


def search_textbooks(query: str, subject_code: Optional[str] = None, n_results: int = 5, use_rerank: bool = False) -> list:
    """Search textbook content by semantic similarity. Optionally rerank for precision."""
    client = _get_or_create_db()
    try:
        collection = client.get_collection("textbooks")
    except Exception:
        return _fallback_textbook_search(query, subject_code)

    where_filter = None
    if subject_code:
        where_filter = {"subject": subject_code}

    results = _query_with_ollama(collection, query, n_results * 2, where_filter)
    formatted = _format_results(results, "textbooks")
    
    if use_rerank and formatted and len(formatted) > 1:
        from agent.retrieval.reranker import rerank
        formatted = rerank(query, formatted, top_n=n_results)
    else:
        formatted = formatted[:n_results]
    
    return formatted


def search_past_papers(
    query: str,
    subject_code: Optional[str] = None,
    paper_type: Optional[str] = None,
    topic: Optional[str] = None,
    n_results: int = 5,
    use_rerank: bool = False,
) -> list:
    """Search past paper questions and mark schemes. Optionally rerank for precision."""
    client = _get_or_create_db()
    try:
        collection = client.get_collection("past_papers")
    except Exception:
        return _fallback_paper_search(query, subject_code)

    where_filter = {}
    if subject_code:
        where_filter["subject"] = subject_code
    if paper_type:
        where_filter["type"] = paper_type
    if topic:
        where_filter["topic"] = topic
    if not where_filter:
        where_filter = None
    elif len(where_filter) > 1:
        # ChromaDB requires $and for multiple filter operators
        where_filter = {"$and": [{k: v} for k, v in where_filter.items()]}

    results = _query_with_ollama(collection, query, n_results * 2, where_filter)
    formatted = _format_results(results, "past_papers")
    if use_rerank and formatted and len(formatted) > 1:
        from agent.retrieval.reranker import rerank
        formatted = rerank(query, formatted, top_n=n_results)
    else:
        formatted = formatted[:n_results]
    return formatted


def search_all(
    query: str,
    subject_code: Optional[str] = None,
    n_results: int = 5,
) -> dict:
    """Search across all collections."""
    result = {}
    result["textbooks"] = search_textbooks(query, subject_code, n_results)
    result["past_papers"] = search_past_papers(query, subject_code, n_results=n_results)
    return result


def _format_results(chroma_results, source: str) -> list:
    if not chroma_results or not chroma_results.get("ids"):
        return []
    output = []
    ids_list = chroma_results["ids"]
    docs_list = chroma_results["documents"] or []
    metas_list = chroma_results["metadatas"] or []
    dists_list = chroma_results.get("distances") or []

    for i in range(len(ids_list[0]) if ids_list else 0):
        chunk = {
            "id": ids_list[0][i],
            "content": docs_list[0][i] if docs_list and docs_list[0] else "",
            "metadata": metas_list[0][i] if metas_list and metas_list[0] else {},
            "distance": dists_list[0][i] if dists_list and dists_list[0] else 0,
            "source": source,
        }
        output.append(chunk)
    return output


# ── Fallback: keyword search in manifest/manual data if chroma not built ──

def _fallback_textbook_search(query: str, subject_code: Optional[str] = None) -> list:
    """Simple keyword search when vector DB not yet built."""
    cache_key = f"tb_{query}_{subject_code}"
    if cache_key in _RESULTS_CACHE:
        return _RESULTS_CACHE[cache_key]

    results = []
    # Check if textbooks exist
    for subj_dir in TEXTBOOK_DIR.iterdir():
        if not subj_dir.is_dir():
            continue
        if subject_code and subject_code not in subj_dir.name:
            continue
        for pdf_file in subj_dir.glob("*.pdf"):
            if pdf_file.stat().st_size < 50000:
                continue
            results.append({
                "id": pdf_file.stem,
                "content": f"教材: {pdf_file.name} (请先构建向量数据库以获得全文搜索能力)",
                "metadata": {"subject": subject_code or subj_dir.name[:4], "filename": pdf_file.name},
                "distance": 0.5,
                "source": "textbooks",
            })

    _RESULTS_CACHE[cache_key] = results[:5]
    return results[:5]


def _fallback_paper_search(query: str, subject_code: Optional[str] = None) -> list:
    """Search paper manifest or file listing."""
    results = []
    manifest_path = PAPERS_DIR / "manifest.json"
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = json.load(f)

    for code, info in manifest.items():
        if subject_code and code != subject_code:
            continue
        keywords = query.lower().split()
        # Simple keyword match in years/types
        for year in info.get("years", [])[-3:]:  # recent 3 years
            for ptype, files in info.get("files", {}).get(year, {}).items():
                for fname in files:
                    if any(kw in fname.lower() for kw in keywords):
                        results.append({
                            "id": f"{code}_{year}_{ptype}",
                            "content": f"试卷: {fname} (Year: {year}, Type: {ptype})",
                            "metadata": {"subject": code, "year": year, "type": ptype, "filename": fname},
                            "distance": 0.3,
                            "source": "past_papers",
                        })

    return results[:5]


def get_collection_stats() -> dict:
    """Return statistics about the vector database."""
    stats = {}
    try:
        client = _get_or_create_db()
        for name in ["textbooks", "past_papers", "techniques"]:
            try:
                col = client.get_collection(name)
                stats[name] = {"count": col.count()}
            except Exception:
                stats[name] = {"count": 0}
    except Exception:
        stats = {"textbooks": {"count": 0}, "past_papers": {"count": 0}, "techniques": {"count": 0}}
    return stats


def search_techniques(query: str, subject_code: str = None, n_results: int = 3) -> list:
    """Search exam techniques and study guides."""
    client = _get_or_create_db()
    try:
        collection = client.get_collection("techniques")
    except Exception:
        return []

    where_filter = None
    if subject_code:
        where_filter = {"subject": subject_code}

    results = _query_with_ollama(collection, query, n_results, where_filter)
    return _format_results(results, "techniques")
