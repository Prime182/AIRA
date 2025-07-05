import os
import PyPDF2

def read_files(query: str, data_dir="data/") -> list:
    """
    Reads text from .pdf and .txt files in the data directory.
    """
    docs = []
    if not os.path.exists(data_dir) or not os.listdir(data_dir):
        print(f"No files found in the '{data_dir}' directory.")
        return docs

    for filename in os.listdir(data_dir):
        filepath = os.path.join(data_dir, filename)
        try:
            if filename.endswith(".txt"):
                with open(filepath, "r", encoding="utf-8") as f:
                    docs.append({"source": filename, "content": f.read()})
            elif filename.endswith(".pdf"):
                with open(filepath, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    content = ""
                    for page in reader.pages:
                        content += page.extract_text()
                    docs.append({"source": filename, "content": content})
        except Exception as e:
            print(f"Error reading file {filename}: {e}")
    return docs
