
from src.staleness_verifier import prepare_review_items


def test_prepare_review_items():
    sections = [
        {
            "id": "README.md::get_user",
            "heading": "get_user",
            "content": "Fetches a user.",
        },
        {
            "id": "README.md::delete_user",
            "heading": "delete_user",
            "content": "Deletes a user.",
        },
    ]

    changes = {
        "added": [
            {
                "id": "app.py::delete_user",
                "type": "function",
                "signature": "(user_id: int)",
                "docstring": "Delete a user",
            }
        ],
        "removed": [],
        "modified": [
            {
                "old": {
                    "id": "app.py::get_user",
                    "signature": "(user_id: str)",
                },
                "new": {
                    "id": "app.py::get_user",
                    "signature": "(user_id: int)",
                },
            }
        ],
    }

    old_links = [
        {
            "doc_id": "README.md::get_user",
            "code_id": "app.py::get_user",
        }
    ]

    new_links = [
        {
            "doc_id": "README.md::get_user",
            "code_id": "app.py::get_user",
        },
        {
            "doc_id": "README.md::delete_user",
            "code_id": "app.py::delete_user",
        },
    ]

    items = prepare_review_items(
        sections,
        changes,
        ["README.md::get_user", "README.md::delete_user"],
        old_links,
        new_links,
    )

    by_heading = {item["heading"]: item for item in items}

    assert by_heading["get_user"]["status"] == "needs_llm_review"
    assert len(by_heading["get_user"]["changed_symbols"]) == 1
    assert (
        by_heading["get_user"]["changed_symbols"][0]["change_type"]
        == "modified"
    )
    assert (
        by_heading["get_user"]["changed_symbols"][0]["previous_signature"]
        == "(user_id: str)"
    )

    assert len(by_heading["delete_user"]["changed_symbols"]) == 1
    assert (
        by_heading["delete_user"]["changed_symbols"][0]["change_type"]
        == "added"
    )