
class UserService:
    """Manage user records."""

    def get_user(self, user_id: int) -> str:
        """Fetch a user by ID."""
        return f"User {user_id}"

    def delete_user(self, user_id: int, force: bool = False) -> bool:
        """Delete a user record."""
        return True


def create_user(name: str, active: bool = True) -> dict:
    """Create a new user."""
    return {"name": name, "active": active}