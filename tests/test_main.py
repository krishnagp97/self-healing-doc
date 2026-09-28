from pathlib import Path

from src.main import run
import pytest


def fake_link_all_sections(sections, chunks):
    return {
        "links": [
            {
                "doc_id": "sample.md::get_user",
                "code_id": "sample.py::UserService.get_user",
                "heading": "get_user",
                "symbol": "UserService.get_user",
            }
        ],
        "unmatched": [],
        "ambiguous": [],
    }


def test_run_end_to_end(monkeypatch, capsys):
    base = Path(__file__).parent / "fixtures"

    old_path = base / "old"
    new_path = base / "new"

    monkeypatch.setattr(
        "src.main.link_all_sections",
        fake_link_all_sections,
    )

    run(old_path, new_path)

    output = capsys.readouterr().out

    assert "Modified: 1" in output
    assert "Affected documentation sections: 1" in output
    assert "sample.md::get_user" in output
    assert "Total review items: 1" in output


def test_run_applies_ai_suggested_update(monkeypatch):
    base = Path(__file__).parent / "fixtures"

    old_path = base / "old"
    new_path = base / "new"

    def fake_review(review_item):
        return {
            "success": True,
            "issue": (
                "Documentation does not mention "
                "the optional email parameter."
            ),
            "suggested_update": (
                "Fetches a user by ID and optionally "
                "includes their email."
            ),
        }

    monkeypatch.setattr(
        "src.main.review_documentation",
        fake_review,
    )

    monkeypatch.setattr(
        "src.main.link_all_sections",
        fake_link_all_sections,
    )

    run(old_path, new_path)

    updated_file = new_path / "sample.md"
    content = updated_file.read_text(encoding="utf-8")

    assert (
        "Fetches a user by ID and optionally includes their email."
        in content
    )


def test_run_handles_ai_review_failure(monkeypatch, capsys):
    base = Path(__file__).parent / "fixtures"

    old_path = base / "old"
    new_path = base / "new"

    def fake_review(review_item):
        return {
            "success": False,
            "issue": "AI review is temporarily unavailable.",
            "suggested_update": "",
        }

    monkeypatch.setattr(
        "src.main.review_documentation",
        fake_review,
    )

    monkeypatch.setattr(
        "src.main.link_all_sections",
        fake_link_all_sections,
    )

    run(old_path, new_path)

    output = capsys.readouterr().out

    assert "✗ AI review failed:" in output
    assert "AI review is temporarily unavailable." in output
    assert "No documentation update suggested." in output

def test_main_exits_with_code_2_when_semantic_linking_fails(monkeypatch):
    def fake_run(old_path, new_path):
        from src.llm.linker import SemanticLinkerError

        raise SemanticLinkerError(
            "Gemini semantic linking is temporarily unavailable."
        )

    monkeypatch.setattr(
        "src.main.run",
        fake_run,
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "main.py",
            "old",
            "new",
        ],
    )

    from src.main import main

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 2