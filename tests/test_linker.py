
from pathlib import Path

from src.scanner import scan_repository
from src.doc_parser import parse_markdown
from src.linker import link_sections
from src.llm.linker import (
    SemanticLinkerError,
    semantic_link_sections,
)
from src.llm.candidates import rank_candidates
from src.combined_linker import link_all_sections
import pytest

def test_link_sections():
    root = Path(__file__).resolve().parents[1] / "fixtures"

    chunks = scan_repository(root)
    sections = parse_markdown(root / "sample.md", root)

    result = link_sections(sections, chunks)

    linked_headings = {
        link["heading"] for link in result["links"]
    }

    assert "get_user" in linked_headings
    assert "delete_user" in linked_headings
    assert result["ambiguous"] == []

def test_headingless_markdown_is_parsed():
    root = Path(__file__).resolve().parents[1] / "fixtures"

    sections = parse_markdown(
        root / "headingless.md",
        root
    )

    assert len(sections) == 1
    assert sections[0]["heading"] == ""
    assert "get_user" in sections[0]["content"]

def test_link_symbol_from_section_content():
    root = Path(__file__).resolve().parents[1] / "fixtures"

    chunks = scan_repository(root)

    sections = [{
        "id": "sample.md::User Management",
        "file": "sample.md",
        "heading": "User Management",
        "level": 1,
        "content": "The get_user function retrieves a user.",
    }]

    result = link_sections(sections, chunks)

    symbols = {
        link["symbol"]
        for link in result["links"]
    }

    assert "UserService.get_user" in symbols


def test_multiple_symbols_in_one_section():
    root = Path(__file__).resolve().parents[1] / "fixtures"

    chunks = scan_repository(root)

    sections = [{
        "id": "sample.md::User Management",
        "file": "sample.md",
        "heading": "User Management",
        "level": 1,
        "content": (
            "The get_user function retrieves a user. "
            "The delete_user function removes a user."
        ),
    }]

    result = link_sections(sections, chunks)

    symbols = {
        link["symbol"]
        for link in result["links"]
    }

    assert "UserService.get_user" in symbols
    assert "UserService.delete_user" in symbols


def test_function_call_reference():
    root = Path(__file__).resolve().parents[1] / "fixtures"

    chunks = scan_repository(root)

    sections = [{
        "id": "sample.md::User",
        "file": "sample.md",
        "heading": "User",
        "level": 1,
        "content": "Call get_user() to retrieve the user.",
    }]

    result = link_sections(sections, chunks)

    symbols = {
        link["symbol"]
        for link in result["links"]
    }

    assert "UserService.get_user" in symbols


def test_symbol_boundary():
    root = Path(__file__).resolve().parents[1] / "fixtures"

    chunks = scan_repository(root)

    sections = [{
        "id": "sample.md::Backup",
        "file": "sample.md",
        "heading": "Backup",
        "level": 1,
        "content": "The get_user_backup function is used here.",
    }]

    result = link_sections(sections, chunks)

    assert not any(
        link["symbol"] == "get_user"
        for link in result["links"]
    )

def test_qualified_symbol_reference():
    chunks = [
        {
            "id": "code-1",
            "name": "UserService.get_user",
            "file": "src/user_service.py",
        },
        {
            "id": "code-2",
            "name": "AdminService.get_user",
            "file": "src/admin_service.py",
        },
    ]

    sections = [{
        "id": "docs::Users",
        "file": "docs/users.md",
        "heading": "Users",
        "level": 1,
        "content": "Use UserService.get_user to retrieve a user.",
    }]

    result = link_sections(sections, chunks)

    assert len(result["links"]) == 1
    assert result["links"][0]["symbol"] == "UserService.get_user"
    assert result["ambiguous"] == []


def test_ambiguous_short_symbol():
    chunks = [
        {
            "id": "code-1",
            "name": "UserService.get_user",
            "file": "src/user_service.py",
        },
        {
            "id": "code-2",
            "name": "AdminService.get_user",
            "file": "src/admin_service.py",
        },
    ]

    sections = [{
        "id": "docs::Users",
        "file": "docs/users.md",
        "heading": "Users",
        "level": 1,
        "content": "The get_user function retrieves a user.",
    }]

    result = link_sections(sections, chunks)

    assert result["links"] == []
    assert len(result["ambiguous"]) == 1
    assert set(result["ambiguous"][0]["code_ids"]) == {
        "code-1",
        "code-2",
    }

