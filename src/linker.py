from pathlib import Path


def link_sections(sections, chunks):
    """Link Markdown sections to code symbols using name and path context."""

    symbols_by_name = {}

    for chunk in chunks:
        short_name = chunk["name"].split(".")[-1].lower()
        symbols_by_name.setdefault(short_name, []).append(chunk)

    links = []
    unmatched = []
    ambiguous = []

    for section in sections:
        heading = section["heading"].strip().strip("`").lower()
        matches = symbols_by_name.get(heading, [])

        if len(matches) == 1:
            selected = matches[0]

        elif len(matches) > 1:
            doc_directory = Path(section["file"]).parent

            same_directory = [
                chunk
                for chunk in matches
                if Path(chunk["file"]).parent == doc_directory
            ]

            if len(same_directory) == 1:
                selected = same_directory[0]
            else:
                ambiguous.append({
                    "doc_id": section["id"],
                    "heading": section["heading"],
                    "code_ids": [chunk["id"] for chunk in matches],
                })
                continue

        else:
            unmatched.append(section["id"])
            continue

        links.append({
            "doc_id": section["id"],
            "code_id": selected["id"],
            "heading": section["heading"],
            "symbol": selected["name"],
        })

    return {
        "links": links,
        "unmatched": unmatched,
        "ambiguous": ambiguous,
    }