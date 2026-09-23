
from src.impact_analyzer import find_affected_docs


def test_find_affected_docs():
    changes = {
        "added": [{"id": "app.py::new_function"}],
        "removed": [{"id": "app.py::old_function"}],
        "modified": [
            {
                "old": {"id": "app.py::update_user"},
                "new": {"id": "app.py::update_user"},
            }
        ],
    }

    old_links = [
        {"doc_id": "README.md::Old function",
         "code_id": "app.py::old_function"},
        {"doc_id": "README.md::Update user",
         "code_id": "app.py::update_user"},
    ]

    new_links = [
        {"doc_id": "README.md::New function",
         "code_id": "app.py::new_function"},
        {"doc_id": "README.md::Update user",
         "code_id": "app.py::update_user"},
    ]

    affected = find_affected_docs(changes, old_links, new_links)

    assert affected == [
        "README.md::New function",
        "README.md::Old function",
        "README.md::Update user",
    ]