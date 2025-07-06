import arxiv

def fetch_papers(query: str, max_results=10) -> list:
    """
    Fetches papers from the arXiv API based on a query.
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
            papers.append({
                "title": result.title,
                "summary": result.summary,
                "pdf_url": result.pdf_url,
                "source": "arxiv"
            })
        return papers
    except Exception as e:
        print(f"An error occurred while fetching from arXiv: {e}")
        return []
