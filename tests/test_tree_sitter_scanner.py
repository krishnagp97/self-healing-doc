
from src.tree_sitter_scanner import extract_symbols


def test_extract_javascript_symbols():
    symbols = extract_symbols("fixtures/multilang/sample.js")

    by_name = {symbol["name"]: symbol for symbol in symbols}

    assert "UserService" in by_name
    assert "UserService.getUser" in by_name
    assert "UserService.deleteUser" in by_name
    assert "createUser" in by_name

    assert by_name["UserService"]["type"] == "class"
    assert "getUser" in by_name["UserService.getUser"]["body"]
    assert by_name["UserService.getUser"]["signature"] == (
        "getUser(userId, includeEmail = false) {"
    )
    assert by_name["createUser"]["line"] == 9


def test_extract_java_symbols():
    symbols = extract_symbols("fixtures/multilang/Sample.java")

    by_name = {symbol["name"]: symbol for symbol in symbols}

    assert "UserService" in by_name
    assert "UserService.getUser" in by_name
    assert "UserService.deleteUser" in by_name
    assert "UserController" in by_name
    assert "UserController.createUser" in by_name

    assert by_name["UserService"]["type"] == "class"
    assert by_name["UserService.getUser"]["signature"] == (
        "String getUser(int userId) {"
    )
    assert by_name["UserController.createUser"]["line"] == 13


def test_extract_cpp_symbols():
    symbols = extract_symbols("fixtures/multilang/sample.cpp")

    by_name = {symbol["name"]: symbol for symbol in symbols}

    assert "UserService" in by_name
    assert "UserService.getUser" in by_name
    assert "UserService.deleteUser" in by_name
    assert "createUser" in by_name

    assert by_name["UserService"]["type"] == "class"
    assert by_name["UserService.getUser"]["signature"] == (
        "int getUser(int userId) {"
    )
    assert by_name["createUser"]["line"] == 13


def test_extract_go_symbols():
    symbols = extract_symbols("fixtures/multilang/sample.go")

    by_name = {symbol["name"]: symbol for symbol in symbols}

    assert "UserService" in by_name
    assert "UserService.GetUser" in by_name
    assert "UserService.DeleteUser" in by_name
    assert "CreateUser" in by_name

    assert by_name["UserService"]["type"] == "class"
    assert by_name["UserService.GetUser"]["signature"] == (
        "func (u UserService) GetUser(userID int) string {"
    )
    assert by_name["CreateUser"]["line"] == 14


def test_extract_rust_symbols():
    symbols = extract_symbols("fixtures/multilang/sample.rs")

    by_name = {symbol["name"]: symbol for symbol in symbols}

    assert "UserService" in by_name
    assert "UserService.get_user" in by_name
    assert "UserService.delete_user" in by_name
    assert "create_user" in by_name

    assert by_name["UserService"]["type"] == "class"
    assert by_name["UserService.get_user"]["signature"] == (
        "fn get_user(user_id: i32) -> String {"
    )
    assert by_name["create_user"]["line"] == 14


def test_extract_typescript_symbols():
    symbols = extract_symbols("fixtures/multilang/sample.ts")

    by_name = {symbol["name"]: symbol for symbol in symbols}

    assert "UserService" in by_name
    assert "UserService.getUser" in by_name
    assert "createUser" in by_name

    assert by_name["UserService"]["type"] == "class"
    assert by_name["UserService.getUser"]["signature"] == (
        "getUser(userId: number): string {"
    )
    assert by_name["createUser"]["line"] == 8


def test_extract_tsx_symbols():
    symbols = extract_symbols("fixtures/multilang/sample.tsx")

    by_name = {symbol["name"]: symbol for symbol in symbols}

    assert "UserCard" in by_name

    assert by_name["UserCard"]["signature"] == (
        "function UserCard(user: User): string {"
    )
    assert by_name["UserCard"]["line"] == 6