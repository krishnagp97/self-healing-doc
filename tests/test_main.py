from pathlib import Path

from src.main import run


def test_run_end_to_end(capsys):
    base = Path(__file__).parent / "fixtures"

    old_path = base / "old"
    new_path = base / "new"

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
            "issue": "Documentation does not mention the optional email parameter.",
            "suggested_update": (
                "Fetches a user by ID and optionally includes their email."
            ),
        }

    monkeypatch.setattr(
        "src.main.review_documentation",
        fake_review,
    )

    run(old_path, new_path)

    updated_file = new_path / "sample.md"
    content = updated_file.read_text(encoding="utf-8")

    assert (
        "Fetches a user by ID and optionally includes their email."
        in content
    )