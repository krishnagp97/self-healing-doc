
def prepare_review_items(sections, changes, affected_doc_ids, old_links, new_links):
    """Prepare review items with only the relevant changed symbols."""
    section_by_id = {section["id"]: section for section in sections}

    changed_symbols = {}

    for chunk in changes["added"]:
        changed_symbols[chunk["id"]] = {
            "change_type": "added",
            "symbol": chunk,
        }

    for chunk in changes["removed"]:
        changed_symbols[chunk["id"]] = {
            "change_type": "removed",
            "symbol": chunk,
        }

    for change in changes["modified"]:
        symbol = change["new"]
        changed_symbols[symbol["id"]] = {
            "change_type": "modified",
            "symbol": symbol,
            "previous_signature": change["old"].get("signature", ""),
        }

    # Map each documentation section to the changed symbols it references.
    symbols_by_doc = {}

    for link in old_links + new_links:
        code_id = link["code_id"]
        doc_id = link["doc_id"]

        if code_id in changed_symbols:
            symbols_by_doc.setdefault(doc_id, set()).add(code_id)

    items = []

    for doc_id in affected_doc_ids:
        section = section_by_id.get(doc_id)

        if section is None:
            continue

        relevant_symbols = [
            changed_symbols[code_id]
            for code_id in sorted(symbols_by_doc.get(doc_id, set()))
        ]

        if not relevant_symbols:
            continue

        items.append({
            "doc_id": doc_id,
            "file": section["file"],
            "heading": section["heading"],
            "heading_level": section["level"],
            "content": section["content"],
            "status": "needs_llm_review",
            "changed_symbols": relevant_symbols,
            
        })

    return items