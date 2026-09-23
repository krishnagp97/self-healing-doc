
def link_sections(sections, chunks):
    """Link Markdown sections to code symbols using exact names."""
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
            links.append({
                "doc_id": section["id"],
                "code_id": matches[0]["id"],
                "heading": section["heading"],
                "symbol": matches[0]["name"],
            })
        elif len(matches) == 0:
            unmatched.append(section["id"])
        else:
            ambiguous.append({
                "doc_id": section["id"],
                "heading": section["heading"],
                "code_ids": [chunk["id"] for chunk in matches],
            })

    return {
        "links": links,
        "unmatched": unmatched,
        "ambiguous": ambiguous,
    }