#!/bin/bash

set -e

export PYTHONPATH="/app:$PYTHONPATH"

if [ -z "$GITHUB_EVENT_PATH" ]; then
    echo "Error: This action must be run inside GitHub Actions."
    exit 1
fi

git config --global --add safe.directory "$GITHUB_WORKSPACE"

echo "=========================================="
echo "       Self-Healing Docs"
echo "=========================================="
echo "Repository: $GITHUB_REPOSITORY"
echo "Event: $GITHUB_EVENT_NAME"

EVENT_FILE="$GITHUB_EVENT_PATH"

export BASE_SHA=$(python -c "import json; print(json.load(open('$EVENT_FILE'))['pull_request']['base']['sha'])")
export MERGE_SHA=$(python -c "import json; print(json.load(open('$EVENT_FILE'))['pull_request']['merge_commit_sha'])")
export PR_NUMBER=$(python -c "import json; print(json.load(open('$EVENT_FILE'))['pull_request']['number'])")
export BASE_REF=$(python -c "import json; print(json.load(open('$EVENT_FILE'))['pull_request']['base']['ref'])")

OLD_DIR="/tmp/self-healing-old"
NEW_DIR="/tmp/self-healing-new"

rm -rf "$OLD_DIR" "$NEW_DIR"

echo ""
echo "Preparing repository snapshots..."

git fetch --no-tags origin "$BASE_SHA" "$MERGE_SHA"

git worktree add --detach "$OLD_DIR" "$BASE_SHA"
git worktree add --detach "$NEW_DIR" "$MERGE_SHA"

export REVIEW_RESULTS_FILE="/tmp/self-healing-review-results.json"

echo ""
echo "Running documentation analysis..."

set +e

python -m src.main "$OLD_DIR" "$NEW_DIR"

STATUS=$?

set -e


# ============================================================
# AI SERVICE UNAVAILABLE
# ============================================================

if [ "$STATUS" -eq 2 ]; then

    echo ""
    echo "⚠️ Self-Healing Docs: AI service unavailable."

python - "$REVIEW_RESULTS_FILE" <<'PY'

import json
import os
import requests
import sys


results_file = sys.argv[1]


undocumented_symbols = []

affected_doc_ids = []


if os.path.exists(results_file):

    try:

        with open(results_file, encoding="utf-8") as f:
            data = json.load(f)


        undocumented_symbols = data.get(
            "undocumented_symbols",
            [],
        )


        affected_doc_ids = data.get(
            "affected_doc_ids",
            [],
        )


    except (json.JSONDecodeError, OSError) as error:

        print(
            f"Warning: Could not read review results: {error}"
        )


repo = os.environ["GITHUB_REPOSITORY"]

pr_number = os.environ["PR_NUMBER"]

token = os.environ["GITHUB_TOKEN"]

api_url = os.environ["GITHUB_API_URL"]


url = (
    f"{api_url}/repos/{repo}"
    f"/issues/{pr_number}/comments"
)


# ------------------------------------------------------------
# Build deterministic documentation warning
# ------------------------------------------------------------

undocumented_section = ""


if undocumented_symbols:

    undocumented_section = """
### Newly added symbols without documentation

The following newly added symbols do not appear to have corresponding documentation:

""" + "\n".join(
        f"- `{symbol['id']}`"
        for symbol in undocumented_symbols
    ) + """

Please review whether these symbols should be documented.
"""


else:

    undocumented_section = """
### Documentation coverage

No newly added undocumented symbols were detected by the deterministic documentation coverage check.
"""


affected_docs_section = ""


if affected_doc_ids:

    affected_docs_section = """
### Documentation potentially affected by code changes

The following documentation sections reference symbols affected by the merged code changes:

""" + "\n".join(
        f"- `{doc_id}`"
        for doc_id in affected_doc_ids
    ) + """

These sections could not be semantically reviewed because the AI service was unavailable.
"""


else:

    affected_docs_section = """
### Documentation impact

No documentation sections were identified as potentially affected by the changed symbols.
"""


# ------------------------------------------------------------
# Build GitHub comment
# ------------------------------------------------------------

body = """⚠️ **Self-Healing Docs:** AI documentation analysis was temporarily unavailable.

The AI service could not complete semantic documentation analysis, so no documentation changes were made.

### Analysis summary

- Newly added undocumented symbols: """ + str(len(undocumented_symbols)) + """
- Documentation sections potentially affected: """ + str(len(affected_doc_ids)) + """

""" + undocumented_section + "\n" + affected_docs_section + """

Please review the documentation above manually.

The Self-Healing Docs Action will not modify documentation when the AI service is unavailable.
"""


# ------------------------------------------------------------
# Post comment to original PR
# ------------------------------------------------------------

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json",
}


response = requests.post(
    url,
    headers=headers,
    json={"body": body},
    timeout=30,
)


response.raise_for_status()


