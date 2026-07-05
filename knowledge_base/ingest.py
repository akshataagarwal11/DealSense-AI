import os
import logging

import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader

import config

logger = logging.getLogger(__name__)


def get_chroma_client():
    """Create or connect to the persistent ChromaDB database."""
    return chromadb.PersistentClient(path=config.CHROMA_DB_PATH)


def get_collection(client):
    """Create or retrieve the DealSense knowledge collection."""
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    return client.get_or_create_collection(
        name="dealsense_knowledge",
        embedding_function=ef
    )


def extract_text_from_file(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50
) -> list[str]:
    """
    Split large documents into overlapping chunks for better RAG retrieval.
    """

    words = text.split()

    chunks = []

    i = 0

    while i < len(words):

        chunk = " ".join(words[i:i + chunk_size])

        chunks.append(chunk)

        i += chunk_size - overlap

    return chunks


def ingest_all_documents():
    print("Starting knowledge base ingestion...")
    """
    Read all PDFs inside knowledge_base/documents/,
    chunk them,
    embed them,
    and store them inside ChromaDB.
    """

    client = get_chroma_client()

    collection = get_collection(client)

    docs_path = config.KNOWLEDGE_BASE_PATH

    all_chunks = []
    all_ids = []
    all_metadata = []

    for filename in os.listdir(docs_path):

        if not filename.endswith(".txt"):
            continue

        pdf_path = os.path.join(docs_path, filename)

        logger.info(f"Ingesting {filename}")

        text = extract_text_from_file(pdf_path)

        chunks = chunk_text(text)

        for i, chunk in enumerate(chunks):

            all_chunks.append(chunk)

            all_ids.append(f"{filename}_{i}")

            all_metadata.append({
                "source": filename,
                "chunk_index": i,
                "policy_version": config.POLICY_VERSION
            })

    if not all_chunks:
        raise ValueError(
            "No PDF documents found in knowledge_base/documents."
        )

    collection.upsert(
        documents=all_chunks,
        ids=all_ids,
        metadatas=all_metadata
    )
    print(f"Successfully ingested {len(all_chunks)} chunks.")

    logger.info(f"Ingested {len(all_chunks)} chunks into ChromaDB")


if __name__ == "__main__":
    ingest_all_documents()