def test_semantic_linker_failure_is_explicit(monkeypatch):
    sections = [{
        "id": "docs::Users",
        "file": "docs/users.md",
        "heading": "Users",
        "level": 1,
        "content": "This function retrieves a user using an ID.",
    }]

    chunks = [{
        "id": "code-1",
        "name": "UserService.get_user",
        "file": "src/user_service.py",
    }]

    def failing_gemini(prompt):
        raise SemanticLinkerError(
            "Gemini quota or rate limit has been exceeded."
        )

    monkeypatch.setattr(
        "src.llm.linker._call_gemini",
        failing_gemini,
    )

    with pytest.raises(SemanticLinkerError) as exc_info:
        semantic_link_sections(sections, chunks)

    assert "quota or rate limit" in str(exc_info.value)

def test_rank_candidates_by_name_overlap():
    section = {
        "heading": "User retrieval",
        "content": "This function retrieves a user using an ID.",
    }

    chunks = [
        {
            "id": "1",
            "name": "UserService.get_user",
            "file": "src/user_service.py",
        },
        {
            "id": "2",
            "name": "PaymentService.process_payment",
            "file": "src/payment_service.py",
        },
        {
            "id": "3",
            "name": "AuthService.login",
            "file": "src/auth.py",
        },
    ]

    candidates = rank_candidates(section, chunks)

    assert candidates
    assert candidates[0]["id"] == "1"

def test_rank_candidates_respects_limit():
    section = {
        "heading": "User",
        "content": "User related operations.",
    }

    chunks = [
        {
            "id": str(i),
            "name": f"UserService.operation_{i}",
            "file": "src/user_service.py",
        }
        for i in range(20)
    ]

    candidates = rank_candidates(
        section,
        chunks,
        limit=5,
    )

    assert len(candidates) == 5

def test_semantic_linker_success(monkeypatch):
    sections = [{
        "id": "docs::Users",
        "file": "docs/users.md",
        "heading": "User retrieval",
        "level": 1,
        "content": "This function retrieves a user using an ID.",
    }]

    chunks = [
        {
            "id": "code-1",
            "name": "UserService.get_user",
            "file": "src/user_service.py",
        },
        {
            "id": "code-2",
            "name": "PaymentService.process_payment",
            "file": "src/payment_service.py",
        },
    ]

    def fake_gemini(prompt):
        return {
            "matches": [
                {
                    "code_id": "code-1",
                    "confidence": 0.95,
                    "reason": "The documentation describes retrieving a user.",
                }
            ]
        }

    monkeypatch.setattr(
        "src.llm.linker._call_gemini",
        fake_gemini,
    )

    result = semantic_link_sections(
        sections,
        chunks,
    )

    assert result["status"] == "success"
    assert result["unresolved"] == []

    assert len(result["links"]) == 1

    link = result["links"][0]

    assert link["doc_id"] == "docs::Users"
    assert link["code_id"] == "code-1"
    assert link["symbol"] == "UserService.get_user"
    assert link["confidence"] == 0.95
    assert link["source"] == "semantic"

def test_semantic_linker_unresolved(monkeypatch):
    sections = [{
        "id": "docs::Unknown",
        "file": "docs/unknown.md",
        "heading": "Unknown behavior",
        "level": 1,
        "content": "This describes some behavior that is not clearly related to any symbol.",
    }]

    chunks = [
        {
            "id": "code-1",
            "name": "UserService.get_user",
            "file": "src/user_service.py",
        },
        {
            "id": "code-2",
            "name": "PaymentService.process_payment",
            "file": "src/payment_service.py",
        },
    ]

    def fake_gemini(prompt):
        return {
            "matches": []
        }

    monkeypatch.setattr(
        "src.llm.linker._call_gemini",
        fake_gemini,
    )

    result = semantic_link_sections(
        sections,
        chunks,
    )

    assert result["status"] == "success"
    assert result["links"] == []
    assert result["unresolved"] == ["docs::Unknown"]

def test_rank_candidates_uses_fallback():
    section = {
        "heading": "Authentication",
        "content": "Authenticate the user and create a session.",
    }

    chunks = [
        {
            "id": "1",
            "name": "UserService.get_user",
            "file": "src/user_service.py",
        },
        {
            "id": "2",
            "name": "PaymentService.process_payment",
            "file": "src/payment_service.py",
        },
        {
            "id": "3",
            "name": "Database.save_record",
            "file": "src/database.py",
        },
    ]

    candidates = rank_candidates(
        section,
        chunks,
        limit=2,
    )

    assert len(candidates) == 2


