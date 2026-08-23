import re
from dataclasses import dataclass, field
from pathlib import Path

from app.schemas import KnowledgeRef

DOCS_DIR = Path(__file__).parent / "docs"

_STOPWORDS = {
    "a",
    "an",
    "the",
    "is",
    "are",
    "was",
    "were",
    "be",
    "to",
    "of",
    "and",
    "or",
    "in",
    "on",
    "for",
    "with",
    "my",
    "your",
    "i",
    "you",
    "it",
    "this",
    "that",
    "do",
    "does",
    "not",
    "what",
    "how",
    "can",
    "please",
    "me",
}


def _tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in _STOPWORDS]


@dataclass
class Document:
    doc_id: str
    title: str
    keywords: set[str]
    body: str
    body_tokens: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.body_tokens = _tokenize(self.body)


class KnowledgeRetriever:

    def __init__(self, docs_dir: Path = DOCS_DIR):
        self._documents = [self._parse(path) for path in sorted(docs_dir.glob("*.md"))]

    @property
    def document_count(self) -> int:
        return len(self._documents)

    def add_document(self, title: str, content: str) -> int:
        lines = content.splitlines()
        keywords: set[str] = set()
        body = content.strip()
        if lines and lines[0].startswith("# "):
            title = lines[0][2:].strip() or title
            body_start = 1
            if len(lines) > 1 and lines[1].lower().startswith("keywords:"):
                keywords = set(_tokenize(lines[1].split(":", 1)[1]))
                body_start = 2
            body = "\n".join(lines[body_start:]).strip()
        doc_id = (
            re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or f"doc-{len(self._documents)}"
        )
        self._documents = [d for d in self._documents if d.doc_id != doc_id]
        self._documents.append(Document(doc_id=doc_id, title=title, keywords=keywords, body=body))
        return len(self._documents)

    @staticmethod
    def _parse(path: Path) -> Document:
        lines = path.read_text().splitlines()
        title = lines[0].lstrip("# ").strip()
        keywords: set[str] = set()
        body_start = 1
        if len(lines) > 1 and lines[1].lower().startswith("keywords:"):
            keywords = set(_tokenize(lines[1].split(":", 1)[1]))
            body_start = 2
        return Document(
            doc_id=path.stem,
            title=title,
            keywords=keywords,
            body="\n".join(lines[body_start:]).strip(),
        )

    def search(self, query: str, top_k: int = 3, min_score: float = 1.0) -> list[KnowledgeRef]:
        query_tokens = set(_tokenize(query))
        if not query_tokens:
            return []
        scored: list[tuple[float, Document]] = []
        for doc in self._documents:
            title_hits = len(query_tokens & set(_tokenize(doc.title)))
            keyword_hits = len(query_tokens & doc.keywords)
            body_hits = sum(1 for t in query_tokens if t in doc.body_tokens)
            score = 3.0 * title_hits + 2.0 * keyword_hits + 0.5 * body_hits
            if score >= min_score:
                scored.append((score, doc))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [
            KnowledgeRef(
                doc_id=doc.doc_id,
                title=doc.title,
                snippet=doc.body[:300],
                score=round(score, 2),
            )
            for score, doc in scored[:top_k]
        ]
