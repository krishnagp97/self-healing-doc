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