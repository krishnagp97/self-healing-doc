from src.llm.reviewer import review_documentation


review_item = {
    "heading": "User Service",
    "content": "The get_user function fetches a user by ID.",
    "changed_symbols": [
        {
            "change_type": "modified",
            "symbol": {
                "id": "sample.py::UserService.get_user",
                "signature": "(self, user_id: int, include_email: bool = False) -> str",
            },
            "previous_signature": "(self, user_id: int) -> str",
        }
    ],
}

result = review_documentation(review_item)

print("\nGemini Review")
print("=" * 50)
print("\nIssue:")
print(result["issue"])

print("\nSuggested update:")
print(result["suggested_update"])