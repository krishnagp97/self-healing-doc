from src.llm.reviewer import review_documentation
import argparse
from pathlib import Path

from src.tree_sitter_scanner import scan_repository
from src.doc_parser import parse_markdown
from src.linker import link_sections
from src.change_detector import detect_changes
from src.impact_analyzer import find_affected_docs
from src.staleness_verifier import prepare_review_items
from src.doc_updater import update_section
import json
import os




def scan_docs(root):
    """Scan all Markdown files in a repository."""
    sections = []
    ignored = {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "dist",
        "build",
        "tests",
        "temp-old",
        "temp-new",
    }
    for file_path in root.rglob("*.md"):
        relative_path = file_path.relative_to(root)

        if any(part in ignored for part in relative_path.parts):
            continue

        sections.extend(parse_markdown(file_path, root))

    return sections


def run(old_path, new_path):
    old_root = Path(old_path).resolve()
    new_root = Path(new_path).resolve()

    results = []

    print("\nSelf-Healing Docs")
    print("=" * 50)

    print("\nScanning repositories...")

    old_chunks = scan_repository(old_root)
    new_chunks = scan_repository(new_root)

    old_sections = scan_docs(old_root)
    new_sections = scan_docs(new_root)

    print(f"  Old code chunks : {len(old_chunks)}")
    print(f"  New code chunks : {len(new_chunks)}")
    print(f"  Old doc sections: {len(old_sections)}")
    print(f"  New doc sections: {len(new_sections)}")

    print("\nLinking documentation...")

    old_link_result = link_sections(old_sections, old_chunks)
    new_link_result = link_sections(new_sections, new_chunks)

    old_links = old_link_result["links"]
    new_links = new_link_result["links"]

    print(f"  Old links: {len(old_links)}")
    print(f"  New links: {len(new_links)}")

    print("\nDetecting changes...")

    changes = detect_changes(old_chunks, new_chunks)

    print(f"  Added   : {len(changes['added'])}")
    print(f"  Removed : {len(changes['removed'])}")
    print(f"  Modified: {len(changes['modified'])}")

    print("\nAnalyzing documentation impact...")

    affected_doc_ids = find_affected_docs(
        changes,
        old_links,
        new_links,
    )

    print(f"  Affected documentation sections: {len(affected_doc_ids)}")

    print("\nPreparing review items...")

    review_items = prepare_review_items(
        new_sections,
        changes,
        affected_doc_ids,
        old_links,
        new_links,
    )

    if not review_items:
        print("\n✓ No documentation requires review.")
        return []

    print("\nDocumentation requiring review")
    print("-" * 50)

    for index, item in enumerate(review_items, start=1):
        print(f"\n{index}. {item['heading']}")
        print(f"   File/Section: {item['doc_id']}")
        print(f"   Status      : {item['status']}")

        print("   Changed symbols:")

        for change in item["changed_symbols"]:
            symbol = change["symbol"]

            print(
                f"      - {change['change_type']}: "
                f"{symbol['id']}"
            )

            if change["change_type"] == "modified":
                print(
                    f"        Previous signature: "
                    f"{change['previous_signature']}"
                )
                print(
                    f"        Current signature : "
                    f"{symbol['signature']}"
                )

        print("\n   AI Review:")

        ai_review = review_documentation(item)

        updated = False

        print("   Issue:")
        print(f"      {ai_review['issue']}")

        suggested_update = ai_review["suggested_update"]

        if suggested_update:
            file_path = new_root / item["file"]

            updated = update_section(
                file_path=file_path,
                section_title=item["heading"],
                new_content=suggested_update,
                heading_level=item["heading_level"],
            )

            if updated:
                print("\n   ✓ Documentation updated.")
            else:
                print("\n   ✗ Documentation section not found.")
        else:
            print("\n   No documentation update suggested.")
        results.append({
            "file": item["file"],
            "heading": item["heading"],
            "success": ai_review["success"],
            "suggested_update": suggested_update,
            "updated": updated,
        })
    print("\n" + "=" * 50)
    print(f"Total review items: {len(review_items)}")
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Detect code changes and identify stale documentation."
    )

    parser.add_argument(
        "old",
        help="Path to the old project snapshot",
    )

    parser.add_argument(
        "new",
        help="Path to the new project snapshot",
    )

    args = parser.parse_args()

    results = run(args.old, args.new)
    output_file = os.getenv(
        "REVIEW_RESULTS_FILE",
        "review_results.json",
    )
    with open(output_file, "w", encoding="utf-8") as file:
      json.dump(results, file, indent=2)


if __name__ == "__main__":
    main()