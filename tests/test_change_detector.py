
from src.change_detector import detect_changes


def test_detect_changes():
    old_chunks = [
        {
            "id": "app.py::old_function",
            "type": "function",
            "signature": "()",
            "docstring": "Old function",
        },
        {
            "id": "app.py::update_user",
            "type": "function",
            "signature": "(user_id: int)",
            "docstring": "Update a user",
        },
    ]

    new_chunks = [
        {
            "id": "app.py::new_function",
            "type": "function",
            "signature": "()",
            "docstring": "New function",
        },
        {
            "id": "app.py::update_user",
            "type": "function",
            "signature": "(user_id: int, active: bool)",
            "docstring": "Update a user",
        },
    ]

    changes = detect_changes(old_chunks, new_chunks)

    assert [chunk["id"] for chunk in changes["added"]] == [
        "app.py::new_function"
    ]
    assert [chunk["id"] for chunk in changes["removed"]] == [
        "app.py::old_function"
    ]
    assert len(changes["modified"]) == 1
    assert changes["modified"][0]["new"]["id"] == "app.py::update_user"