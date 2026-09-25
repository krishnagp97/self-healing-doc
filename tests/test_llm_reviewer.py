from unittest.mock import MagicMock, patch

from src.llm.reviewer import review_documentation


def test_review_documentation():
    review_item = {
        "heading": "User Service",
        "content": "The get_user function fetches a user by ID.",
        "changed_symbols": [
            {
                "change_type": "modified",
                "symbol": {
                    "id": "sample.py::UserService.get_user",
                    "signature": (
                        "(self, user_id: int, "
                        "include_email: bool = False) -> str"
                    ),
                },
                "previous_signature": "(self, user_id: int) -> str",
            }
        ],
    }

    mock_response = MagicMock()

    mock_response.text = """
Issue:
The documentation does not mention the new include_email parameter.

Suggested update:
Fetches a user by ID, optionally including their email address.
"""

    with patch("src.llm.reviewer.genai.Client") as mock_client:
        mock_client.return_value.models.generate_content.return_value = (
            mock_response
        )

        result = review_documentation(review_item)

    assert "include_email" in result["issue"]
    assert "optionally including their email" in result["suggested_update"]