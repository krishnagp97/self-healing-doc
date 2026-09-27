# Self-Healing Docs

Automatically detect stale documentation after merged pull requests, review the changes with Gemini, and create a documentation pull request with the required updates.

## What it does

Self-Healing Docs runs after a pull request is merged and checks whether the code changes have made existing documentation outdated.

It:

1. Scans the old and new versions of the repository.
2. Detects added, removed, and modified code symbols.
3. Links code symbols to relevant documentation sections.
4. Identifies documentation affected by the code changes.
5. Uses Gemini to review whether the documentation needs an update.
6. Updates the affected documentation when necessary.
7. Creates a separate pull request containing the documentation changes.

If the AI review fails, the action does not modify the documentation. Instead, it comments on the original pull request so the failure is visible to the developer.

## How it works

Merged Pull Request
        │
        ▼
Scan Repository Changes
        │
        ▼
Detect Code Changes
        │
        ▼
Find Affected Documentation
        │
        ▼
Gemini AI Review
        │
        ├── Documentation is up to date
        │          │
        │          ▼
        │      No changes
        │
        └── Documentation is stale
                   │
                   ▼
            Update Documentation
                   │
                   ▼
          Create Documentation PR


## Features

- Supports multiple programming languages through Tree-sitter.
- Updates only affected documentation sections.
- Creates a separate pull request for documentation updates.
- Comments on the original pull request when AI review fails.
- Retries failed AI review requests before reporting an error.
- Works as a reusable GitHub Action across repositories.
- Uses the GitHub pull request diff between the base and merge commits for analysis.


## Supported Languages

Self-Healing Docs uses Tree-sitter to analyze source code.

Currently supported:

- C++
- Go
- Java
- JavaScript
- Python
- Rust
- TypeScript
- TSX

The documentation analysis is based on code symbols such as functions, classes, and their signatures.

More languages can be added by extending the Tree-sitter scanner.