import re
from pathlib import Path


def _tokenize(text):
    """Convert text into lowercase searchable tokens."""

    if not text:
        return set()

    text = re.sub(
        r"([a-z0-9])([A-Z])",
        r"\1 \2",
        text,
    )

    text = re.sub(r"[_./\\-]+", " ", text)

    return {
        token.lower()
        for token in re.findall(r"[a-zA-Z0-9]+", text)
        if len(token) > 1
    }


def _candidate_tokens(chunk):
    """Build searchable tokens from a code chunk."""

    text = " ".join([
        chunk.get("name", ""),
        chunk.get("file", ""),
    ])

    return _tokenize(text)


def _path_tokens(path):
    """Extract searchable tokens from a file path."""

    return _tokenize(Path(path).as_posix())


def rank_candidates(section, chunks, limit=10):
    """
    Rank code chunks by relevance to a Markdown section.

    Ranking considers:
    - symbol/name overlap
    - code file path overlap
    - documentation file path overlap

    Candidates are always returned when chunks exist so that
    semantic linking still gets a chance when lexical overlap
    is weak.
    """

    section_text = " ".join([
        section.get("heading", ""),
        section.get("content", ""),
    ])

    section_tokens = _tokenize(section_text)

    doc_path_tokens = _path_tokens(
        section.get("file", "")
    )

    ranked = []

    for index, chunk in enumerate(chunks):

        candidate_tokens = _candidate_tokens(chunk)
        code_path_tokens = _path_tokens(
            chunk.get("file", "")
        )

        name_overlap = section_tokens & candidate_tokens
        path_overlap = doc_path_tokens & code_path_tokens

        score = (
            len(name_overlap) * 2
            + len(path_overlap)
        )

        ranked.append({
            "chunk": chunk,
            "score": score,
            "name_overlap": name_overlap,
            "path_overlap": path_overlap,
            "index": index,
        })

    ranked.sort(
        key=lambda item: (
            item["score"],
            -item["index"],
        ),
        reverse=True,
    )

    return [
        item["chunk"]
        for item in ranked[:limit]
    ]