print("✓ Comment added to original PR.")

PY

    exit 0

fi


# ============================================================
# UNEXPECTED FAILURE
# ============================================================

if [ "$STATUS" -ne 0 ]; then

    echo ""
    echo "❌ Self-Healing Docs failed unexpectedly."

    exit "$STATUS"

fi


# ============================================================
# AI REVIEW RESULTS
# ============================================================

echo ""
echo "Review results:"

cat "$REVIEW_RESULTS_FILE"


# ============================================================
# HANDLE FAILED AI REVIEWS
# ============================================================

python - "$REVIEW_RESULTS_FILE" <<'PY'

import json
import os
import requests
import sys


results_file = sys.argv[1]


with open(results_file, encoding="utf-8") as f:
    data = json.load(f)


results = data["reviews"]


undocumented_symbols = data.get(
    "undocumented_symbols",
    [],
)


affected_doc_ids = data.get(
    "affected_doc_ids",
    [],
)


failed = any(
    not item["success"]
    for item in results
)


if not failed:

    print("AI review completed successfully.")

    sys.exit(0)


print("AI review failed.")


# ------------------------------------------------------------
# Collect documentation requiring manual review
# ------------------------------------------------------------

documentation = []

changed_symbols = []


for item in results:

    if not item["success"]:

        documentation.append(
            f"- `{item['file']}` → `{item['heading']}`"
        )


        for change in item["changed_symbols"]:

            symbol = change["symbol"]


            changed_symbols.append(
                f"- `{symbol['file']}::{symbol['name']}`"
            )


# ------------------------------------------------------------
# Build undocumented symbols section
# ------------------------------------------------------------

undocumented_section = ""


if undocumented_symbols:

    undocumented_section = """
### Potentially undocumented symbols

The following newly added symbols do not appear to have corresponding documentation:

""" + "\n".join(
        f"- `{symbol['id']}`"
        for symbol in undocumented_symbols
    ) + """

Please review whether these symbols should be documented.
"""


else:

    undocumented_section = """
### Documentation coverage

No newly added undocumented symbols were detected by the deterministic documentation coverage check.
"""


# ------------------------------------------------------------
# Build potentially affected documentation section
# ------------------------------------------------------------

affected_docs_section = ""


if affected_doc_ids:

    affected_docs_section = """
### Documentation potentially affected by code changes

The following documentation sections reference symbols affected by the merged code changes:

""" + "\n".join(
        f"- `{doc_id}`"
        for doc_id in affected_doc_ids
    ) + """

These sections could not be fully reviewed because the AI service was unavailable.
"""


else:

    affected_docs_section = """
### Documentation impact

No documentation sections were identified as potentially affected by the changed symbols.
"""


# ------------------------------------------------------------
# Build GitHub comment
# ------------------------------------------------------------

body = """⚠️ **Self-Healing Docs:** AI documentation review was temporarily unavailable.

The AI service could not complete the documentation review, so no documentation changes were made.

### Documentation requiring manual review

""" + "\n".join(documentation) + """

### Related code changes

""" + "\n".join(changed_symbols) + "\n" + undocumented_section + "\n" + affected_docs_section + """

Please review the documentation above manually. The documentation may be outdated because the related code was modified.

The Self-Healing Docs Action will not modify documentation when the AI review is unavailable.
"""


# ------------------------------------------------------------
# GitHub API configuration
# ------------------------------------------------------------

repo = os.environ["GITHUB_REPOSITORY"]

pr_number = os.environ["PR_NUMBER"]

token = os.environ["GITHUB_TOKEN"]

api_url = os.environ["GITHUB_API_URL"]


url = (
    f"{api_url}/repos/{repo}"
    f"/issues/{pr_number}/comments"
)


headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json",
}


# ------------------------------------------------------------
# Post comment to original PR
# ------------------------------------------------------------

response = requests.post(
    url,
    headers=headers,
    json={"body": body},
    timeout=30,
)


response.raise_for_status()


print("✓ Comment added to original PR.")

sys.exit(0)

PY


# ============================================================
# REPORT UNDOCUMENTED SYMBOLS
# ============================================================

python - "$REVIEW_RESULTS_FILE" <<'PY'

import json
import os
import requests
import sys


results_file = sys.argv[1]


with open(results_file, encoding="utf-8") as f:
    data = json.load(f)


undocumented_symbols = data["undocumented_symbols"]


if not undocumented_symbols:

    sys.exit(0)


print("")

print("⚠️ Potentially undocumented symbols detected:")


for symbol in undocumented_symbols:

    print(
        f"   - {symbol['id']}"
    )


repo = os.environ["GITHUB_REPOSITORY"]

pr_number = os.environ["PR_NUMBER"]

token = os.environ["GITHUB_TOKEN"]

api_url = os.environ["GITHUB_API_URL"]


url = (
    f"{api_url}/repos/{repo}"
    f"/issues/{pr_number}/comments"
)


