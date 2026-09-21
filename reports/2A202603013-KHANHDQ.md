# Individual contribution report

---

## Thông tin

- Họ và tên: Dương Quốc Khánh
- Nhóm: LomDom
- Repository/branch: khanhdq-integration

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File | Trạng thái |
|---|---|---|---|
| task1 — thu thập legal docs | Tải thủ công 4 PDF/DOCX từ nguồn chính phủ; thay `bo-luat-dan-su.pdf` (PDF scan, 0 ký tự) bằng `luat_bao_ve_nguoi_tieu_dung_2023.pdf` | `src/task1_collect_legal_docs.py`, `data/landing/legal/` | Done |
| task2 — crawl news | Implement `crawl_article()` dùng `requests` + `markitdown`, điền 8 URL báo chính phủ về pháp luật BĐS; hash MD5 URL làm tên file để idempotent | `src/task2_crawl_news.py`, `data/landing/news/` (8 JSON) | Done |
| task3 — convert markdown | `convert_legal_docs()`: 4/4 PDF/DOCX → Markdown, guard <200 ký tự, idempotent; `convert_news_articles()`: 8/8 JSON → Markdown, không crash khi news/ rỗng | `src/task3_convert_markdown.py`, `data/standardized/` | Done |
| task4 — chunking & indexing | `load_documents()`, `chunk_documents()`, `embed_texts()` dispatch 3 provider, `embed_chunks()` batch 32, `index_to_vectorstore()` upsert; điền `DOCUMENT_TITLES` và `DOCUMENT_URLS` thật từ chinhphu.vn | `src/task4_chunking_indexing.py` | Done |
| ChromaDB index | Chạy pipeline lần 1 (legal, 1392 chunk) và lần 2 (legal+news, 2147 chunk) sau khi có news | `chroma_db/` | Done |
| pyproject.toml | Ghim version numpy<2, transformers<4.50, sentence-transformers<4, thêm markitdown[pdf,docx] để tránh xung đột torch/numpy trên macOS Intel | `pyproject.toml` | Done |

## Quyết định kỹ thuật quan trọng

1. **Thay `bo-luat-dan-su.pdf` bằng `luat_bao_ve_nguoi_tieu_dung_2023.pdf`**
   **Lý do:** `bo-luat-dan-su.pdf` nặng 6.7 MB nhưng convert ra 0 ký tự — PDF scan ảnh, markitdown không trích được text. Kiểm tra bằng cách đo `len(result.text_content)` sau convert.
   **Trade-off:** Mất Bộ luật Dân sự khỏi corpus; thay bằng Luật Bảo vệ NTD 2023 (623 KB, 111K ký tự) — vẫn đúng chủ đề pháp luật BĐS/hộ kinh doanh và có text layer đầy đủ.

2. **Dùng `requests` + `markitdown` thay vì Crawl4AI cho task2**
   **Lý do:** Crawl4AI yêu cầu playwright chromium và async; `requests` + `markitdown` đã là dependency trong pyproject.toml, không cài thêm gì, đủ cho các trang báo chính phủ không có JS rendering phức tạp.
   **Trade-off:** Một số trang có JS-heavy content có thể bị thiếu, nhưng 8/8 URL từ baochinhphu.vn và tuoitre.vn đều crawl thành công với requests thông thường.

## Kiểm thử và kết quả

- Chạy `python -m src.task3_convert_markdown`: 4/4 legal ✅, 8/8 news ✅, không file nào <200 ký tự
- Chạy `python -m src.task4_chunking_indexing` lần 1: 1392 chunk (4 legal docs)
- Chạy lại sau khi có news: 2147 chunk (4 legal + 8 news = 12 documents), upsert không nhân bản ✅
- `pytest tests/test_acceptance.py::test_corpus_has_required_legal_documents` PASS
- `pytest tests/test_acceptance.py::test_corpus_has_required_news_with_metadata` PASS
- `pytest tests/test_acceptance.py::test_standardized_output_covers_both_source_types` PASS

## Điều còn hạn chế

- `DOCUMENT_URLS` cho `mau-so-1a.md` vẫn là `None` — chưa tìm được URL chính thức xác minh được cho mẫu hợp đồng này; citation ở task10 sẽ không có link dẫn ngược cho file này
- Nếu có thêm thời gian: bổ sung OCR cho PDF scan (tesseract) để có thể dùng lại `bo-luat-dan-su.pdf` thay vì bỏ

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 2026-09-21
- Tên thành viên: Dương Quốc Khánh
