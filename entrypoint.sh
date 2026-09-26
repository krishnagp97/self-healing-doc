#!/bin/bash

set -e

[ -n "$GITHUB_EVENT_PATH" ] || {
    echo "Error: This action must be run inside GitHub Actions."
    exit 1
}

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

echo ""
echo "Pull Request: #$PR_NUMBER"
echo "Base SHA:     $BASE_SHA"
echo "Merge SHA:    $MERGE_SHA"
echo "Base branch:  $BASE_REF"

OLD_DIR="/tmp/self-healing-old"
NEW_DIR="/tmp/self-healing-new"

rm -rf "$OLD_DIR" "$NEW_DIR"

echo ""
echo "Creating repository snapshots..."

git fetch --no-tags origin "$BASE_SHA" "$MERGE_SHA"

git worktree add --detach "$OLD_DIR" "$BASE_SHA"
git worktree add --detach "$NEW_DIR" "$MERGE_SHA"

echo "✓ Snapshots created"

echo ""
echo "Running documentation analysis..."

export REVIEW_RESULTS_FILE="/tmp/self-healing-review-results.json"

python -m src.main "$OLD_DIR" "$NEW_DIR"

echo ""
echo "Review results:"
cat "$REVIEW_RESULTS_FILE"

echo ""

python - "$REVIEW_RESULTS_FILE" <<'PY'
import json
import os
import requests
import sys

results_file = sys.argv[1]

with open(results_file, encoding="utf-8") as f:
    results = json.load(f)

failed = any(not item["success"] for item in results)

if failed:
    print("AI review failed.")

    repo = os.environ["GITHUB_REPOSITORY"]
    pr_number = os.environ["PR_NUMBER"]
    token = os.environ["GITHUB_TOKEN"]
    api_url = os.environ["GITHUB_API_URL"]

    url = f"{api_url}/repos/{repo}/issues/{pr_number}/comments"

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

    body = """⚠️ **Self-Healing Docs:** AI documentation review was temporarily unavailable.

The AI service could not complete the documentation review, so no documentation changes were made.

### Documentation requiring manual review

""" + "\n".join(documentation) + """

### Related code changes

""" + "\n".join(changed_symbols) + """

Please review the documentation above manually. The documentation may be outdated because the related code was modified.

The Self-Healing Docs Action will not modify documentation when the AI review is unavailable."""

    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={"body": body},
        timeout=30,
    )

    response.raise_for_status()

    print("✓ Comment added to original PR.")

    sys.exit(0)

print("AI review completed successfully.")
PY

UPDATED=$(python - "$REVIEW_RESULTS_FILE" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    results = json.load(f)

print("true" if any(item["updated"] for item in results) else "false")
PY
)

[ "$UPDATED" != "true" ] || {
    echo "No documentation updates. Skipping branch creation."
    exit 0
}

export DOCS_BRANCH="docs/self-healing-${PR_NUMBER}"

echo ""
echo "Creating documentation branch: $DOCS_BRANCH"

cd "$NEW_DIR"

git checkout -b "$DOCS_BRANCH"

echo "✓ Documentation branch created"

echo ""
echo "Committing documentation updates..."

git add .

git commit -m "docs: update documentation automatically"

echo "✓ Documentation changes committed"

echo ""
echo "Pushing documentation branch..."

git push -u origin "$DOCS_BRANCH"

echo "✓ Documentation branch pushed"

echo ""
echo "Creating documentation PR..."

UPDATED_SECTIONS=$(python - "$REVIEW_RESULTS_FILE" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    results = json.load(f)

for item in results:
    if item["updated"]:
        print(f"- `{item['file']}` → `{item['heading']}`")
PY
)

CHANGED_SYMBOLS=$(python - "$REVIEW_RESULTS_FILE" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    results = json.load(f)

seen = set()

for item in results:
    if item["updated"]:
        for change in item["changed_symbols"]:
            symbol = change["symbol"]
            value = f"- `{symbol['file']}::{symbol['name']}`"

            if value not in seen:
                print(value)
                seen.add(value)
PY
)

python - "$UPDATED_SECTIONS" "$CHANGED_SYMBOLS" <<'PY'
import json
import os
import requests
import sys

updated_sections = sys.argv[1]
changed_symbols = sys.argv[2]

repo = os.environ["GITHUB_REPOSITORY"]
token = os.environ["GITHUB_TOKEN"]
api_url = os.environ["GITHUB_API_URL"]

url = f"{api_url}/repos/{repo}/pulls"

body = f"""## Self-Healing Docs

Updated documentation based on changes from PR #{os.environ["PR_NUMBER"]}.

### Updated sections

{updated_sections}

### Changed symbols

{changed_symbols}

This PR was generated automatically by Self-Healing Docs.
"""

response = requests.post(
    url,
    headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    },
    json={
        "title": f"docs: update documentation for #{os.environ['PR_NUMBER']}",
        "body": body,
        "head": os.environ["DOCS_BRANCH"],
        "base": os.environ["BASE_REF"],
    },
    timeout=30,
)

response.raise_for_status()

pr = response.json()

print(f"✓ Documentation PR created: {pr['html_url']}")
PY

echo ""
echo "Self-Healing Docs analysis completed."