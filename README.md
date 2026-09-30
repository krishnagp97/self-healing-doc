# Self-Healing Docs

Self-Healing Docs is a GitHub Action that automatically detects when code changes may make documentation stale.

After a pull request is merged, it compares the repository before and after the change, identifies affected code symbols, connects those symbols to documentation, and uses Gemini to determine whether the affected documentation needs to be updated.

When an update is required, the action modifies only the affected documentation sections and creates a separate pull request for review.

## Features

* Detects added, removed, and modified code symbols
* Supports C++, Go, Java, JavaScript, Python, Rust, TypeScript, and TSX
* Parses Markdown documentation into individual sections
* Links code symbols to documentation using deterministic and semantic analysis
* Uses Gemini when semantic reasoning is required
* Identifies documentation affected by code changes
* Updates only affected documentation sections
* Handles nested Markdown sections
* Detects potentially undocumented newly added symbols
* Creates separate documentation pull requests
* Falls back safely to a comment when AI analysis cannot be completed

---

## The Problem

Documentation often becomes outdated when code changes.

For example, a function may originally be:

```python
def get_user(user_id):
    ...
```

and the documentation may say:

```text
Fetches a user by ID.
```

Later, the implementation changes:

```python
def get_user(user_id, include_email=False):
    ...
```

The code is updated, but the documentation may still describe the old behavior.

The difficult part is not simply finding changed files. A change in one function may affect a specific section of a README or documentation file somewhere else in the repository.

Self-Healing Docs addresses this by building a relationship between **code symbols and documentation sections** before determining which documentation needs review.

---

## How It Works

The system processes a merged pull request in several stages:

```text
Merged Pull Request
        |
        v
Repository Snapshots
        |
        v
Code Scanning
        |
        v
Change Detection
        |
        v
Documentation Parsing
        |
        v
Code ↔ Documentation Linking
        |
        v
Impact Analysis
        |
        v
Gemini Documentation Review
        |
        +----------------------+
        |                      |
   Documentation           Documentation
    is current               is stale
        |                      |
        v                      v
   No changes           Update affected
                              section
                                |
                                v
                     Create Documentation PR
```

Gemini does **not** blindly review the entire repository.

The system first narrows the problem down to documentation that may actually be affected by the code changes.

---

# 1. Repository Scanning

The first step is extracting structured information from the repository.

Source files are analyzed using **Tree-sitter**.

Instead of treating a source file as plain text, the scanner extracts code symbols such as:

```text
Class
 ├── Method
 ├── Method
 └── Method

Function
Function
```

For example:

```python
class UserService:
    def get_user(self, user_id, include_email=False):
        ...
```

can be represented as a code symbol such as:

```text
UserService.get_user
```

along with information about its file, name, and signature.

This allows the rest of the system to reason about code at the symbol level instead of comparing entire files.

---

# 2. Comparing Old and New Code

The action works with two repository states:

```text
Base Commit
     |
     |  code changes
     v
Merge Commit
```

The scanner analyzes both states and compares their extracted symbols.

The change detector identifies:

* Added symbols
* Removed symbols
* Modified symbols

For example:

```text
Modified:
src/user_service.py::UserService.get_user
```

A change to one method can therefore be traced independently from unrelated changes elsewhere in the repository.

---

# 3. Documentation Parsing

Markdown documentation is parsed into individual sections.

For example:

```markdown
# Users

Fetches a user by ID.

## Authentication

Users must be authenticated before accessing this endpoint.

## API Usage

Use the user endpoint to retrieve account information.
```

is treated as multiple documentation sections rather than one large file.

This allows the system to update:

```text
Users
```

without rewriting:

```text
Authentication
API Usage
```

when those sections are unrelated to the code change.

This approach also allows files such as `README.md` and other Markdown documentation files to participate in the same analysis.

---

# 4. Linking Code to Documentation

The system needs to answer:

> Which code symbols does this documentation section describe?

It first attempts **deterministic linking**.

Explicit references, symbol names, paths, and other available relationships are used to find likely matches.

Conceptually:

```text
Documentation Section
        |
        v
Deterministic Linker
        |
   +----+----+
   |         |
Confident   Unresolved /
  Match     Ambiguous
              |
              v
       Candidate Generation
              |
              v
       Candidate Ranking
              |
              v
      Gemini Semantic Linker
```

Deterministic matching handles straightforward cases, while Gemini is reserved for cases where the relationship requires semantic understanding.

This reduces unnecessary AI calls and keeps the analysis more predictable.

---

# 5. Semantic Linking

Some documentation does not explicitly mention the exact function or class name.

For example, documentation might say:

```text
This section explains how users are retrieved from the system.
```

while the implementation contains:

```text
UserService.get_user
```

A simple string match may not be enough to connect the two.

For unresolved or ambiguous sections, the system generates a limited set of candidate code symbols and sends those candidates to Gemini.

Gemini returns a possible semantic match with a confidence value.

Only sufficiently confident matches are accepted.

Low-confidence matches remain unresolved rather than creating a potentially incorrect relationship.

This keeps the AI component constrained instead of allowing it to arbitrarily associate documentation with source code.

---

# 6. Impact Analysis

Once code symbols have been linked to documentation sections, the system can determine which documentation is affected by a code change.

For example:

