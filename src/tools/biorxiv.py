"""bioRxiv/medRxiv preprint search tool."""

import re
from datetime import datetime, timedelta
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from src.utils.exceptions import SearchError
from src.utils.models import Citation, Evidence


class BioRxivTool:
    """Search tool for bioRxiv and medRxiv preprints."""

    BASE_URL = "https://api.biorxiv.org/details"
    # Use medRxiv for medical/clinical content (more relevant for drug repurposing)
    DEFAULT_SERVER = "medrxiv"
    # Fetch papers from last N days
    DEFAULT_DAYS = 90

    def __init__(self, server: str = DEFAULT_SERVER, days: int = DEFAULT_DAYS) -> None:
        """
        Initialize bioRxiv tool.

        Args:
            server: "biorxiv" or "medrxiv"
            days: How many days back to search
        """
        self.server = server
        self.days = days

    @property
    def name(self) -> str:
        return "biorxiv"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def search(self, query: str, max_results: int = 10) -> list[Evidence]:
        """
        Search bioRxiv/medRxiv for preprints matching query.

        Note: bioRxiv API doesn't support keyword search directly.
        We fetch recent papers and filter client-side.

        Args:
            query: Search query (keywords)
            max_results: Maximum results to return

        Returns:
            List of Evidence objects from preprints
        """
        # Build date range for last N days
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=self.days)).strftime("%Y-%m-%d")
        interval = f"{start_date}/{end_date}"

        # Fetch recent papers
        url = f"{self.BASE_URL}/{self.server}/{interval}/0/json"

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise SearchError(f"bioRxiv search failed: {e}") from e

            data = response.json()
            papers = data.get("collection", [])

            # Filter papers by query keywords
            query_terms = self._extract_terms(query)
            matching = self._filter_by_keywords(papers, query_terms, max_results)

            return [self._paper_to_evidence(paper) for paper in matching]

    def _extract_terms(self, query: str) -> list[str]:
        """Extract search terms from query."""
        # Simple tokenization, lowercase
        terms = re.findall(r"\b\w+\b", query.lower())
        # Filter out common stop words
        stop_words = {"the", "a", "an", "in", "on", "for", "and", "or", "of", "to"}
        return [t for t in terms if t not in stop_words and len(t) > 2]

    def _filter_by_keywords(
        self, papers: list[dict[str, Any]], terms: list[str], max_results: int
    ) -> list[dict[str, Any]]:
        """Filter papers that contain query terms in title or abstract."""
        scored_papers = []

        for paper in papers:
            title = paper.get("title", "").lower()
            abstract = paper.get("abstract", "").lower()
            text = f"{title} {abstract}"

            # Count matching terms
            matches = sum(1 for term in terms if term in text)

            if matches > 0:
                scored_papers.append((matches, paper))

        # Sort by match count (descending)
        scored_papers.sort(key=lambda x: x[0], reverse=True)

        return [paper for _, paper in scored_papers[:max_results]]

    def _paper_to_evidence(self, paper: dict[str, Any]) -> Evidence:
        """Convert a preprint paper to Evidence."""
        doi = paper.get("doi", "")
        title = paper.get("title", "Untitled")
        authors_str = paper.get("authors", "Unknown")
        date = paper.get("date", "Unknown")
        abstract = paper.get("abstract", "No abstract available.")
        category = paper.get("category", "")

        # Parse authors (format: "Smith, J; Jones, A")
        authors = [a.strip() for a in authors_str.split(";")][:5]

        # Note this is a preprint in the content
        content = (
            f"[PREPRINT - Not peer-reviewed] " f"{abstract[:1800]}... " f"Category: {category}."
        )

        return Evidence(
            content=content[:2000],
            citation=Citation(
                source="biorxiv",
                title=title[:500],
                url=f"https://doi.org/{doi}" if doi else "https://www.medrxiv.org/",
                date=date,
                authors=authors,
            ),
            relevance=0.75,  # Slightly lower than peer-reviewed
        )
