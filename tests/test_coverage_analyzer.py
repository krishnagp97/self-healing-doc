from src.coverage_analyzer import find_undocumented_symbols


def test_finds_new_undocumented_function():
    changes = {
        "added": [
            {
                "id": "backend/cache.js::getCachedUser",
                "name": "getCachedUser",
                "type": "function",
            }
        ],
        "removed": [],
        "modified": [],
    }

    sections = [
        {
            "id": "readme.md::users",
            "heading": "Users",
            "content": "The getUser function retrieves users.",
        }
    ]

    result = find_undocumented_symbols(
        changes,
        sections,
    )

    assert len(result) == 1
    assert result[0]["name"] == "getCachedUser"


def test_ignores_documented_function():
    changes = {
        "added": [
            {
                "id": "backend/cache.js::getCachedUser",
                "name": "getCachedUser",
                "type": "function",
            }
        ],
        "removed": [],
        "modified": [],
    }

    sections = [
        {
            "id": "readme.md::users",
            "heading": "Users",
            "content": "The getCachedUser function retrieves users from cache.",
        }
    ]

    result = find_undocumented_symbols(
        changes,
        sections,
    )

    assert result == []


def test_ignores_non_documentable_symbols():
    changes = {
        "added": [
            {
                "id": "backend/cache.js::CACHE_SIZE",
                "name": "CACHE_SIZE",
                "type": "variable",
            }
        ],
        "removed": [],
        "modified": [],
    }

    sections = []

    result = find_undocumented_symbols(
        changes,
        sections,
    )

    assert result == []

def test_detects_new_function_without_documentation():
    changes = {
        "added": [
            {
                "id": "backend/cache.js::getCachedUser",
                "name": "getCachedUser",
                "type": "function",
                "signature": "function getCachedUser(id) {}",
            }
        ],
        "removed": [],
        "modified": [],
    }

    sections = [
        {
            "id": "readme.md::users",
            "heading": "Users",
            "content": (
                "The getUser function retrieves a user "
                "from the database."
            ),
        }
    ]

    result = find_undocumented_symbols(
        changes,
        sections,
    )

    assert len(result) == 1
    assert result[0]["id"] == "backend/cache.js::getCachedUser"