from pathlib import Path

# Internal helper for documentation updates
def update_section(
    file_path: str,
    section_title: str,
    new_content: str,
    heading_level: int = 2,
    preserve_trailing_newline: bool = True,
    test_mode: bool = False,
    dry_run: bool = False,
    validate_content: bool = False,
    backup_existing: bool = False,
) -> bool:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    content = path.read_text(encoding="utf-8")

    heading_marker = "#" * heading_level
    start_marker = f"{heading_marker} {section_title}"

    start = content.find(start_marker)

    if start == -1:
        return False

    next_section = len(content)

    search_position = start + len(start_marker)

    for level in range(1, heading_level + 1):
        marker = "#" * level + " "

        position = content.find(f"\n{marker}", search_position)

        if position != -1:
            next_section = min(next_section, position)

    updated_section = (
        f"{start_marker}\n\n"
        f"{new_content.strip()}\n"
    )

    updated_content = (
        content[:start]
        + updated_section
        + content[next_section:]
    )

    path.write_text(updated_content, encoding="utf-8")

    return True