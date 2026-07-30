from google import genai
from google.genai.types import EmbedContentConfig
import os
import numpy as np
import chromadb
from dotenv import load_dotenv
load_dotenv()

client = genai.Client()

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="my_docs")

def index_chunks(chunks):
    ids = []
    embeddings = []
    documents = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=chunk["text"],
            config=EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
        )
        ids.append(f"chunk_{i}")
        embeddings.append(result.embeddings[0].values)
        documents.append(chunk["text"])
        metadatas.append({"source": chunk["source"]})

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )
    print(f"Indexed {len(ids)} chunks into Chroma.")

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
index_chunks(chunks)

# Vector DB search
def search(query, top_k=3):
    query_embedding = client.models.embed_content(
        model="gemini-embedding-001",
        contents=query,
        config=EmbedContentConfig(task_type="RETRIEVAL_QUERY")
    ).embeddings[0].values

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    return list(zip(results["documents"][0], results["metadatas"][0], results["distances"][0]))

results = search("How many vacation days do I get?")
for text, meta, distance in results:
    print(f"{distance:.3f} | {meta['source']} | {text}")
    
print(collection.count())

def rag_query(query):
    retrieved = search(query, top_k=3)
    # retrieved is now [(text, metadata, distance), ...] from the Chroma version
    context = "\n".join(f"- {text} (source: {meta['source']})" for text, meta, _ in retrieved)

    prompt = f"""Answer using ONLY the context below. If it doesn't contain the answer, say you don't know.

Context:
{context}

Question: {query}

Answer:"""

    response = client.models.generate_content(model="gemini-3.5-flash", contents=prompt)
    return response.text, retrieved

answer, sources = rag_query("How many vacation days do I get?")