
def find_affected_docs(changes, old_links, new_links):
    """Find documentation sections linked to changed code symbols."""
    changed_ids = set()

    for chunk in changes["added"]:
        changed_ids.add(chunk["id"])

    for chunk in changes["removed"]:
        changed_ids.add(chunk["id"])

    for change in changes["modified"]:
        changed_ids.add(change["new"]["id"])

    affected_docs = set()

    for link in old_links + new_links:
        if link["code_id"] in changed_ids:
            affected_docs.add(link["doc_id"])

    return sorted(affected_docs)