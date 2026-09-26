from pathlib import Path

from tree_sitter import Language, Parser

import tree_sitter_cpp
import tree_sitter_go
import tree_sitter_java
import tree_sitter_javascript
import tree_sitter_python
import tree_sitter_rust
import tree_sitter_typescript


LANGUAGES = {
    ".py": Language(tree_sitter_python.language()),
    ".js": Language(tree_sitter_javascript.language()),
    ".jsx": Language(tree_sitter_javascript.language()),
    ".ts": Language(tree_sitter_typescript.language_typescript()),
    ".tsx": Language(tree_sitter_typescript.language_tsx()),
    ".java": Language(tree_sitter_java.language()),
    ".cpp": Language(tree_sitter_cpp.language()),
    ".cc": Language(tree_sitter_cpp.language()),
    ".cxx": Language(tree_sitter_cpp.language()),
    ".go": Language(tree_sitter_go.language()),
    ".rs": Language(tree_sitter_rust.language()),
}


def get_parser(extension):
    """Return a Tree-sitter parser for a supported file extension."""
    language = LANGUAGES.get(extension)

    if language is None:
        return None

    return Parser(language)


def scan_file(file_path):
    """Parse a supported source file with Tree-sitter."""
    file_path = Path(file_path)
    parser = get_parser(file_path.suffix.lower())

    if parser is None:
        return []

    source = file_path.read_bytes()
    tree = parser.parse(source)

    return tree

def extract_signature(source, node):
    """Extract and normalize the declaration/signature of a syntax node."""
    text = source[node.start_byte:node.end_byte].decode("utf-8")

    lines = text.splitlines()

    if not lines:
        return ""

    signature_lines = []

    for line in lines:
        stripped = line.strip()

        if not stripped:
            continue

        signature_lines.append(stripped)

        if stripped.endswith(":") or stripped.endswith("{"):
            break

    signature = " ".join(signature_lines)

    # Normalize whitespace around parentheses for cleaner signatures.
    signature = signature.replace("( ", "(")
    signature = signature.replace(" )", ")")

    return signature

SYMBOL_NODE_TYPES = {
    ".py": {
        "class": "class_definition",
        "function": "function_definition",
        "method": "function_definition",
    },
    ".js": {
        "class": "class_declaration",
        "function": "function_declaration",
        "method": "method_definition",
    },
    ".jsx": {
        "class": "class_declaration",
        "function": "function_declaration",
        "method": "method_definition",
    },
    ".ts": {
        "class": "class_declaration",
        "function": "function_declaration",
        "method": "method_definition",
    },
    ".tsx": {
        "class": "class_declaration",
        "function": "function_declaration",
        "method": "method_definition",
    },
    
    ".java": {
        "class": "class_declaration",
        "function": "method_declaration",
        "method": "method_declaration",
    },
    
    ".cpp": {
        "class": "class_specifier",
        "function": "function_definition",
        "method": "function_definition",
    },
    ".cc": {
        "class": "class_specifier",
        "function": "function_definition",
        "method": "function_definition",
    },
    ".cxx": {
        "class": "class_specifier",
        "function": "function_definition",
        "method": "function_definition",
    },
    
    ".go": {
        "class": "type_spec",
        "function": "function_declaration",
        "method": "method_declaration",
    },
    
    ".rs": {
        "class": "struct_item",
        "function": "function_item",
        "method": "function_item",
    },
}


def extract_docstring(source, node, extension):
    """Extract a documentation string from a symbol."""
    if extension != ".py":
        return ""

    body = node.child_by_field_name("body")

    if body is None or not body.children:
        return ""

    first_statement = body.children[0]

    if first_statement.type != "expression_statement":
        return ""

    string_node = first_statement.children[0]

    if string_node.type != "string":
        return ""

    text = source[
        string_node.start_byte:string_node.end_byte
    ].decode("utf-8")

    try:
        import ast

        return ast.literal_eval(text)
    except (SyntaxError, ValueError):
        return ""

def extract_symbols(file_path):
    """Extract classes, functions, and methods from a source file."""
    file_path = Path(file_path)
    extension = file_path.suffix.lower()

    parser = get_parser(extension)
    node_types = SYMBOL_NODE_TYPES.get(extension)

    if parser is None or node_types is None:
        return []

    source = file_path.read_bytes()
    tree = parser.parse(source)

    symbols = []

    class_node_type = node_types["class"]
    function_node_type = node_types["function"]
    method_node_type = node_types["method"]

    def walk(node, parent=None):
        node_type = node.type

        # Rust methods are nested inside impl blocks.
        if extension == ".rs" and node_type == "impl_item":
            type_node = node.child_by_field_name("type")

            if type_node:
                parent = source[
                    type_node.start_byte:type_node.end_byte
                ].decode("utf-8")

        is_symbol = node_type in {
            class_node_type,
            function_node_type,
            method_node_type,
        }

        if is_symbol:
            name_node = node.child_by_field_name("name")
            go_parent = None

            # Go methods are linked to their receiver type.
            if extension == ".go" and node_type == "method_declaration":
                receiver = node.child_by_field_name("receiver")

                if receiver:
                    receiver_text = source[
                        receiver.start_byte:receiver.end_byte
                    ].decode("utf-8").strip("() ")

                    receiver_parts = receiver_text.split()

                    if receiver_parts:
                        go_parent = receiver_parts[-1].lstrip("*")

            # C++ stores function names inside nested declarators.
            if (
                extension in {".cpp", ".cc", ".cxx"}
                and node_type == "function_definition"
            ):
                declarator = node.child_by_field_name("declarator")

                while declarator and declarator.type in {
                    "function_declarator",
                    "pointer_declarator",
                    "reference_declarator",
                }:
                    nested = declarator.child_by_field_name("declarator")

                    if nested is None:
                        break

                    declarator = nested

                if declarator:
                    name_node = declarator

            if name_node:
                name = source[
                    name_node.start_byte:name_node.end_byte
                ].decode("utf-8")

                effective_parent = go_parent or parent
                full_name = (
                    f"{effective_parent}.{name}"
                    if effective_parent
                    else name
                )

                symbol_type = (
                    "class"
                    if node_type == class_node_type
                    else "function"
                )

                symbols.append({
                    "name": full_name,
                    "type": symbol_type,
                    "file": file_path.as_posix(),
                    "line": node.start_point[0] + 1,
                    "end_line": node.end_point[0] + 1,
                    "signature": extract_signature(source, node),
                    "body": source[node.start_byte:node.end_byte].decode("utf-8"),
                    "docstring": extract_docstring(source, node, extension),
                })

                parent = full_name

        for child in node.children:
            walk(child, parent)

    walk(tree.root_node)

    return symbols


def scan_repository(root_path):
    """Scan a repository using Tree-sitter."""
    root = Path(root_path).resolve()
    chunks = []

    ignored = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        "node_modules",
        "dist",
        "build",
        "tests",
        "temp-old",
        "temp-new",
    }

    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue

        relative_path = file_path.relative_to(root)

        if any(part in ignored for part in relative_path.parts):
            continue

        if file_path.suffix.lower() not in LANGUAGES:
            continue

        try:
            symbols = extract_symbols(file_path)

            for symbol in symbols:
                symbol["id"] = (
                    f"{relative_path.as_posix()}::{symbol['name']}"
                )

                symbol["file"] = relative_path.as_posix()

                chunks.append(symbol)

        except (UnicodeDecodeError, OSError) as error:
            print(f"Skipping {file_path}: {error}")

    return chunks

