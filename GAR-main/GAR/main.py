# main.py
import os
import pandas as pd
from Selection_agent import SelectionAgent
from DPO_agent import DPO_Agent
from DPO_agent_Finetuning import dpo_agent_finetuning
from Finetuned_DPO_agent import Finetuned_DPO_agent
from openai import OpenAI

_PROJ_ROOT = os.environ.get("GAR_PROJECT_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

def main():
    API_KEY = os.getenv('OPENAI_API_KEY')

    dataset_path = os.path.join(_PROJ_ROOT, 'data/raw/dataset.csv')
    selected_docs_path = os.path.join(_PROJ_ROOT, 'data/processed/selected_docs.csv')
    dpo_responses_path = os.path.join(_PROJ_ROOT, 'data/processed/dpo_responses.csv')
    final_answers_path = os.path.join(_PROJ_ROOT, 'data/processed/final_answers.csv')
    train_path = os.path.join(_PROJ_ROOT, 'data/models/fine_tuned/train.jsonl')
    eval_path = os.path.join(_PROJ_ROOT, 'data/models/fine_tuned/eval.jsonl')

    for p in (selected_docs_path, dpo_responses_path, final_answers_path, train_path, eval_path):
        ensure_dir(p)

    print("STEP: Selection started")
    selection_agent = SelectionAgent(API_KEY)
    df = pd.read_csv(dataset_path)
    selection_agent.process_data(df, selected_docs_path)
    print("STEP: Selection completed")

    print("STEP: DPO started")
    dpo_agent = DPO_Agent(API_KEY)
    selected_df = pd.read_csv(selected_docs_path)
    dpo_agent.process_data(selected_df, dpo_responses_path)
    print("STEP: DPO completed")

    print("STEP: DPO Finetuning started")
    finetuning_agent = dpo_agent_finetuning(API_KEY)
    finetuning_agent.save_from_csv_to_jsonl(dpo_responses_path, selected_docs_path, train_path)
    finetuning_agent.split_jsonl(train_path, train_path, eval_path)
    print("STEP: DPO Finetuning completed")

    print("STEP: Finetuned DPO started")
    finetuned_agent = Finetuned_DPO_agent(API_KEY)
    finetuned_agent.process_finetuning(df, final_answers_path)
    print("STEP: Finetuned DPO completed")
    print("STEP: Pipeline done")

if __name__ == '__main__':
    main()