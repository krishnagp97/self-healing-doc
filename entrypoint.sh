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

if not failed:
    print("AI review completed successfully.")
    sys.exit(0)

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
PY

echo ""
echo "Self-Healing Docs analysis completed."