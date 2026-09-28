
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

    print("\nDEBUG ====================")
    print("affected_doc_ids:", affected_doc_ids)
    print("section IDs:", list(section_by_id.keys()))
    print("changed symbol IDs:", list(changed_symbols.keys()))
    print("symbols_by_doc:", symbols_by_doc)
    print("==========================")
    items = []

    for doc_id in affected_doc_ids:
        print(f"\nDEBUG processing doc_id: {doc_id}")
        section = section_by_id.get(doc_id)

        if section is None:
            print("DEBUG -> section NOT FOUND")
            continue
        print("DEBUG -> section FOUND")
        relevant_symbols = [
            changed_symbols[code_id]
            for code_id in sorted(symbols_by_doc.get(doc_id, set()))
        ]
        print("DEBUG -> relevant_symbols:", relevant_symbols)
        if not relevant_symbols:
            continue
        print("DEBUG -> ADDING REVIEW ITEM")
        items.append({
            "doc_id": doc_id,
            "file": section["file"],
            "heading": section["heading"],
            "heading_level": section["level"],
            "content": section["content"],
            "status": "needs_llm_review",
            "changed_symbols": relevant_symbols,
            
        })
        print("\nDEBUG final items:", items)

    return items