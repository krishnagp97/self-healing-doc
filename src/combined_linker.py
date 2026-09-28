from src.linker import link_sections
from src.llm.linker import semantic_link_sections


def link_all_sections(sections, chunks):
    """
    Run deterministic linking first and semantic linking only
    for sections that could not be resolved deterministically.
    """

    deterministic = link_sections(
        sections,
        chunks,
    )

    deterministic_links = deterministic["links"]
    unmatched = set(deterministic["unmatched"])

    ambiguous = deterministic["ambiguous"]

    ambiguous_ids = {
        item["doc_id"]
        for item in ambiguous
    }

    # Semantic linking is only needed for unresolved or
    # ambiguous sections.
    semantic_section_ids = unmatched | ambiguous_ids

    semantic_sections = [
        section
        for section in sections
        if section["id"] in semantic_section_ids
    ]

    semantic_links = []
    semantic_unresolved = []

    if semantic_sections:
        semantic_result = semantic_link_sections(
            semantic_sections,
            chunks,
        )

        semantic_links = semantic_result["links"]
        semantic_unresolved = semantic_result["unresolved"]

    return {
        "links": deterministic_links + semantic_links,
        "unmatched": semantic_unresolved,
        "ambiguous": ambiguous,
    }