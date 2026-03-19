import os
import logging
import nltk
from financerag.tasks import FinDER, FinQABench, FinanceBench, TATQA, FinQA, ConvFinQA, MultiHiertt
from financerag.retrieval import DenseRetrieval, SentenceTransformerEncoder
from sentence_transformers import SentenceTransformer, CrossEncoder
from hybrid_search import HybridSearcher

_PROJ_ROOT = os.environ.get("GAR_PROJECT_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(_PROJ_ROOT)

logging.basicConfig(level=logging.INFO)

nltk.download('punkt')
hybrid_searcher = HybridSearcher()

tasks, names = hybrid_searcher.setup_task()

retrieval_model = hybrid_searcher.retrieval_model_setup()
reranker_model = hybrid_searcher.reranker_model_setup()

output_dir = os.path.join(_PROJ_ROOT, "outputs", "hybrid_search")

for task, name in zip(tasks, names):
    optimal_alpha = hybrid_searcher.tune_alpha(task, retrieval_model)
    hybrid_retrieval_results = hybrid_searcher.get_hybrid_score(task, optimal_alpha, retrieval_model)
    reranked_results = hybrid_searcher.get_reranker_score(task, hybrid_retrieval_results, reranker_model)
    ndcg_score = hybrid_searcher.get_final_ndcg(tasks, names)

    print(f"Task: {name}, NDCG Score: {ndcg_score}")
    print(f"Optimal Alpha: {optimal_alpha}")
    task.rerank_results = reranked_results
    task.save_results(top_k=10, output_dir=output_dir)

hybrid_searcher.merge_csv_results(output_dir)
