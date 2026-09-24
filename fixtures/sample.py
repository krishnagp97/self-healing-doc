class UserService:
    """Manage user records."""

    def get_user(
        self,
        user_id: int,
        include_email: bool = False,
        include_phone: bool = False,
        include_address: bool = False
    ) -> str:
       """Fetch a user by ID, optionally including email and phone."""
       return f"User {user_id}"

    def delete_user(self, user_id: int, force: bool = False) -> bool:
        """Delete a user record."""
        return True

    def update_user(self, user_id: int, name: str) -> bool:
        """Update a user's name."""
        return True


def create_user(
    name: str,
    active: bool = True,
    role: str = "user"
) -> dict:
    """Create a new user."""
    return {
    "name": name,
    "active": active,
    "role": role,
}