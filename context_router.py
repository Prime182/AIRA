from langchain_core.documents import Document
from context_sources import arxiv_api, user_local_files, github_docs

SOURCE_FETCHERS = {
    "arxiv_api": arxiv_api.fetch_papers,
    "user_local_files": user_local_files.read_files,
    "github_docs": github_docs.fetch_docs, # Re-added for general context fetching
}

def fetch_all_context(query: str, sources: list) -> list:
    """
    Fetches context from all specified sources, adds a source type to the metadata,
    and returns them as Document objects.
    """
    all_docs = []
    for source_name in sources:
        if source_name in SOURCE_FETCHERS:
            try:
                docs_data = SOURCE_FETCHERS[source_name](query)
                
                # This block handles sources that return Document objects directly (e.g., user_local_files)
                if all(isinstance(d, Document) for d in docs_data):
                    for doc in docs_data:
                        doc.metadata['source_type'] = source_name
                    all_docs.extend(docs_data)
                    continue

                # This block handles sources that return dictionaries (e.g., arxiv, github_docs)
                for doc_data in docs_data:
                    content = doc_data.get("content", "")
                    metadata = doc_data.get("metadata", {})
                    
                    # Add or update metadata fields
                    metadata['source_type'] = source_name
                    if 'title' in doc_data and 'title' not in metadata:
                        metadata['title'] = doc_data['title']
                    
                    all_docs.append(Document(page_content=content, metadata=metadata))

            except Exception as e:
                print(f"Error fetching from {source_name}: {e}")
    return all_docs
