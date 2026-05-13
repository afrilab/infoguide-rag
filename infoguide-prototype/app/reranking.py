from sentence_transformers import CrossEncoder


RERANKER_MODEL_NAME = "BAAI/bge-reranker-v2-m3"


def load_reranker_model():
    """
    Cross-encoder reranker modelini yükler.
    Bu model query ile chunk'ı birlikte değerlendirir.
    """
    reranker = CrossEncoder(RERANKER_MODEL_NAME)
    return reranker


def rerank_results(query, retrieved_results, reranker_model, top_k=5):
    """
    Retrieval sonucunda gelen chunk'ları yeniden sıralar.

    Parameters:
        query: Kullanıcının orijinal veya expanded query'si
        retrieved_results: FAISS veya BM25'ten dönen chunk listesi
        reranker_model: Yüklenmiş CrossEncoder modeli
        top_k: Reranking sonrası kaç chunk döndürülecek

    Returns:
        En alakalı top_k chunk listesi
    """

    if not retrieved_results:
        return []

    pairs = []

    for result in retrieved_results:
        pairs.append([query, result["text"]])

    scores = reranker_model.predict(pairs)

    reranked_results = []

    for result, score in zip(retrieved_results, scores):
        new_result = result.copy()
        new_result["rerank_score"] = float(score)
        reranked_results.append(new_result)

    reranked_results = sorted(
        reranked_results,
        key=lambda x: x["rerank_score"],
        reverse=True
    )

    return reranked_results[:top_k]