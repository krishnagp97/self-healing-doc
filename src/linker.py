from pathlib import Path
import re


def _symbol_variants(name):
    """Return useful variants of a code symbol name."""

    short_name = name.split(".")[-1]

    return {
        name.lower(),
        short_name.lower(),
    }


def _find_explicit_symbols(text, chunks):
    """Find code symbols explicitly mentioned in Markdown text."""

    text = text.lower()

    matches = []
    seen = set()
    qualified_ranges = []

    

    for chunk in chunks:
        full_name = chunk["name"].lower()

        if "." not in full_name:
            continue

        pattern = rf"(?<![a-zA-Z0-9_]){re.escape(full_name)}(?![a-zA-Z0-9_])"

        for match in re.finditer(pattern, text):
            qualified_ranges.append(
                (match.start(), match.end())
            )

            if chunk["id"] not in seen:
                matches.append(chunk)
                seen.add(chunk["id"])

    

    for chunk in chunks:
        short_name = chunk["name"].split(".")[-1].lower()

        pattern = rf"(?<![a-zA-Z0-9_]){re.escape(short_name)}(?![a-zA-Z0-9_])"

        for match in re.finditer(pattern, text):

            
            inside_qualified = any(
                start <= match.start() and match.end() <= end
                for start, end in qualified_ranges
            )

            if inside_qualified:
                continue

            if chunk["id"] not in seen:
                matches.append(chunk)
                seen.add(chunk["id"])

    return matches


def _resolve_ambiguity(section, matches):
    """Resolve duplicate symbol names using documentation path."""

    if len(matches) == 1:
        return matches[0]

    doc_directory = Path(section["file"]).parent

    same_directory = [
        chunk
        for chunk in matches
        if Path(chunk["file"]).parent == doc_directory
    ]

    if len(same_directory) == 1:
        return same_directory[0]

    return None


def link_sections(sections, chunks):
    """Link Markdown sections to explicitly referenced code symbols."""

    links = []
    unmatched = []
    ambiguous = []

    for section in sections:

        # Search both the heading and body.
        text = f"{section['heading']}\n{section['content']}"

        matches = _find_explicit_symbols(text, chunks)

        if not matches:
            unmatched.append(section["id"])
            continue

        # Group matches by short symbol name.
        grouped = {}

        for chunk in matches:
            short_name = chunk["name"].split(".")[-1].lower()
            grouped.setdefault(short_name, []).append(chunk)

        section_linked = False

        for symbol_matches in grouped.values():

            selected = _resolve_ambiguity(
                section,
                symbol_matches,
            )

            if selected:
                links.append({
                    "doc_id": section["id"],
                    "code_id": selected["id"],
                    "heading": section["heading"],
                    "symbol": selected["name"],
                })

                section_linked = True

            else:
                ambiguous.append({
                    "doc_id": section["id"],
                    "heading": section["heading"],
                    "code_ids": [
                        chunk["id"]
                        for chunk in symbol_matches
                    ],
                })

        if not section_linked and not any(
            item["doc_id"] == section["id"]
            for item in ambiguous
        ):
            unmatched.append(section["id"])

    return {
        "links": links,
        "unmatched": unmatched,
        "ambiguous": ambiguous,
    }