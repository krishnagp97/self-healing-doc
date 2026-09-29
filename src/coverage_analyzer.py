DOCUMENTABLE_TYPES = {
    "function",
    "class",
    "method",
}


def find_undocumented_symbols(changes, sections):
    """Find newly added symbols that have no documentation reference."""

    added_symbols = changes["added"]

    documented_text = "\n".join(
        f"{section['heading']}\n{section['content']}"
        for section in sections
    ).lower()

    undocumented = []

    for symbol in added_symbols:
        if symbol.get("type") not in DOCUMENTABLE_TYPES:
            continue

        name = symbol.get("name", "")

        if not name:
            continue

        short_name = name.split(".")[-1].lower()

        if short_name not in documented_text:
            undocumented.append(symbol)

    return undocumented