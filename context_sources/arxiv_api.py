import arxiv
import requests
import PyPDF2
from io import BytesIO

def fetch_papers(query: str, max_results=5) -> list:
    """
    Fetches papers from the arXiv API, downloads the PDF, and extracts the text content.
    """
    print(f"Querying arXiv with: '{query}'")
    try:
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        papers = []
        results = list(search.results())
        if not results:
            print(f"No results found on arXiv for query: {query}")
            return []
            
        for result in results:
            try:
                # Download the PDF content
                response = requests.get(result.pdf_url)
                response.raise_for_status()
                
                # Read the PDF from the downloaded content
                pdf_file = BytesIO(response.content)
                reader = PyPDF2.PdfReader(pdf_file)
                
                # Extract text from all pages
                pdf_text = ""
                for page in reader.pages:
                    pdf_text += page.extract_text() or ""

                papers.append({
                    "title": result.title,
                    "summary": result.summary,
                    "content": pdf_text,  # Add the full PDF text
                    "pdf_url": result.pdf_url,
                    "source": "arxiv"
                })
            except Exception as e:
                print(f"Could not process paper '{result.title}': {e}")
                # Optionally, append with summary only if PDF fails
                papers.append({
                    "title": result.title,
                    "summary": result.summary,
                    "content": result.summary, # Fallback to summary
                    "pdf_url": result.pdf_url,
                    "source": "arxiv"
                })
        return papers
    except Exception as e:
        print(f"An error occurred while fetching from arXiv: {e}")
        return []
