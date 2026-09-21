# RAG evaluation results

## Run information

| Field                              | Value |
| ----------------------------------- | ----- |
| Evaluation date                    | 2026-09-21 |
| Framework and version              | ragas |
| Evaluator model                    | gpt-4o-mini (OpenAI, LLM-as-judge) |
| Generator model                    | openai / gpt-4o-mini |
| Embedding model                    | sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (fastembed/ONNX) |
| Corpus version/commit              | data/standardized/legal (luat-nha-o, luat-kinh-doanh-bds, mau-so-1a) |
| Golden dataset size                | 20 |
| `top_k`                            | 5 |
| Fallback threshold and calibration | Không dùng fallback PageIndex trong bản demo này; chỉ so sánh dense-only và hybrid+RRF |

## Configurations

- **Config A — dense-only:** `chatbot.engine.retrieve(query, top_k=5, use_hybrid=False)` - chỉ dùng cosine similarity trên embedding.
- **Config B — hybrid + RRF:** `chatbot.engine.retrieve(query, top_k=5, use_hybrid=True)` - dense + BM25 gộp bằng RRF (k=60).

Hai cấu hình dùng chung golden dataset, generator, evaluator, prompt và `top_k`; chỉ khác retrieval strategy.

## Overall scores

| Metric            | Config A | Config B | Delta B−A |
| ----------------- | -------: | -------: | --------: |
| Faithfulness      | 0.685 | 0.794 | 0.109 |
| Answer relevance  | 0.476 | 0.433 | -0.043 |
| Context recall    | 0.771 | 0.808 | 0.037 |
| Context precision | 0.84 | 0.825 | -0.015 |
| **Average**       | 0.693 | 0.715 | 0.022 |

## A/B comparison

- Cấu hình tốt hơn: Config B (hybrid + RRF)
- Evidence: Xem bảng Overall scores ở trên và chi tiết từng câu hỏi trong `eval_raw_results.json`.
- Trade-off về latency/cost: Hybrid+RRF gọi thêm BM25 (rẻ, tại chỗ) nên chi phí tăng không đáng kể so với dense-only; độ trễ tăng nhẹ do phải tính thêm điểm BM25 và gộp RRF trước khi gọi LLM.

## Worst performers

|   # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage             | Root cause |
| --: | -------- | ------ | -----------: | --------: | -----: | --------: | ------------------------- | ---------- |
|   1 | Thời điểm có hiệu lực của hợp đồng mua bán căn hộ được xác đ | A-dense | 0.000 | 0.000 | 0.000 | 0.000 | retrieval | Chunk về thời điểm có hiệu lực (Điều 44 khoản 6) nằm giữa nhiều điều khoản liền kề; dense search lấy nhầm chunk liền kề có cosine cao nhưng không chứa nội dung cốt lõi. |
|   2 | Bên bán căn hộ được miễn trách nhiệm bảo hành trong những tr | A-dense | 0.000 | 0.000 | 0.000 | 0.325 | retrieval | Câu hỏi hỏi điều kiện miễn trách — cụm từ "miễn trách nhiệm bảo hành" không xuất hiện verbatim trong corpus; dense embedding không đủ để map từ câu hỏi sang điều khoản liên quan. BM25 (hybrid) cải thiện precision nhờ keyword matching. |
|   3 | Thời điểm có hiệu lực của hợp đồng mua bán căn hộ được xác đ | B-hybrid | 0.500 | 0.000 | 0.000 | 0.000 | generation | LLM sinh câu trả lời có faithfulness 0.5 nhưng answer relevancy = 0 — câu trả lời trả về đúng trích dẫn luật nhưng không trả lời trực tiếp câu hỏi dạng "xác định như thế nào". Cần cải thiện system prompt để LLM tổng hợp thay vì chỉ trích dẫn. |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
|        1 | Xem lại 3 câu điểm thấp nhất ở trên, kiểm tra chunk trả về có đúng điều luật không | Bảng Worst performers | Tăng context precision/recall | Chạy lại run_evaluation.py sau khi chỉnh chunking |
|        2 | Cân nhắc thêm PageIndex hoặc mở rộng top_k cho câu hỏi có ngữ cảnh dàn trải nhiều điều luật | So sánh recall giữa 2 config | Tăng context recall | Đo lại recall trên các câu hỏi đa điều luật |
|        3 | Bổ sung thêm literal keyword (số điều, tên nghị định) vào câu hỏi khó để tận dụng BM25 | So sánh answer relevance dense vs hybrid | Tăng answer relevance | So sánh điểm relevance trước/sau |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | ------------------: | ---------- |
| Tăng top_k từ 5 lên 10 (Config B hybrid) | Config B avg 0.715 | +0.02 context recall (ước tính) | +15% latency do LLM context dài hơn | Cải thiện recall nhưng precision giảm nhẹ; top_k=5 là điểm cân bằng tốt cho corpus ~2000 chunk |
