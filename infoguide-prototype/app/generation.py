import os
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


def build_context_from_chunks(chunks):
    context_parts = []

    for index, chunk in enumerate(chunks, start=1):
        chunk_id = chunk.get("chunk_id", index)

        metadata = chunk.get("metadata", {}) or {}

        heading = metadata.get("heading") or chunk.get("heading", "No heading")
        text = chunk.get("text", "")
        context_block = f"[Chunk {chunk_id} | Heading: {heading}]\n{text}"
        context_parts.append(context_block)

    return "\n\n---\n\n".join(context_parts)


def generate_answer_with_gpt(query, context_chunks, client):
    context = build_context_from_chunks(context_chunks)

    prompt = f"""
You are InfoGuide, a RAG-based question answering assistant.

Your task:
Answer the user's question using ONLY the provided context chunks.

Rules:
- Do not use outside knowledge.
- If the answer is not in the context, say:
  "The provided documents do not contain enough information to answer this question."
- Be clear and concise.
- Mention which chunks support the answer.

User question:
{query}

Retrieved context chunks:
{context}

Final answer:
"""

    response = client.chat.completions.create(
        model=GPT_MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "You are a strict RAG assistant. Only use given context."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
        max_tokens=500
    )

    return response.choices[0].message.content.strip()