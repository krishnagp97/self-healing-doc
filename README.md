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

```text
Merged Pull Request
        |
        v
Scan Repository Changes
        |
        v
Detect Code Changes
        |
        v
Find Affected Documentation
        |
        v
Gemini AI Review
        |
        +---- Review succeeds
        |          |
        |          +---- Documentation is up to date
        |          |             |
        |          |             v
        |          |         No changes
        |          |
        |          +---- Documentation is stale
        |                        |
        |                        v
        |                 Update Documentation
        |                        |
        |                        v
        |                Create Documentation PR
        |
        +---- Review fails
                   |
                   v
          Comment on Original PR
                   |
                   v
              No Changes
```

## Features

- Supports multiple programming languages through Tree-sitter.
- Updates only affected documentation sections.
- Creates a separate pull request for documentation updates.
- Comments on the original pull request when AI review fails.
- Retries failed AI review requests before reporting an error.
- Works as a reusable GitHub Action across repositories.
- Compares the repository state between the pull request's base and merge commits.


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

## Requirements

- GitHub repository with GitHub Actions enabled.
- GitHub Actions workflow with `contents: write` and `pull-requests: write` permissions.
- Gemini API key.
- Repository code written in a supported language.
- `actions/checkout@v4` in the workflow.


## Usage

Self-Healing Docs is distributed as a reusable GitHub Action.

Add the action to a GitHub Actions workflow:

```yaml
- name: Run Self-Healing Docs
  uses: krishnagp97/self-healing-doc@v1
  with:
    gemini-api-key: ${{ secrets.GEMINI_API_KEY }}
    github-token: ${{ github.token }}
```

See [QUICKSTART.md](QUICKSTART.md) for setup instructions.


## Project Structure

```text
self-healing-doc/
├── .github/
│   └── workflows/
│       └── test-action.yml
├── fixtures/
│   ├── multilang/
│   │   ├── sample.cpp
│   │   ├── sample.go
│   │   ├── sample.java
│   │   ├── sample.js
│   │   ├── sample.rs
│   │   ├── sample.ts
│   │   └── sample.tsx
│   ├── sample.md
│   └── sample.py
├── src/
│   ├── __init__.py
│   ├── change_detector.py
│   ├── doc_parser.py
│   ├── doc_updater.py
│   ├── graph.py
│   ├── impact_analyzer.py
│   ├── linker.py
│   ├── main.py
│   ├── scanner.py
│   ├── staleness_verifier.py
│   ├── tree_sitter_scanner.py
│   └── llm/
│       ├── __init__.py
│       └── reviewer.py
├── tests/
│   ├── fixtures/
│   │   ├── new/
│   │   │   ├── sample.md
│   │   │   └── sample.py
│   │   └── old/
│   │       ├── sample.md
│   │       └── sample.py
│   ├── manual_llm_test.py
│   ├── test_change_detector.py
│   ├── test_doc_parser.py
│   ├── test_doc_updater.py
│   ├── test_graph.py
│   ├── test_impact_analyzer.py
│   ├── test_linker.py
│   ├── test_llm_reviewer.py
│   ├── test_main.py
│   ├── test_scanner.py
│   ├── test_staleness_verifier.py
│   └── test_tree_sitter_scanner.py
├── .gitignore
├── action.yml
├── Dockerfile
├── docs.md
├── entrypoint.sh
├── README.md
├── QUICKSTART.md
└── requirements.txt
```


## How Documentation Is Linked

Self-Healing Docs connects source code symbols with documentation sections by analyzing references between them.

It uses:

- Code symbols such as functions, classes, and methods.
- Documentation sections and the code symbols they reference.
- Changes between the pull request's base and merge commits.

When a code symbol changes, the action uses these relationships to identify the documentation sections that may have become stale.


## AI Review Behavior

Gemini reviews the affected documentation before any changes are made.

- If the documentation is up to date, no changes are made.
- If the documentation is stale, only the affected sections are updated.
- If the AI review fails, the documentation is not modified.
- Failed AI requests are retried before the action reports an error.
- When the AI review cannot be completed, the action comments on the original pull request.

## Testing

The project includes automated tests covering the main components of the action.

```bash
python -m pytest -q
```

The test suite covers:

- Repository scanning
- Change detection
- Documentation parsing
- Code-documentation linking
- Impact analysis
- Documentation updates
- Staleness verification
- Tree-sitter multi-language scanning
- Gemini review
- End-to-end action behavior

The action has also been tested in a separate external GitHub repository with merged pull requests, including successful documentation updates, AI review failures, and non-Python source files.



