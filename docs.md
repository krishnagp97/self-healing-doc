# Documentation

This project automatically detects documentation that may become outdated after code changes.

## update_section

Updates the content of a Markdown documentation section identified by its heading. Supports configurable heading levels (defaulting to 2) and a dry-run mode to simulate changes without modifying the file.

Returns `True` if the section was found and updated (or would be updated when `dry_run` is enabled), and `False` if the section title is not found in the document. Raises `FileNotFoundError` if the specified file path does not exist.

## Action Test

This section is used to verify the reusable GitHub Action.