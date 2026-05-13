import os
import numpy as np
import faiss
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


def create_query_embedding(query, embedding_model):
    query_vector = embedding_model.embed_query(query)
    query_vector = np.array([query_vector], dtype=np.float32)

    faiss.normalize_L2(query_vector)

    return query_vector