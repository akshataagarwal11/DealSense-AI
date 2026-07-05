import logging

from knowledge_base.ingest import get_chroma_client, get_collection

logger = logging.getLogger(__name__)


def retrieve_context(deal: dict, n_results: int = 5) -> str:
    """
    Build a semantic query from deal data and retrieve the
    most relevant knowledge base chunks.
    """

    query = (
        f"Deal stage: {deal['stage']}. "
        f"Company size: {deal['company_size']}. "
        f"Days since activity: {deal['days_since_activity']}. "
        f"Deal value: {deal['amount']}. "
        f"Risk signals and scoring criteria for this type of deal."
    )

    client = get_chroma_client()
    collection = get_collection(client)

    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )

    chunks = results.get("documents", [[]])[0]
    metadata = results.get("metadatas", [[]])[0]

    if not chunks:
        logger.warning("No knowledge base context retrieved.")
        return ""

    formatted = ""

    for chunk, meta in zip(chunks, metadata):
        source = meta.get("source", "Unknown")
        formatted += f"[Source: {source}]\n{chunk}\n\n"

    logger.info(
        f"Retrieved {len(chunks)} knowledge chunks "
        f"for deal '{deal['name']}'."
    )

    return formatted