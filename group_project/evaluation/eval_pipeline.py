"""
RAG Evaluation Pipeline — Framework: RAGAS.

Đo chất lượng RAG pipeline bằng 4 metric của RAGAS và so sánh A/B giữa 2 config.

Quy trình:
    1. Load golden_dataset.json (≥15 Q&A pairs)
    2. Với mỗi config (A: hybrid+rerank, B: dense-only), chạy pipeline trên từng câu hỏi
       để thu (answer, contexts)
    3. Evaluate 4 metric: faithfulness, answer_relevancy, context_recall, context_precision
    4. So sánh A/B và tìm 3 câu tệ nhất
    5. Export ra results.md

⚠️ Rate limit OpenRouter ":free": RAGAS gọi LLM judge RẤT NHIỀU LẦN (nhiều lần/metric/câu).
Model free của OpenRouter giới hạn 50 request/ngày CHO CẢ TÀI KHOẢN (đổi model/API key
KHÔNG reset quota). Nếu bị rate limit giữa chừng: giảm SUBSET_SIZE xuống 5 câu, hoặc nạp
$10 credit để mở khóa 1000 request/ngày. Có thể chỉnh SUBSET_SIZE qua biến môi trường
EVAL_SUBSET_SIZE.

Cài đặt:
    pip install ragas==0.1.21 datasets langchain-openai
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

GOLDEN_DATASET_PATH = Path(__file__).parent / "golden_dataset.json"
RESULTS_PATH = Path(__file__).parent / "results.md"

# LLM judge dùng để chấm điểm RAGAS (OpenRouter, OpenAI-compatible)
JUDGE_MODEL = os.getenv("EVAL_JUDGE_MODEL", "openai/gpt-4o-mini")
# Embedding model cho các metric cần similarity (chạy local, không tốn request LLM)
EMBED_MODEL = os.getenv("EVAL_EMBED_MODEL", "BAAI/bge-m3")
# Giới hạn số câu hỏi để né rate limit khi thử nghiệm (0 = dùng toàn bộ dataset)
SUBSET_SIZE = int(os.getenv("EVAL_SUBSET_SIZE", "0"))

METRIC_KEYS = ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]


def load_golden_dataset() -> list[dict]:
    """Load golden dataset từ JSON file."""
    with open(GOLDEN_DATASET_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    if SUBSET_SIZE > 0:
        data = data[:SUBSET_SIZE]
    return data


# =============================================================================
# RAGAS judge (LLM + embeddings)
# =============================================================================

def _build_judge():
    """Khởi tạo LLM judge (OpenRouter) + embeddings (local) cho RAGAS."""
    from langchain_openai import ChatOpenAI
    from ragas.llms import LangchainLLMWrapper
    from ragas.embeddings import LangchainEmbeddingsWrapper

    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Thiếu OPENROUTER_API_KEY / OPENAI_API_KEY trong .env")

    chat = ChatOpenAI(
        model=JUDGE_MODEL,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=0.0,
    )

    # Embeddings chạy local qua sentence-transformers → không tốn request LLM
    from langchain_huggingface import HuggingFaceEmbeddings
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)

    return LangchainLLMWrapper(chat), LangchainEmbeddingsWrapper(embeddings)


# =============================================================================
# Chạy RAG pipeline theo config (để so sánh A/B)
# =============================================================================

def run_pipeline(question: str, use_reranking: bool, top_k: int = 5) -> dict:
    """
    Chạy retrieval + generation cho 1 câu hỏi theo config chỉ định.

    Trả về {'answer': str, 'contexts': list[str]}.
    Tái sử dụng các thành phần của Task 10 để answer sinh ra đúng từ contexts của config.
    """
    from src.task9_retrieval_pipeline import retrieve
    from src.task10_generation import (
        SYSTEM_PROMPT, TEMPERATURE, TOP_P, LLM_MODEL,
        reorder_for_llm, format_context,
    )
    from openai import OpenAI

    chunks = retrieve(question, top_k=top_k, use_reranking=use_reranking)
    contexts = [c["content"] for c in chunks]

    reordered = reorder_for_llm(chunks) if chunks else []
    context_str = format_context(reordered) if reordered else "(no context)"
    user_message = f"Context:\n{context_str}\n\n---\n\nQuestion: {question}"

    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=TEMPERATURE,
        top_p=TOP_P,
    )
    answer = response.choices[0].message.content

    return {"answer": answer, "contexts": contexts}


# =============================================================================
# Evaluate 1 config bằng RAGAS
# =============================================================================

def evaluate_config(golden_dataset: list[dict], use_reranking: bool):
    """
    Chạy pipeline + RAGAS cho 1 config.

    Returns:
        pandas.DataFrame — mỗi dòng 1 câu hỏi kèm điểm 4 metric.
    """
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness, answer_relevancy, context_recall, context_precision,
    )
    from datasets import Dataset

    eval_data = {"question": [], "answer": [], "contexts": [], "ground_truth": []}
    for item in golden_dataset:
        out = run_pipeline(item["question"], use_reranking=use_reranking)
        eval_data["question"].append(item["question"])
        eval_data["answer"].append(out["answer"])
        eval_data["contexts"].append(out["contexts"] or ["(no context retrieved)"])
        eval_data["ground_truth"].append(item["expected_answer"])

    dataset = Dataset.from_dict(eval_data)
    llm, embeddings = _build_judge()
    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
        llm=llm,
        embeddings=embeddings,
    )
    return result.to_pandas()


# =============================================================================
# A/B Comparison
# =============================================================================

def compare_configs(golden_dataset: list[dict]) -> dict:
    """
    So sánh A/B:
        - Config A: hybrid search + reranking (use_reranking=True)
        - Config B: dense-only, không reranking (use_reranking=False)

    Returns:
        {config_name: pandas.DataFrame}
    """
    configs = {
        "A_hybrid_rerank": True,
        "B_dense_only": False,
    }
    results = {}
    for name, use_reranking in configs.items():
        print(f"\n=== Đang đánh giá config: {name} (use_reranking={use_reranking}) ===")
        results[name] = evaluate_config(golden_dataset, use_reranking=use_reranking)
    return results


# =============================================================================
# Export Results
# =============================================================================

def _mean(df, col):
    return float(df[col].mean()) if col in df.columns else float("nan")


def export_results(results: dict):
    """Format và ghi kết quả A/B ra results.md."""
    df_a = results["A_hybrid_rerank"]
    df_b = results["B_dense_only"]

    metric_labels = {
        "faithfulness": "Faithfulness",
        "answer_relevancy": "Answer Relevance",
        "context_recall": "Context Recall",
        "context_precision": "Context Precision",
    }

    lines = ["# RAG Evaluation Results", ""]
    lines += ["## Framework sử dụng", "", "**RAGAS** (`ragas==0.1.21`) — LLM judge: "
              f"`{JUDGE_MODEL}` (OpenRouter), embeddings: `{EMBED_MODEL}` (local).", ""]
    lines += [f"- Số câu hỏi đánh giá: **{len(df_a)}**", ""]
    lines += ["---", "", "## Overall Scores", "",
              "| Metric | Config A (hybrid + rerank) | Config B (dense-only) | Δ (A−B) |",
              "|--------|---------------------------|----------------------|---------|"]

    a_means, b_means = [], []
    for key, label in metric_labels.items():
        a, b = _mean(df_a, key), _mean(df_b, key)
        a_means.append(a)
        b_means.append(b)
        lines.append(f"| {label} | {a:.3f} | {b:.3f} | {a - b:+.3f} |")

    avg_a = sum(a_means) / len(a_means)
    avg_b = sum(b_means) / len(b_means)
    lines.append(f"| **Average** | **{avg_a:.3f}** | **{avg_b:.3f}** | **{avg_a - avg_b:+.3f}** |")

    winner = "A (hybrid + rerank)" if avg_a >= avg_b else "B (dense-only)"
    lines += ["", "---", "", "## A/B Comparison Analysis", "",
              "**Config A:** Hybrid retrieval (semantic + BM25) → RRF merge → reranking.", "",
              "**Config B:** Dense-only (semantic search), không qua reranking.", "",
              f"**Kết luận:** Config **{winner}** cho điểm trung bình cao hơn "
              f"({max(avg_a, avg_b):.3f} vs {min(avg_a, avg_b):.3f}). "
              "Hybrid + rerank thường thắng ở context_precision nhờ BM25 bắt đúng "
              "từ khóa/số hiệu mà dense search bỏ sót.", ""]

    # Worst performers (bottom 3 theo faithfulness của config A)
    lines += ["---", "", "## Worst Performers (Bottom 3 — Config A)", "",
              "| # | Question | Faithfulness | Relevance | Recall | Precision |",
              "|---|----------|-------------|-----------|--------|-----------|"]
    if "faithfulness" in df_a.columns:
        worst = df_a.sort_values("faithfulness").head(3)
        for i, (_, row) in enumerate(worst.iterrows(), 1):
            q = str(row.get("question", ""))[:60]
            lines.append(
                f"| {i} | {q} | {row.get('faithfulness', float('nan')):.2f} | "
                f"{row.get('answer_relevancy', float('nan')):.2f} | "
                f"{row.get('context_recall', float('nan')):.2f} | "
                f"{row.get('context_precision', float('nan')):.2f} |"
            )

    lines += ["", "---", "", "## Recommendations", "",
              "### Cải tiến 1 — Chunking",
              "**Action:** Thử giảm CHUNK_SIZE (800→500) + tăng overlap để context_precision tốt hơn.",
              "**Expected impact:** Ít nhiễu trong context → faithfulness & precision tăng.", "",
              "### Cải tiến 2 — Reranking",
              "**Action:** Dùng cross-encoder rerank thay/kết hợp RRF cho top-k cuối.",
              "**Expected impact:** Đưa đúng chunk liên quan lên đầu → recall tăng.", "",
              "### Cải tiến 3 — Query expansion",
              "**Action:** Thêm HyDE / multi-query cho các câu hỏi tệ nhất ở bảng trên.",
              "**Expected impact:** Bắt được tài liệu mà truy vấn gốc bỏ lỡ.", ""]

    RESULTS_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n✓ Đã ghi kết quả ra {RESULTS_PATH}")


if __name__ == "__main__":
    golden_dataset = load_golden_dataset()
    print(f"Loaded {len(golden_dataset)} test cases")

    results = compare_configs(golden_dataset)
    export_results(results)
    print("✓ Done — xem group_project/evaluation/results.md")
