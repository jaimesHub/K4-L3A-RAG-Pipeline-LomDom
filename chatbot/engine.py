"""Adapter that wires the chatbot UI to the src/task5-10 RAG pipeline.

This used to be a self-contained TF-IDF/BM25 engine (own embedding cache,
its own hybrid RRF, its own citation generation) that never touched
ChromaDB or the src/task5-10 exercises. That meant the UI in
chatbot/static/index.html never exercised the pipeline that actually
passes docs/MODULE_CONTRACTS.md's 15/15 contract tests.

This module now composes the already contract-tested building blocks from
src/ instead of reimplementing retrieval or generation:

    - src.task9_retrieval_pipeline.retrieve() for dense/hybrid retrieval
      (with PageIndex fallback under the score threshold), and
    - src.task10_generation.{reorder_for_llm, format_context, call_llm,
      SYSTEM_PROMPT} for citation-grounded generation.

src.task10_generation.generate_with_citation() itself does not accept a
use_hybrid flag (it always calls retrieve() with its default
use_reranking=True). chatbot/static/index.html has a Dense-only /
Hybrid+RRF toggle, which is the retrieval A/B comparison
docs/STEP_BY_STEP.md asks for, so it must stay wired up. generate_with_citation()
below therefore re-composes retrieve() + reorder_for_llm() + format_context()
+ call_llm() itself (all imported from src/, none reimplemented) so that
use_hybrid can be threaded through to retrieve(use_reranking=...).

`config` is imported and re-exported here (as `engine.config`) because
group_project/evaluation/run_evaluation.py reads
`engine.config.LLM_PROVIDER` / `LLM_MODEL` / `DEFAULT_MODELS` /
`EMBEDDING_MODEL` — do not remove this import without checking that file.
"""

from . import config
from src.task9_retrieval_pipeline import retrieve
from src.task10_generation import SYSTEM_PROMPT, call_llm, format_context, reorder_for_llm


def warm_up() -> dict:
    """Report ChromaDB readiness for /api/health and server startup.

    Unlike the old TF-IDF engine, the src/ pipeline reads from an
    already-populated ChromaDB collection (built by running
    `python -m src.task4_chunking_indexing` separately), so there is no
    index to build here — this just confirms the collection is reachable
    and reports its size. Never raises: callers (server.py's /api/health
    and startup banner) should not crash just because ChromaDB isn't
    indexed yet.
    """
    try:
        from src.task4_chunking_indexing import COLLECTION_NAME, get_collection

        collection = get_collection()
        return {"chunks": collection.count(), "collection": COLLECTION_NAME}
    except Exception as error:  # noqa: BLE001
        return {"chunks": None, "collection": None, "error": str(error)}


def generate_with_citation(
    question: str, top_k: int = config.TOP_K, use_hybrid: bool = True
) -> dict:
    """Retrieve + generate a cited answer for `question`.

    Composes src.task9_retrieval_pipeline.retrieve() (with use_reranking
    driven by the UI's use_hybrid toggle) and the same
    src.task10_generation building blocks
    (reorder_for_llm/format_context/call_llm/SYSTEM_PROMPT) that
    src.task10_generation.generate_with_citation() itself uses — just with
    use_hybrid threaded through. Returns a GenerationResult-shaped dict
    (see src/contracts.py).

    "sources" is the *reordered* list, not the raw retrieved chunks:
    format_context() numbers "[Document N]" against `reordered`, so
    citations only map back to the right source if `sources` is that same
    list/order (this mirrors the citation-order fix in
    src/task10_generation.py).

    Also includes a "retrieval_method" alias of "retrieval_source" for
    backward compatibility with group_project/evaluation/run_evaluation.py,
    which reads `result["retrieval_method"]` directly.
    """
    chunks = retrieve(question, top_k=top_k, use_reranking=use_hybrid)

    if not chunks:
        return {
            "answer": "Tôi không thể xác minh thông tin này từ nguồn hiện có.",
            "sources": [],
            "retrieval_source": "none",
            "retrieval_method": "none",
        }

    reordered = reorder_for_llm(chunks)
    context = format_context(reordered)
    user_message = f"Context:\n{context}\n\nCâu hỏi: {question}"

    try:
        answer = call_llm(SYSTEM_PROMPT, user_message)
    except Exception as error:  # noqa: BLE001
        answer = (
            f"(Chưa thể gọi mô hình sinh câu trả lời: {error}. "
            "Dưới đây là các đoạn trích dẫn liên quan nhất tìm được trong "
            "kho dữ liệu để bạn tham khảo trực tiếp.)"
        )

    if not answer.strip():
        answer = "Tôi không thể xác minh thông tin này từ nguồn hiện có."

    retrieval_source = reordered[0].get("retrieval_method", "hybrid")
    if retrieval_source not in ("hybrid", "pageindex"):
        retrieval_source = "hybrid"

    return {
        "answer": answer,
        "sources": reordered,
        "retrieval_source": retrieval_source,
        "retrieval_method": retrieval_source,
    }


if __name__ == "__main__":
    import json

    result = generate_with_citation("Hợp đồng mua bán căn hộ có bắt buộc công chứng không?")
    print(json.dumps({**result, "sources": len(result["sources"])}, ensure_ascii=False, indent=2))
