
import json
from pathlib import Path

from src.scanner import scan_repository
from src.doc_parser import parse_markdown
from src.linker import link_sections
from src.graph import build_graph, save_graph


def test_build_and_save_graph(tmp_path):
    root = Path(__file__).resolve().parents[1] / "fixtures"

    chunks = scan_repository(root)
    sections = parse_markdown(root / "sample.md", root)
    link_result = link_sections(sections, chunks)

    graph = build_graph(chunks, sections, link_result)

    output_path = tmp_path / "output" / "graph.json"
    save_graph(graph, output_path)

    assert output_path.exists()

    saved_graph = json.loads(output_path.read_text(encoding="utf-8"))
    assert len(saved_graph["symbols"]) == len(chunks)
    assert len(saved_graph["sections"]) == len(sections)
    assert saved_graph["links"] == link_result["links"]