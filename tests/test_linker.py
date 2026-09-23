
from pathlib import Path

from src.scanner import scan_repository
from src.doc_parser import parse_markdown
from src.linker import link_sections


def test_link_sections():
    root = Path(__file__).resolve().parents[1] / "fixtures"

    chunks = scan_repository(root)
    sections = parse_markdown(root / "sample.md", root)

    result = link_sections(sections, chunks)

    linked_headings = {
        link["heading"] for link in result["links"]
    }

    assert "get_user" in linked_headings
    assert "delete_user" in linked_headings
    assert result["ambiguous"] == []