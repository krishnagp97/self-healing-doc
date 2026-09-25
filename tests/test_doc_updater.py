from src.doc_updater import update_section


def test_update_middle_section(tmp_path):
    doc = tmp_path / "README.md"

    doc.write_text(
        """# Project

## Authentication

Old authentication details.

## API

API details.

## Deployment

Deployment details.
""",
        encoding="utf-8",
    )

    result = update_section(
        str(doc),
        "Authentication",
        "Updated authentication details.",
    )

    assert result is True

    content = doc.read_text(encoding="utf-8")

    assert "Updated authentication details." in content
    assert "Old authentication details." not in content
    assert "## API" in content
    assert "API details." in content
    assert "## Deployment" in content


def test_update_last_section(tmp_path):
    doc = tmp_path / "README.md"

    doc.write_text(
        """# Project

## Authentication

Authentication details.

## Deployment

Old deployment details.
""",
        encoding="utf-8",
    )

    result = update_section(
        str(doc),
        "Deployment",
        "Updated deployment details.",
    )

    assert result is True

    content = doc.read_text(encoding="utf-8")

    assert "Updated deployment details." in content
    assert "Old deployment details." not in content
    assert "## Authentication" in content


def test_section_not_found(tmp_path):
    doc = tmp_path / "README.md"

    doc.write_text(
        """# Project

## Authentication

Authentication details.
""",
        encoding="utf-8",
    )

    result = update_section(
        str(doc),
        "Database",
        "Database details.",
    )

    assert result is False

    content = doc.read_text(encoding="utf-8")

    assert "Database details." not in content