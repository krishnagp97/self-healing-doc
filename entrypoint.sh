#!/bin/bash
set -e

if [ -z "$GITHUB_EVENT_PATH" ]; then
    echo "Error: This action must be run inside GitHub Actions."
    exit 1
fi

echo "=========================================="
echo "       Self-Healing Docs"
echo "=========================================="

echo "Repository: $GITHUB_REPOSITORY"
echo "Event: $GITHUB_EVENT_NAME"

EVENT_FILE="$GITHUB_EVENT_PATH"

BASE_SHA=$(python -c "import json; print(json.load(open('$EVENT_FILE'))['pull_request']['base']['sha'])")
MERGE_SHA=$(python -c "import json; print(json.load(open('$EVENT_FILE'))['pull_request']['merge_commit_sha'])")
PR_NUMBER=$(python -c "import json; print(json.load(open('$EVENT_FILE'))['pull_request']['number'])")
BASE_REF=$(python -c "import json; print(json.load(open('$EVENT_FILE'))['pull_request']['base']['ref'])")

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

git worktree add --detach "$OLD_DIR" "$BASE_SHA"
git worktree add --detach "$NEW_DIR" "$MERGE_SHA"

echo "✓ Snapshots created"

echo ""
echo "Running documentation analysis..."

python -m src.main "$OLD_DIR" "$NEW_DIR"

echo ""
echo "Self-Healing Docs analysis completed."