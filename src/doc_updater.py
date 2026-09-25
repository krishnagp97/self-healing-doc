from pathlib import Path


def update_section(
    file_path: str,
    section_title: str,
    new_content: str,
) -> bool:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    content = path.read_text(encoding="utf-8")

    start_marker = f"## {section_title}"

    start = content.find(start_marker)

    if start == -1:
        return False

    next_section = content.find("\n## ", start + len(start_marker))

    if next_section == -1:
        next_section = len(content)

    updated_section = f"## {section_title}\n\n{new_content.strip()}\n"

    updated_content = (
        content[:start]
        + updated_section
        + content[next_section:]
    )

    path.write_text(updated_content, encoding="utf-8")

    return True