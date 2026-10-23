"""
Base graph definitions and runner for YouTube Buddy LangGraph agents.

Supports native LangGraph `StateGraph` when installed, with a self-contained
DAG execution engine fallback so the system remains resilient across environments.
"""
import json
import logging
from typing import Any, Callable, Dict, List, Optional, TypedDict

logger = logging.getLogger(__name__)

# Try to import native LangGraph
try:
    from langgraph.graph import StateGraph as NativeStateGraph, END as NATIVE_END, START as NATIVE_START
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False
    NativeStateGraph = None
    NATIVE_END = "__END__"
    NATIVE_START = "__START__"

END = NATIVE_END
START = NATIVE_START


class FallbackCompiledGraph:
    """Lightweight deterministic DAG executor for graph workflows."""

    def __init__(self, nodes: Dict[str, Callable], edges: List[tuple[str, str]], entry_point: str):
        self.nodes = nodes
        self.edges = edges
        self.entry_point = entry_point

    def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        current_node = self.entry_point
        current_state = dict(state)
        visited = 0
        max_steps = 50

        # Build adjacency mapping
        adj: Dict[str, str] = {}
        for src, dst in self.edges:
            adj[src] = dst

        while current_node and current_node not in (END, "__END__") and visited < max_steps:
            if current_node in self.nodes:
                fn = self.nodes[current_node]
                logger.info("Executing graph node: %s", current_node)
                updates = fn(current_state)
                if isinstance(updates, dict):
                    current_state.update(updates)
            current_node = adj.get(current_node, END)
            visited += 1

        return current_state


class CompatStateGraph:
    """StateGraph compatibility wrapper."""

    def __init__(self, state_schema: Any):
        self.state_schema = state_schema
        self.nodes: Dict[str, Callable] = {}
        self.edges: List[tuple[str, str]] = []
        self.entry_point: str | None = None
        if HAS_LANGGRAPH and NativeStateGraph:
            self._native = NativeStateGraph(state_schema)
        else:
            self._native = None

    def add_node(self, node: str, action: Callable):
        self.nodes[node] = action
        if self._native:
            self._native.add_node(node, action)
        return self

    def add_edge(self, start_key: str, end_key: str):
        self.edges.append((start_key, end_key))
        if self._native:
            self._native.add_edge(start_key, end_key)
        return self

    def set_entry_point(self, key: str):
        self.entry_point = key
        if self._native:
            self._native.set_entry_point(key)
        return self

    def compile(self):
        if self._native:
            return self._native.compile()
        return FallbackCompiledGraph(self.nodes, self.edges, self.entry_point or "start")


def create_state_graph(schema: Any) -> CompatStateGraph:
    """Factory to create a compatible StateGraph instance."""
    return CompatStateGraph(schema)


def parse_json_from_llm(text: str) -> Dict[str, Any]:
    """Clean and parse JSON from local LLM markdown output."""
    if not text:
        return {}
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {"raw_content": text}