def test_rank_candidates_prefers_related_path():
    section = {
        "id": "docs::Users",
        "file": "docs/users.md",
        "heading": "Authentication",
        "level": 1,
        "content": "Authenticate the user.",
    }

    chunks = [
        {
            "id": "payment",
            "name": "PaymentService.process",
            "file": "src/payment/payment_service.py",
        },
        {
            "id": "user",
            "name": "AuthService.login",
            "file": "src/users/auth_service.py",
        },
    ]

    candidates = rank_candidates(
        section,
        chunks,
        limit=2,
    )

    assert candidates[0]["id"] == "user"

def test_combined_linker_keeps_deterministic_match(monkeypatch):
    sections = [{
        "id": "docs::Users",
        "file": "docs/users.md",
        "heading": "User retrieval",
        "level": 1,
        "content": "UserService.get_user retrieves a user.",
    }]

    chunks = [
        {
            "id": "code-1",
            "name": "UserService.get_user",
            "file": "src/user_service.py",
        }
    ]

    def fail_gemini(prompt):
        raise AssertionError(
            "Gemini should not be called for deterministic matches"
        )

    monkeypatch.setattr(
        "src.combined_linker.semantic_link_sections",
        fail_gemini,
    )

    result = link_all_sections(
        sections,
        chunks,
    )

    assert len(result["links"]) == 1
    assert result["links"][0]["code_id"] == "code-1"
    assert result["links"][0]["symbol"] == "UserService.get_user"

def test_combined_linker_uses_semantic_for_unmatched(monkeypatch):
    sections = [{
        "id": "docs::Users",
        "file": "docs/users.md",
        "heading": "User behavior",
        "level": 1,
        "content": "This describes some user behavior.",
    }]

    chunks = [
        {
            "id": "code-1",
            "name": "UserService.get_user",
            "file": "src/user_service.py",
        }
    ]

    def fake_semantic(sections, chunks):
        assert len(sections) == 1
        assert sections[0]["id"] == "docs::Users"

        return {
            "status": "success",
            "links": [{
                "doc_id": "docs::Users",
                "code_id": "code-1",
                "heading": "User behavior",
                "symbol": "UserService.get_user",
                "confidence": 0.95,
                "source": "semantic",
            }],
            "unresolved": [],
        }

    monkeypatch.setattr(
        "src.combined_linker.semantic_link_sections",
        fake_semantic,
    )

    result = link_all_sections(
        sections,
        chunks,
    )

    assert len(result["links"]) == 1

    link = result["links"][0]

    assert link["code_id"] == "code-1"
    assert link["source"] == "semantic"
    assert result["unmatched"] == []

def test_combined_linker_propagates_semantic_failure(monkeypatch):
    sections = [{
        "id": "docs::Unknown",
        "file": "docs/unknown.md",
        "heading": "Unknown behavior",
        "level": 1,
        "content": "This cannot be linked deterministically.",
    }]

    chunks = [
        {
            "id": "code-1",
            "name": "UserService.get_user",
            "file": "src/user_service.py",
        }
    ]

    def failing_semantic(sections, chunks):
        raise SemanticLinkerError(
            "Gemini semantic linking is temporarily unavailable."
        )

    monkeypatch.setattr(
        "src.combined_linker.semantic_link_sections",
        failing_semantic,
    )

    try:
        link_all_sections(
            sections,
            chunks,
        )

        assert False, "Expected SemanticLinkerError"

    except SemanticLinkerError as exc:
        assert "temporarily unavailable" in str(exc)


def test_semantic_linker_quota_failure_is_explicit(monkeypatch):
    sections = [{
        "id": "docs::Users",
        "file": "docs/users.md",
        "heading": "Users",
        "level": 1,
        "content": "This function retrieves a user using an ID.",
    }]

    chunks = [{
        "id": "code-1",
        "name": "UserService.get_user",
        "file": "src/user_service.py",
    }]

    def failing_gemini(prompt):
        raise SemanticLinkerError(
            "Gemini quota or rate limit has been exceeded."
        )

    monkeypatch.setattr(
        "src.llm.linker._call_gemini",
        failing_gemini,
    )

    with pytest.raises(SemanticLinkerError) as exc_info:
        semantic_link_sections(sections, chunks)

    assert str(exc_info.value) == (
        "Gemini quota or rate limit has been exceeded."
    )