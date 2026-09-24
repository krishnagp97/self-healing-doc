
from pathlib import Path

from src.scanner import scan_repository


def test_scan_repository():
    root = Path(__file__).resolve().parents[1] / "fixtures"
    chunks = scan_repository(root)

    by_name = {chunk["name"]: chunk for chunk in chunks}

    assert "UserService" in by_name
    assert "UserService.get_user" in by_name
    assert "UserService.delete_user" in by_name
    assert "create_user" in by_name

    assert by_name["UserService.get_user"]["signature"] == (
    "(self, user_id: int, include_email: bool = False) -> str"
    )
    assert by_name["create_user"]["docstring"] == "Create a new user."
    assert by_name["UserService"]["type"] == "class"