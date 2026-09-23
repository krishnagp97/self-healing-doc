
from pathlib import Path

from markdown_it import MarkdownIt


def parse_markdown(file_path, root):
    """Split a Markdown file into sections based on headings."""
    file_path = Path(file_path)
    root = Path(root).resolve()

    text = file_path.read_text(encoding="utf-8")
    tokens = MarkdownIt().parse(text)

    relative_path = file_path.resolve().relative_to(root).as_posix()

    sections = []
    current = None

    for i, token in enumerate(tokens):
        if token.type == "heading_open":
            if current:
                sections.append(current)

            inline = tokens[i + 1]
            current = {
                "id": f"{relative_path}::{inline.content}",
                "file": relative_path,
                "heading": inline.content,
                "level": int(token.tag[1]),
                "content": "",
            }

        elif current and token.type == "inline":
            current["content"] += token.content + "\n"

    if current:
        sections.append(current)

    return sections