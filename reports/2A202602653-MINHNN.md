# Individual contribution report

---

## Thông tin

- Họ và tên: Nguyễn Ngọc Minh
- Nhóm: LomDom
- Repository/branch: minhnn

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File | Trạng thái |
|---|---|---|---|
| task1 — collect_legal_documents() | Thêm hàm trả `list[Document]` đúng contract, metadata đầy đủ cho 4 file pháp luật BĐS | `src/task1_collect_legal_docs.py` | Done |
| task5 — semantic_search() | Query ChromaDB bằng `embed_texts()` chung từ task4, `score = 1 - cosine_distance`, sort giảm dần | `src/task5_semantic_search.py` | Done |
| task6 — lexical_search() | BM25Plus (thay BM25Okapi tránh IDF âm), lazy-load CORPUS qua `sys.modules` để monkeypatch test hoạt động | `src/task6_lexical_search.py` | Done |
| task7 — rerank_rrf() | RRF `sum(1/(k+rank))` rank từ 1, deduplicate theo id, `retrieval_method="hybrid"` | `src/task7_reranking.py` | Done |
| task8 — pageindex fallback | Upload PDF lên PageIndex Cloud REST API, cache doc_id, gọi Chat API, parse thành SearchResult; graceful fail khi thiếu API key | `src/task8_pageindex_vectorless.py` | Done |
| task9 — retrieve() | Dense + BM25 × top_k×2, RRF fuse 1 lần, fallback dùng `dense[0]["score"]` (cosine gốc, không phải RRF score) | `src/task9_retrieval_pipeline.py` | Done |
| task10 — generate_with_citation() | `reorder_for_llm` non-mutating, `format_context` có title+source, dispatch openai/gemini/anthropic, safe refusal, fix bug citation lệch thứ tự (`sources: reordered`) | `src/task10_generation.py` | Done |
| CHECKLIST.md | Cập nhật trạng thái toàn bộ pipeline sau khi implement | `CHECKLIST.md` | Done |

## Quyết định kỹ thuật quan trọng

1. **Dùng BM25Plus thay BM25Okapi**
   **Lý do:** BM25Okapi sinh IDF âm khi term xuất hiện trong hầu hết corpus — với corpus nhỏ (2 docs trong test) score của doc không liên quan cao hơn doc liên quan, khiến `test_lexical_search_returns_bm25_contract` fail. BM25Plus đảm bảo IDF ≥ 0, docs không chứa query term luôn score = 0.
   **Trade-off:** BM25Plus tính toán nặng hơn nhẹ so với Okapi, không đáng kể trên corpus ~2000 chunk.

2. **Fallback threshold dùng cosine score gốc của dense, không dùng RRF score**
   **Lý do:** RRF score (~0.016–0.033) và cosine score (0.3–0.9) hoàn toàn khác thang đo — nếu so threshold với RRF score thì fallback sẽ kích hoạt 100% thời gian (vì mọi RRF score đều nhỏ hơn threshold hợp lý 0.3). Contract test `test_retrieve_uses_dense_score_for_fallback` và `test_retrieve_fuses_once_when_dense_is_confident` xác minh điều này.
   **Trade-off:** Phải giữ riêng biến `dense` trước khi fuse để lấy score gốc — tăng một chút độ phức tạp code nhưng logic đúng hơn.

## Kiểm thử và kết quả

- Chạy `pytest tests/test_contracts.py -q`: **15/15 PASS** sau khi implement xong
- Query in-domain "Điều kiện chuyển nhượng hợp đồng mua bán căn hộ chung cư": dense[0].score = 0.737, BM25 trả đúng chunk từ mau-so-1a.md, hybrid RRF hợp nhất đúng thứ tự
- Query out-of-domain "Công thức nấu phở bò": dense[0].score = 0.380 > threshold 0.3 → không kích hoạt fallback, trả hybrid (đúng hành vi vì không có PageIndex key)
- Fix bug citation: `reorder_for_llm([c0,c1,c2,c3,c4])` → `[c0,c2,c4,c3,c1]`, 3/5 vị trí lệch nếu dùng `sources: chunks` thay vì `sources: reordered`

## Điều còn hạn chế

- `SCORE_THRESHOLD = 0.3` chưa được calibrate chính thức trên corpus thật — dữ liệu thực tế cho thấy nên nâng lên 0.38–0.45 để phân biệt rõ hơn in-domain vs out-of-domain
- `PAGEINDEX_API_KEY` chưa điền nên fallback chưa được test end-to-end thật; pipeline graceful fail nhưng tính năng này chưa verify được hoàn toàn
- Nếu có thêm thời gian: calibrate threshold và test pageindex fallback với API key thật

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 2026-09-21
- Tên thành viên: Nguyễn Ngọc Minh
