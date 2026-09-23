
class UserService:
    """Manage user records."""

    def get_user(
    self,
    user_id: int,
    include_email: bool = False
) -> str:
      """Fetch a user by ID, optionally including email."""
      return f"User {user_id}"

    def delete_user(self, user_id: int, force: bool = False) -> bool:
        """Delete a user record."""
        return True


def create_user(name: str, active: bool = True) -> dict:
    """Create a new user."""
    return {"name": name, "active": active}