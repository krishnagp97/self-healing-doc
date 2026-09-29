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


def find_potentially_affected_docs(changes, sections):
    """Find documentation sections that mention changed symbols."""

    changed_symbols = []

    for symbol in changes["added"]:
        changed_symbols.append(symbol)

    for symbol in changes["removed"]:
        changed_symbols.append(symbol)

    for change in changes["modified"]:
        changed_symbols.append(change["new"])

    affected = []

    for section in sections:
        text = (
            f"{section['heading']}\n"
            f"{section['content']}"
        ).lower()

        for symbol in changed_symbols:
            name = symbol.get("name", "")

            if not name:
                continue

            short_name = name.split(".")[-1].lower()

            if short_name in text:
                affected.append(section["id"])
                break

    return sorted(set(affected))