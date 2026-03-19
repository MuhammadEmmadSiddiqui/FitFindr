"""
Generate a PNG of the LangGraph screening pipeline and save it to graph.png.

Usage (from project root):
    .venv\Scripts\python.exe save_graph.py
"""
import sys
from pathlib import Path

# make backend/src importable
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from src.config import settings  # noqa: E402 – loads .env

# Build the graph without fully initialising the heavy service
from langgraph.graph import END, StateGraph
from src.services.graph_service import (
    ScreeningState,
    DEEP_THRESHOLD,
    SKIP_THRESHOLD,
)

# ── Lightweight stubs (no Groq clients, no embedding model needed) ─────────

def embed_and_score(state): ...
def parse_resume(state): ...
def retry_parse(state): ...
def deep_analysis(state): ...
def build_result(state): ...

def route_after_embed(state):
    return "build_result" if state.get("analysis_depth") == "skip" else "parse_resume"

def route_after_parse(state):
    return "deep_analysis" if state.get("analysis_depth") == "deep" else "build_result"

def route_after_retry(state):
    return "deep_analysis" if state.get("analysis_depth") == "deep" else "build_result"

g = StateGraph(ScreeningState)
g.add_node("embed_and_score", embed_and_score)
g.add_node("parse_resume",    parse_resume)
g.add_node("retry_parse",     retry_parse)
g.add_node("deep_analysis",   deep_analysis)
g.add_node("build_result",    build_result)

g.set_entry_point("embed_and_score")

g.add_conditional_edges(
    "embed_and_score",
    route_after_embed,
    {"parse_resume": "parse_resume", "build_result": "build_result"},
)
g.add_conditional_edges(
    "parse_resume",
    route_after_parse,
    {
        "retry_parse":   "retry_parse",
        "deep_analysis": "deep_analysis",
        "build_result":  "build_result",
    },
)
g.add_conditional_edges(
    "retry_parse",
    route_after_retry,
    {"deep_analysis": "deep_analysis", "build_result": "build_result"},
)
g.add_edge("deep_analysis", "build_result")
g.add_edge("build_result",  END)

compiled = g.compile()

# ── Save as PNG ────────────────────────────────────────────────────────────

output = Path(__file__).parent / "graph.png"
png_bytes = compiled.get_graph().draw_mermaid_png()
output.write_bytes(png_bytes)
print(f"Graph saved → {output}")