```text
Changed:
UserService.get_user
        |
        v
Linked documentation:
README.md → Users
        |
        v
Review required
```

While unrelated documentation is ignored:

```text
README.md → Installation
README.md → Authentication
README.md → Users  ← affected
docs/api.md → Payments
```

Only the relevant section proceeds to the AI review stage.

---

# 7. Gemini Documentation Review

After the affected documentation has been identified, Gemini reviews the relationship between the changed code and the existing documentation.

The reviewer determines whether:

```text
Documentation
      |
      +---- Still accurate
      |        |
      |        v
      |     No update
      |
      +---- Outdated
               |
               v
        Suggested update
```

The AI is therefore used for **reasoning about documentation correctness**, not for deciding which files changed in the first place.

---

# 8. Targeted Documentation Updates

When an update is required, the system updates the affected Markdown section rather than replacing the entire file.

For example:

```markdown
## Users

Fetches a user by ID.
```

can become:

```markdown
## Users

Fetches a user by ID and optionally includes their email.
```

The surrounding documentation remains unchanged.

Nested Markdown headings are also handled so that updating one section does not accidentally consume unrelated subsections.

---

# 9. Undocumented Symbols

When new code symbols are added without corresponding documentation, Self-Healing Docs can identify them as potentially undocumented.

For example:

```text
Added:
UserService.get_user_preferences
```

If no suitable documentation reference is found, the action reports the symbol for review.

The system does **not** automatically invent documentation for newly added symbols.

Instead, it reports potentially undocumented symbols on the original pull request so developers can decide whether documentation should be added.

This avoids generating documentation that may not accurately describe the intended behavior of newly added code.

---

# 10. Documentation Pull Request

The action does not directly commit documentation changes to the main branch.

Instead:

```text
Code PR merged
      |
      v
Documentation analysis
      |
      v
Documentation changes
      |
      v
New documentation branch
      |
      v
Documentation Pull Request
```

The resulting pull request contains the generated documentation changes separately from the original code change.

This keeps the documentation update reviewable and gives developers the opportunity to inspect the generated changes before merging them.

---

# 11. Failure Handling

AI services can fail because of:

* Rate limits
* Quota exhaustion
* Temporary service failures
* Invalid model responses
* Other API errors

Self-Healing Docs is designed to fail safely.

If required AI analysis cannot be completed:

```text
AI analysis fails
       |
       v
No documentation update
       |
       v
Comment on original PR
```

The action does not make documentation changes based on incomplete AI analysis.

Transient failures and invalid responses are retried where appropriate. Quota or rate-limit failures are surfaced explicitly rather than repeatedly attempting an unavailable service.

---

# Architecture

The main processing pipeline can be viewed as:

```text
                    Repository
                        |
             +----------+----------+
             |                     |
             v                     v
        Source Scanner       Documentation Parser
             |                     |
             v                     v
       Code Symbols         Documentation Sections
             |                     |
             +----------+----------+
                        |
                        v
                Documentation Linker
                        |
             +----------+----------+
             |                     |
             v                     v
       Deterministic         Semantic Linking
          Linking                 |
             |                    |
             +----------+----------+
                        |
                        v
                 Change Detector
                        |
                        v
                 Impact Analyzer
                        |
                        v
                Documentation Review
                        |
                        v
                 Documentation Updater
                        |
                        v
                 GitHub PR Creation
```

The architecture separates deterministic analysis from AI-based reasoning.

This means the AI is used where semantic understanding is useful, while repository scanning, change detection, section parsing, and documentation updates remain deterministic.

---

# Supported Languages

Source code analysis currently supports:

* C++
* Go
* Java
* JavaScript
* Python
* Rust
* TypeScript
* TSX

Tree-sitter provides the parsing layer, making it possible to add additional languages by extending the scanner.

---

# Getting Started

Self-Healing Docs runs as a GitHub Action after a pull request is merged.

For installation, workflow configuration, Gemini API setup, GitHub permissions, and testing instructions, see **[QUICKSTART.md](QUICKSTART.md)**.

---

# Testing

The project includes automated tests for the main components:

* Repository scanning
* Tree-sitter language scanning
* Change detection
* Documentation parsing
* Deterministic code-documentation linking
* Candidate generation and ranking
* Semantic linking
* Impact analysis
* Documentation updates
* Nested documentation sections
* Staleness verification
* Gemini review
* AI failure handling
* End-to-end processing

Run the test suite with:

```bash
python -m pytest -q
```

The GitHub Action has also been tested through real merged pull request workflows, including:

* Removed documented symbols
* Modified documented symbols
* Newly added undocumented symbols
* Unrelated documentation remaining unchanged
* Successful Gemini analysis
* AI quota/rate-limit failure handling
* Automatic documentation pull request creation
* Fallback comments on the original pull request

---

# Project Structure

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
│   ├── change_detector.py
│   ├── combined_linker.py
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
│       ├── candidates.py
│       ├── linker.py
│       └── reviewer.py
├── tests/
├── action.yml
├── Dockerfile
├── entrypoint.sh
├── QUICKSTART.md
├── README.md
└── requirements.txt
```

---

# Version

Current release:

```text
v1.1.0
```

The action is distributed as a versioned GitHub Action and can be referenced using the `v1` release:

```yaml
uses: krishnagp97/self-healing-doc@v1
```
