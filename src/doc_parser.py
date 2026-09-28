from pathlib import Path

from markdown_it import MarkdownIt


def parse_markdown(file_path, root):
    """Split Markdown into sections while preserving headingless content."""

    file_path = Path(file_path)
    root = Path(root).resolve()

    text = file_path.read_text(encoding="utf-8")
    tokens = MarkdownIt().parse(text)

    relative_path = file_path.resolve().relative_to(root).as_posix()

    sections = []
    current = None
    pre_heading_content = []

    for i, token in enumerate(tokens):

        if token.type == "heading_open":

            # Save the previous section
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

        elif token.type == "inline":

            if current:
                current["content"] += token.content + "\n"
            else:
                # Content before the first heading
                pre_heading_content.append(token.content)

    # Content before the first heading becomes a section
    if pre_heading_content:
        content = "\n".join(pre_heading_content).strip()

        if content:
            sections.insert(0, {
                "id": f"{relative_path}::__root__",
                "file": relative_path,
                "heading": "",
                "level": 0,
                "content": content,
            })

    # Save final heading-based section
    if current:
        sections.append(current)

    return sections