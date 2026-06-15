import os
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI


GPT_MODEL_NAME = "gpt-4o-mini"


def load_gpt_client():
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in .env file.")

    client = OpenAI(api_key=api_key)
    return client


def expand_query_with_gpt(query, client):
    prompt = f"""
You are a query expansion assistant for a RAG system.

Original user query:
{query}

Your task:
1. Extract the main intent of the user.
2. Generate related keywords.
3. Generate an expanded search query.

Return only this format:

Intent: ...
Keywords: keyword1, keyword2, keyword3
Expanded Query: ...
"""

    response = client.chat.completions.create(
        model=GPT_MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful query expansion assistant for a RAG system."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
        max_tokens=200
    )

    output = response.choices[0].message.content.strip()

    if "Expanded Query:" in output:
        expanded_query = output.split("Expanded Query:")[-1].strip()
    else:
        expanded_query = output.strip()

    return output, expanded_query


def decompose_query_with_gpt(query, client):
    prompt = f"""You are a query decomposition assistant for a RAG system.

Analyze the following query. If it addresses a single focused concept, return it unchanged as one line. If it contains multiple distinct concepts or questions that each need independent retrieval, break it into as many atomic sub-queries as the query genuinely requires — do not force a fixed count.

Each sub-query should:
- Address a single specific concept
- Be independently searchable in a document

Original query:
{query}

Return ONLY the final sub-queries (or the original query if no decomposition is needed), one per line, no numbering or extra text:"""

    response = client.chat.completions.create(
        model=GPT_MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "You are a query decomposition assistant. If the query is already focused, return it as-is. Otherwise decompose it. Return one query per line, no numbering."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1,
        max_tokens=500,
    )

    output = response.choices[0].message.content.strip()
    sub_queries = [line.strip() for line in output.splitlines() if line.strip()]
    return sub_queries if sub_queries else [query]


def create_query_embedding(query, embedding_model):
    query_vector = embedding_model.embed_query(query)
    return np.array([query_vector], dtype=np.float32)


def create_sub_query_embeddings(sub_queries, embedding_model):
    return [
        np.array([embedding_model.embed_query(q)], dtype=np.float32)
        for q in sub_queries
    ]