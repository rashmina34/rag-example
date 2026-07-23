from google import genai
from google.genai.types import EmbedContentConfig
import os
import numpy as np

client = genai.Client()

def load_chunks(folder="docs"):
    chunks = []
    for filename in os.listdir(folder):
        path = os.path.join(folder, filename)
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    chunks.append({"text": line, "source": filename})
    return chunks
chunks = load_chunks()

def embed_chunks(chunks):
    for chunk in chunks:
        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=chunk["text"],
            config=EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
        )
        chunk["embedding"] = result.embeddings[0].values
    return chunks

chunks = embed_chunks(chunks)
print("Embedded", len(chunks), "chunks.")

def cosine_similarity(a, b):
    a, b = np.array(a), np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def search(query, chunks, top_k=2):
    query_embedding = client.models.embed_content(
        model="gemini-embedding-001",
        contents=query,
        config=EmbedContentConfig(task_type="RETRIEVAL_QUERY")
    ).embeddings[0].values

    scored = []
    for chunk in chunks:
        score = cosine_similarity(query_embedding, chunk["embedding"])
        scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_k]

results = search("How many vacation days do I get?", chunks)
# for score, chunk in results:
#     print(f"{score:.3f} | {chunk['source']} | {chunk['text']}")
    
    
def build_prompt(query, retrieved_chunks):
    context = "\n".join(f"- {chunk['text']} (source: {chunk['source']})" for _, chunk in retrieved_chunks)

    prompt = f"""Answer the question using ONLY the context below. If the context doesn't contain the answer, say you don't know — don't make anything up.

Context:
{context}

Question: {query}

Answer:"""
    return prompt


def rag_query(query, chunks):
    retrieved = search(query, chunks, top_k=3)
    prompt = build_prompt(query, retrieved)

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt
    )
    return response.text, retrieved

answer, sources = rag_query("How many vacation days do I get?", chunks)
print("Answer:", answer)
print("\nSources used:")
for score, chunk in sources:
    print(f"  ({score:.3f}) {chunk['source']}: {chunk['text']}")
    
answer, sources = rag_query("What's the CEO's name?", chunks)
print(answer)