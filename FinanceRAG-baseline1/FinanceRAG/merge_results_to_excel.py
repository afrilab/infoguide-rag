import json
from pathlib import Path
import pandas as pd


RESULTS_CSV = "results/final.csv"
DATASET_DIR = "dataset"
OUTPUT_XLSX = "results/final_merged.xlsx"


def load_jsonl_as_dict(file_path: Path):
    data = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            data[row["_id"]] = row
    return data


def load_all_datasets(dataset_root: Path):
    """
    dataset/ altındaki tüm subset klasörlerini yükler.
    Her subset için queries, queries_prep, corpus sözlükleri tutulur.
    """
    datasets = {}

    for subset_dir in dataset_root.iterdir():
        if not subset_dir.is_dir():
            continue

        queries_path = subset_dir / "queries.jsonl"
        queries_prep_path = subset_dir / "queries_prep.jsonl"
        corpus_path = subset_dir / "corpus.jsonl"

        if not queries_path.exists():
            continue
        if not queries_prep_path.exists():
            continue
        if not corpus_path.exists():
            continue

        try:
            datasets[subset_dir.name] = {
                "queries": load_jsonl_as_dict(queries_path),
                "queries_prep": load_jsonl_as_dict(queries_prep_path),
                "corpus": load_jsonl_as_dict(corpus_path),
            }
            print(f"Loaded dataset: {subset_dir.name}")
        except Exception as e:
            print(f"Skipping {subset_dir.name} due to error: {e}")

    return datasets


def find_match_across_datasets(query_id, corpus_id, datasets):
    """
    query_id ve corpus_id'yi tüm datasetlerde arar.
    Aynı dataset içinde ikisi birden varsa onu döndürür.
    """
    for subset_name, data in datasets.items():
        if query_id in data["queries"] and corpus_id in data["corpus"]:
            query_text = data["queries"][query_id].get("text", "")
            expanded_query_text = data["queries_prep"].get(query_id, {}).get("text", "")
            document_text = data["corpus"][corpus_id].get("text", "")

            return {
                "subset": subset_name,
                "query_id": query_id,
                "query": query_text,
                "expanded_query": expanded_query_text,
                "document_id": corpus_id,
                "document": document_text,
            }

    # Hiçbir datasette eşleşme yoksa boş dön
    return {
        "subset": "NOT_FOUND",
        "query_id": query_id,
        "query": "",
        "expanded_query": "",
        "document_id": corpus_id,
        "document": "",
    }


def main():
    results_path = Path(RESULTS_CSV)
    dataset_root = Path(DATASET_DIR)
    output_path = Path(OUTPUT_XLSX)

    if not results_path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")

    if not dataset_root.exists():
        raise FileNotFoundError(f"Dataset directory not found: {dataset_root}")

    df = pd.read_csv(results_path)

    if "query_id" not in df.columns or "corpus_id" not in df.columns:
        raise ValueError(
            f"final.csv must contain 'query_id' and 'corpus_id'. Current columns: {df.columns.tolist()}"
        )

    datasets = load_all_datasets(dataset_root)

    if not datasets:
        raise ValueError("No valid dataset folders found under dataset/")

    merged_rows = []

    for _, row in df.iterrows():
        query_id = row["query_id"]
        corpus_id = row["corpus_id"]

        merged_row = find_match_across_datasets(query_id, corpus_id, datasets)
        merged_rows.append(merged_row)

    merged_df = pd.DataFrame(merged_rows)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged_df.to_excel(output_path, index=False)

    print(f"\nDone. Excel file saved to: {output_path}")
    print(f"Total rows written: {len(merged_df)}")
    print(f"Rows not found: {(merged_df['subset'] == 'NOT_FOUND').sum()}")


if __name__ == "__main__":
    main()