body = """⚠️ **Self-Healing Docs:** Potentially undocumented symbols detected.

The following newly added symbols do not appear to have corresponding documentation references:

""" + "\n".join(
    f"- `{symbol['id']}`"
    for symbol in undocumented_symbols
) + """

Please review whether these symbols should be documented.

No automatic documentation sections were created for these symbols.
"""


headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json",
}


response = requests.post(
    url,
    headers=headers,
    json={"body": body},
    timeout=30,
)


response.raise_for_status()


print("✓ Comment added to original PR.")

PY


# ============================================================
# CHECK WHETHER DOCUMENTATION WAS UPDATED
# ============================================================

UPDATED=$(python - "$REVIEW_RESULTS_FILE" <<'PY'

import json
import sys


with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)


reviews = data["reviews"]


updated = any(
    item.get("success")
    and item.get("updated")
    for item in reviews
)


print("true" if updated else "false")

PY
)


if [ "$UPDATED" != "true" ]; then

    echo ""
    echo "No documentation updates. Skipping branch creation."

    exit 0

fi


# ============================================================
# CREATE DOCUMENTATION PR
# ============================================================

BRANCH_NAME="docs/self-healing-$(date +%s)"

echo ""
echo "Creating documentation branch: $BRANCH_NAME"


git checkout -b "$BRANCH_NAME"


git config user.name "github-actions[bot]"

git config user.email "41898282+github-actions[bot]@users.noreply.github.com"


python - "$REVIEW_RESULTS_FILE" <<'PY'

import json
import sys

from pathlib import Path


results_file = sys.argv[1]


with open(results_file, encoding="utf-8") as f:
    data = json.load(f)


def get_heading_level(line):
    """Return Markdown heading level, or 0 if the line is not a heading."""

    stripped = line.lstrip()

    if not stripped.startswith("#"):
        return 0

    level = len(stripped) - len(stripped.lstrip("#"))

    if level > 6:
        return 0

    if len(stripped) <= level:
        return 0

    if not stripped[level].isspace():
        return 0

    return level


def normalize_heading(text):
    """Normalize heading whitespace for reliable comparison."""

    return " ".join(text.strip().split())


for review in data["reviews"]:

    if not review["success"]:
        continue


    file_path = Path(review["file"])

    heading = review["heading"]

    heading_level = review["heading_level",1]

    content = review["suggested_update"]


    full_path = Path.cwd() / file_path


    if not full_path.exists():

        print(
            f"Warning: Documentation file not found: {file_path}"
        )

        continue


    text = full_path.read_text(
        encoding="utf-8"
    )


    lines = text.splitlines()


    normalized_heading = normalize_heading(
        heading
    )


    try:

        index = next(
            i
            for i, line in enumerate(lines)
            if (
                get_heading_level(line) == heading_level
                and normalize_heading(
                    line.lstrip().lstrip("#").strip()
                ) == normalized_heading
            )
        )


    except StopIteration:

        print(
            f"Warning: Heading not found: "
            f"{'#' * heading_level} {heading}"
        )

        continue


    end = len(lines)


    for i in range(index + 1, len(lines)):

        current_level = get_heading_level(
            lines[i]
        )


        if (
            current_level
            and current_level <= heading_level
        ):

            end = i

            break


    markdown_heading = (
        "#" * heading_level
        + " "
        + heading.strip()
    )


    new_section = [
        markdown_heading,
        "",
        content.strip(),
        "",
    ]


    lines[index:end] = new_section


    full_path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

PY

git add .


if git diff --cached --quiet; then

    echo ""
    echo "No documentation changes detected after update."

    exit 0

fi


git commit -m "docs: update documentation automatically"


git push origin "$BRANCH_NAME"


echo ""
echo "✓ Documentation branch pushed."

echo "Branch: $BRANCH_NAME"


# ============================================================
# CREATE PR USING GITHUB API
# ============================================================

python - <<'PY'

import os
import requests


repo = os.environ["GITHUB_REPOSITORY"]

token = os.environ["GITHUB_TOKEN"]

api_url = os.environ["GITHUB_API_URL"]


branch = os.environ.get(
    "BRANCH_NAME",
    "",
)


if not branch:

    branch = os.popen(
        "git branch --show-current"
    ).read().strip()


url = (
    f"{api_url}/repos/{repo}/pulls"
)


headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json",
}


body = {
    "title": "docs: update documentation automatically",

    "head": branch,

    "base": os.environ["BASE_REF"],

    "body": """## Self-Healing Docs

This pull request was automatically generated because documentation was detected as potentially outdated after a code change.

Please review the generated documentation before merging.
""",
}


response = requests.post(
    url,
    headers=headers,
    json=body,
    timeout=30,
)


response.raise_for_status()


pull_request = response.json()


print(
    f"✓ Documentation PR created: "
    f"{pull_request['html_url']}"
)

PY