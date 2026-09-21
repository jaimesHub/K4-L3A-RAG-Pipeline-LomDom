import os

import streamlit as st
from dotenv import load_dotenv

from src.task9_retrieval_pipeline import DEFAULT_TOP_K, SCORE_THRESHOLD
from src.task10_generation import generate_with_citation


load_dotenv()

st.set_page_config(
    page_title="RAG Chatbot",
    page_icon="",
    layout="wide",
)

# Nhãn hiển thị cho retrieval_source (cấp câu trả lời) theo GenerationResult.
RETRIEVAL_SOURCE_LABELS = {
    "hybrid": "Hybrid (Dense + BM25 + RRF)",
    "pageindex": "PageIndex fallback",
    "none": "Không có nguồn (safe refusal)",
}


@st.cache_resource(show_spinner="Đang tải pipeline RAG (lần đầu sẽ tải model embedding BAAI/bge-m3 ~2GB, có thể mất vài phút)...")
def get_generation_fn():
    """Cache tham chiếu tới generate_with_citation.

    Streamlit chạy lại toàn bộ script sau mỗi tương tác của người dùng. Model
    embedding BAAI/bge-m3 (~2GB) đã được cache ở cấp module trong
    src/task4_chunking_indexing.py (biến _sentence_transformer_model), nhưng
    vẫn cache thêm ở đây bằng st.cache_resource để đảm bảo pipeline chỉ được
    chuẩn bị một lần cho cả session, tránh treo UI khi rerun.
    """
    return generate_with_citation


def render_sources(sources: list[dict]) -> None:
    """Hiển thị danh sách SearchResult: title, source, score, retrieval_method, snippet."""
    st.markdown(f"**Nguồn trích dẫn ({len(sources)}):**")
    for index, item in enumerate(sources, start=1):
        metadata = item.get("metadata", {})
        title = metadata.get("title") or "(không rõ tiêu đề)"
        source_name = metadata.get("source") or "(không rõ tệp nguồn)"
        url = metadata.get("url")
        score = item.get("score")
        score_text = f"{score:.3f}" if isinstance(score, (int, float)) else "N/A"
        method = item.get("retrieval_method", "N/A")
        content = item.get("content", "")
        snippet = content[:400] + ("…" if len(content) > 400 else "")

        with st.expander(f"[{index}] {title} · score={score_text} · {method}"):
            if url:
                st.markdown(f"- **Tệp nguồn:** {source_name}")
                st.markdown(f"- **URL:** [{url}]({url})")
            else:
                st.markdown(f"- **Tệp nguồn:** {source_name} (không có URL)")
            st.markdown(f"- **Phương thức truy hồi (chunk):** `{method}`")
            st.markdown(f"- **Score:** `{score_text}`")
            st.markdown(f"> {snippet}")


def render_assistant_turn(answer: str, sources: list[dict], retrieval_source: str) -> None:
    """Hiển thị answer, retrieval method (cấp câu trả lời) và sources.

    Nếu retrieval_source == "none" hoặc sources rỗng, hiển thị cảnh báo safe
    refusal rõ ràng thay vì một bảng nguồn trống gây khó hiểu.
    """
    st.markdown(answer)

    if retrieval_source == "none" or not sources:
        st.warning(
            "Không tìm thấy nguồn phù hợp trong corpus hiện có — đây là câu trả lời "
            "từ chối an toàn (safe refusal), không phải lỗi hệ thống."
        )
        return

    label = RETRIEVAL_SOURCE_LABELS.get(retrieval_source, retrieval_source)
    st.caption(f"Retrieval method (cấp câu trả lời): **{label}**")
    render_sources(sources)


if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("RAG Chatbot")
    st.caption("Thay mô tả theo đề tài của nhóm")
    top_k = st.slider("Số chunks (top_k)", 3, 10, DEFAULT_TOP_K)
    st.caption(
        f"Ngưỡng fallback PageIndex hiện tại (SCORE_THRESHOLD trong "
        f"src/task9_retrieval_pipeline.py): `{SCORE_THRESHOLD}`. Không chỉnh được "
        "từ UI vì generate_with_citation() chỉ nhận tham số top_k."
    )
    st.caption(f"LLM_PROVIDER hiện tại: `{os.getenv('LLM_PROVIDER', 'openai')}`")

st.title("RAG Chatbot")
st.caption("Thay tiêu đề và hướng dẫn sử dụng")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            render_assistant_turn(
                message["content"],
                message.get("sources", []),
                message.get("retrieval_source", "none"),
            )
        else:
            st.markdown(message["content"])

query = st.chat_input("Nhập câu hỏi...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        result = None
        try:
            with st.spinner("Đang truy hồi và sinh câu trả lời..."):
                generate_fn = get_generation_fn()
                result = generate_fn(query, top_k=top_k)
        except RuntimeError as exc:
            # RuntimeError được raise tường minh khi thiếu API key (embedding
            # provider hoặc LLM provider) — hiện rõ cần điền gì vào .env.
            st.error(
                "Thiếu cấu hình provider trong `.env`: "
                f"{exc}\n\n"
                "Kiểm tra các biến `LLM_PROVIDER`, `EMBEDDING_PROVIDER` và API key "
                "tương ứng (`OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`)."
            )
        except ValueError as exc:
            # ValueError khi LLM_PROVIDER/EMBEDDING_PROVIDER trong .env không hợp lệ.
            st.error(f"Cấu hình provider không hợp lệ trong `.env`: {exc}")
        except Exception as exc:
            # Bọc mọi lỗi khác (retrieval, ChromaDB, network...) để không làm crash UI.
            st.error(f"Đã xảy ra lỗi không mong muốn khi sinh câu trả lời: {exc}")

        if result is not None:
            answer = result.get("answer", "")
            sources = result.get("sources", [])
            retrieval_source = result.get("retrieval_source", "none")

            render_assistant_turn(answer, sources, retrieval_source)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                    "retrieval_source": retrieval_source,
                }
            )
