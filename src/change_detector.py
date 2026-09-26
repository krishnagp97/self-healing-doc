
def detect_changes(old_chunks, new_chunks):
    """Detect added, removed, and modified code symbols."""
    old_by_id = {chunk["id"]: chunk for chunk in old_chunks}
    new_by_id = {chunk["id"]: chunk for chunk in new_chunks}

    old_ids = set(old_by_id)
    new_ids = set(new_by_id)

    added = [new_by_id[symbol_id] for symbol_id in sorted(new_ids - old_ids)]
    removed = [old_by_id[symbol_id] for symbol_id in sorted(old_ids - new_ids)]

    modified = []

    fields_to_compare = ("type", "signature", "docstring")

    for symbol_id in sorted(old_ids & new_ids):
        old_chunk = old_by_id[symbol_id]
        new_chunk = new_by_id[symbol_id]

        fields = fields_to_compare

        if old_chunk.get("type") != "class":
            fields = fields + ("body",)

        if any(
            old_chunk.get(field) != new_chunk.get(field)
            for field in fields
        ):
            modified.append({
                "old": old_chunk,
                "new": new_chunk,
            })


    return {
        "added": added,
        "removed": removed,
        "modified": modified,
    }