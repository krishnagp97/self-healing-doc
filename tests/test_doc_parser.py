
from pathlib import Path

from src.doc_parser import parse_markdown


def test_parse_markdown():
    root = Path(__file__).resolve().parents[1] / "fixtures"
    file_path = root / "sample.md"

    sections = parse_markdown(file_path, root)
    by_heading = {section["heading"]: section for section in sections}

    assert "User Service" in by_heading
    assert "get_user" in by_heading
    assert "delete_user" in by_heading

    assert by_heading["get_user"]["level"] == 2
    assert "Fetches a user by ID." in by_heading["get_user"]["content"]