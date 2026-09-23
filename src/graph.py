
import json
from pathlib import Path


def build_graph(chunks, sections, link_result):
    """Combine code symbols, documentation sections, and links."""
    return {
        "symbols": chunks,
        "sections": sections,
        "links": link_result["links"],
        "unmatched": link_result["unmatched"],
        "ambiguous": link_result["ambiguous"],
    }


def save_graph(graph, output_path):
    """Write the graph to a JSON file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(graph, indent=2),
        encoding="utf-8",
    )