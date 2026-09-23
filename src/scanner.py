
import ast
from pathlib import Path


def get_signature(node):
    """Return a readable function signature."""
    args = node.args
    parts = []

    positional = args.posonlyargs + args.args
    defaults = [None] * (len(positional) - len(args.defaults)) + args.defaults

    for arg, default in zip(positional, defaults):
        text = arg.arg

        if arg.annotation:
            text += f": {ast.unparse(arg.annotation)}"

        if default:
            text += f" = {ast.unparse(default)}"

        parts.append(text)

    if args.vararg:
        parts.append(f"*{args.vararg.arg}")

    elif args.kwonlyargs:
        parts.append("*")

    for arg, default in zip(args.kwonlyargs, args.kw_defaults):
        text = arg.arg

        if arg.annotation:
            text += f": {ast.unparse(arg.annotation)}"

        if default:
            text += f" = {ast.unparse(default)}"

        parts.append(text)

    if args.kwarg:
        parts.append(f"**{args.kwarg.arg}")

    signature = ", ".join(parts)
    signature = f"({signature})"

    if node.returns:
       signature += f" -> {ast.unparse(node.returns)}"

    return signature


def scan_file(file_path, root):
    """Extract classes and functions from one Python file."""
    source = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(file_path))

    chunks = []
    relative_path = file_path.relative_to(root).as_posix()

    def visit(node, parent=""):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = f"{parent}.{node.name}" if parent else node.name

            chunks.append({
                "id": f"{relative_path}::{name}",
                "type": "function",
                "name": name,
                "file": relative_path,
                "line": node.lineno,
                "end_line": node.end_lineno,
                "signature": get_signature(node),
                "docstring": ast.get_docstring(node) or "",
            })

            # Include methods nested inside functions only if needed later.
            return

        if isinstance(node, ast.ClassDef):
            name = f"{parent}.{node.name}" if parent else node.name

            chunks.append({
                "id": f"{relative_path}::{name}",
                "type": "class",
                "name": name,
                "file": relative_path,
                "line": node.lineno,
                "end_line": node.end_lineno,
                "signature": "",
                "docstring": ast.get_docstring(node) or "",
            })

            for child in node.body:
                visit(child, name)

            return

        if isinstance(node, ast.Module):
            for child in node.body:
                visit(child, parent)

    visit(tree)
    return chunks


def scan_repository(root_path):
    """Scan a repository and return all discovered code chunks."""
    root = Path(root_path).resolve()
    chunks = []

    ignored = {
        ".git", ".venv", "venv", "__pycache__",
        "node_modules", "dist", "build",
    }

    for file_path in root.rglob("*.py"):
        if any(part in ignored for part in file_path.parts):
            continue

        try:
            chunks.extend(scan_file(file_path, root))
        except (SyntaxError, UnicodeDecodeError) as error:
            print(f"Skipping {file_path}: {error}")

    return chunks