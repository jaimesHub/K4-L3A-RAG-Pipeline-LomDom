# Chatbot pháp lý - Hợp đồng mua bán căn hộ (mục 9)

**UI thay thế** cho `app.py` (Streamlit). `chatbot/` chỉ là một trang HTML
tĩnh (`chatbot/static/index.html`, thuần HTML/CSS/JS, không cần build) phục
vụ bởi một server Python nhỏ dùng `http.server` có sẵn trong thư viện
chuẩn — `app.py` vẫn là sản phẩm chính theo spec, không bị thay thế.

`chatbot/` **không còn engine retrieval riêng**. `chatbot/engine.py` giờ là
một adapter mỏng gọi thẳng pipeline `src/task5-10` — cùng pipeline đã qua
15/15 contract test (`tests/test_contracts.py`) và cùng pipeline `app.py`
dùng:

- `src.task9_retrieval_pipeline.retrieve()` cho dense/hybrid retrieval
  (kèm PageIndex fallback khi dưới ngưỡng score), và
- `src.task10_generation.{reorder_for_llm, format_context, call_llm,
  SYSTEM_PROMPT}` cho sinh câu trả lời có trích dẫn.

`src.task10_generation.generate_with_citation()` không nhận tham số
`use_hybrid`, nhưng UI có toggle Dense-only / Hybrid+RRF (phép A/B mà
`docs/STEP_BY_STEP.md` yêu cầu), nên `chatbot/engine.py` tự compose lại
`retrieve()` + `reorder_for_llm()` + `format_context()` + `call_llm()` (tất
cả import từ `src/`, không viết lại logic) để `use_hybrid` được truyền
xuống `retrieve(use_reranking=...)`.

Trước đây `chatbot/engine.py` là một pipeline TF-IDF + BM25 độc lập
(`chatbot/corpus.py` tự chunk, tự build embedding cache) không đụng
ChromaDB. Pipeline đó đã bị gỡ khỏi `engine.py`; `chatbot/corpus.py` và
`chatbot/llm.py` vẫn còn trong repo nhưng không còn được `engine.py` dùng
nữa.

## Điều kiện để chạy

Vì giờ dùng chung pipeline với `app.py`, cần:

1. `chroma_db/` đã được index bằng `python -m src.task4_chunking_indexing`
   (chạy riêng, **không** chạy kèm chatbot — xem lưu ý bên dưới).
2. `.env` có `LLM_PROVIDER` + API key tương ứng (`OPENAI_API_KEY` /
   `GEMINI_API_KEY` / `ANTHROPIC_API_KEY`).

Nếu `chroma_db/` chưa có hoặc rỗng, `/api/health` vẫn trả 200 nhưng
`engine.warm_up()` báo `chunks: null` kèm `error` thay vì làm server crash;
`/api/chat` sẽ trả list rỗng / safe refusal cho tới khi index sẵn sàng.

## Chạy chatbot

```bash
# Trong venv của repo (đã có sẵn các dependency cần thiết)
python -m pip install -e ".[dev]"   # lần đầu
cp .env.example .env                # điền LLM_PROVIDER + API key tương ứng
python -m src.task4_chunking_indexing   # chỉ cần chạy 1 lần / khi corpus đổi
python -m chatbot.server
```

Server in ra URL (mặc định `http://127.0.0.1:8000`) và tự mở trình duyệt.

Nếu chưa điền API key cho `LLM_PROVIDER` trong `.env`, `call_llm()` sẽ lỗi
nhưng không làm request crash - chatbot trả lại một câu trả lời báo lỗi rõ
ràng kèm các đoạn trích dẫn liên quan tìm được (phần retrieval vẫn hoạt
động độc lập với LLM).

## Đánh giá (evaluation)

`group_project/evaluation/run_evaluation.py` vẫn `import chatbot.engine`
và gọi `engine.generate_with_citation(question, top_k=..., use_hybrid=...)`
+ đọc `engine.config.*` — các tên này được giữ nguyên trong lần rewire này
nên script đó không bị vỡ. Chi tiết cách chạy: xem docstring đầu file
`group_project/evaluation/run_evaluation.py`.
