import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings

# Initialize ChromaDB client
client = chromadb.PersistentClient(path="./vector_store")

# Initialize embedding function
embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def process_and_store_documents(docs: list, collection_name: str):
    """
    Processes documents, splits them into chunks, embeds them, and stores them in a session-specific ChromaDB collection.
    """
    if not docs:
        return
        
    collection = client.get_or_create_collection(name=collection_name)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    
    for doc in docs:
        # Check if doc is a Document object with page_content
        if hasattr(doc, 'page_content'):
            chunks = text_splitter.split_text(doc.page_content)
            if chunks:
                # Generate unique IDs for each chunk to avoid collisions
                source_id = doc.metadata.get("source", "unknown")
                ids = [f"{source_id}_{i}" for i in range(len(chunks))]

                collection.add(
                    embeddings=embedding_function.embed_documents(chunks),
                    documents=chunks,
                    metadatas=[doc.metadata] * len(chunks),
                    ids=ids
                )

def query_vector_db(query: str, collection_name: str, n_results=5) -> list:
    """
    Queries a session-specific vector database for relevant document chunks.
    """
    try:
        collection = client.get_collection(name=collection_name)
        query_embedding = embedding_function.embed_query(query)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        # The query returns a list of results for each query embedding. 
        # Since we only pass one, we take the first element.
        return results.get("documents", [[]])[0]
    except Exception as e:
        print(f"Error querying collection {collection_name}: {e}")
        return []

def delete_session_collection(collection_name: str):
    """
    Deletes a specific ChromaDB collection associated with a session.
    """
    try:
        client.delete_collection(name=collection_name)
        print(f"Collection '{collection_name}' deleted successfully.")
    except Exception as e:
        print(f"Error deleting collection '{collection_name}': {e}")
        raise # Re-raise the exception to be handled by the calling function

def collection_exists(collection_name: str) -> bool:
    """
    Checks if a ChromaDB collection with the given name exists.
    """
    try:
        client.get_collection(name=collection_name)
        return True
    except Exception: # ChromaDB raises ValueError if collection not found
        return False
