from langchain_core.documents import Document
from context_sources import arxiv_api, user_local_files, github_docs

SOURCE_FETCHERS = {
    "arxiv_api": arxiv_api.fetch_papers,
    "user_local_files": user_local_files.read_files,
    "github_docs": github_docs.fetch_docs, # Re-added for general context fetching
}

def fetch_all_context(query: str, sources: list) -> list:
    """
    Fetches context from all specified sources and converts to Document objects.
    """
    all_docs = []
    for source in sources:
        if source in SOURCE_FETCHERS:
            try:
                docs_data = SOURCE_FETCHERS[source](query)
                for doc_data in docs_data:
                    # Determine content and metadata based on the source
                    if source == "arxiv_api":
                        content = doc_data.get("summary", "")
                        metadata = {
                            "title": doc_data.get("title"),
                            "pdf_url": doc_data.get("pdf_url"),
                            "source": "arxiv"
                        }
                    else: # For user_local_files and github_docs
                        content = doc_data.get("content", "")
                        metadata = {"source": doc_data.get("source")}
                    
                    all_docs.append(Document(page_content=content, metadata=metadata))

            except Exception as e:
                print(f"Error fetching from {source}: {e}")
    return all_docs
