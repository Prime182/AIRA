import os
import PyPDF2
from langchain.docstore.document import Document

def read_files(query: str, data_dir="data/") -> list:
    """
    Reads .pdf and .txt files in the data directory and returns them as LangChain Document objects.
    """
    docs = []
    if not os.path.exists(data_dir) or not os.listdir(data_dir):
        print(f"No files found in the '{data_dir}' directory.")
        return docs

    for filename in os.listdir(data_dir):
        filepath = os.path.join(data_dir, filename)
        content = ""
        try:
            if filename.endswith(".txt"):
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
            elif filename.endswith(".pdf"):
                with open(filepath, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        content += page.extract_text() or ""
            
            if content:
                doc = Document(page_content=content, metadata={"source": filename})
                docs.append(doc)
        except Exception as e:
            print(f"Error processing file {filename}: {e}")
    return docs
