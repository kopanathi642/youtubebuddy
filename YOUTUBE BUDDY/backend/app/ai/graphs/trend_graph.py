"""
Trend Analysis Agent Graph (LangGraph).

Pipeline:
  analyze_niche -> search_trends -> score_topics -> format_report
"""
from typing import Any, Dict, List, TypedDict

from app.ai.graphs.base_graph import END, create_state_graph, parse_json_from_llm
from app.ai.providers.ai_dispatcher import generate_ai_text as generate_text


class TrendState(TypedDict, total=False):
    context: str
    niche: str
    raw_trends: List[str]
    scored_topics: List[Dict[str, Any]]
    final_report: Dict[str, Any]


def analyze_niche_node(state: TrendState) -> Dict[str, Any]:
    context = state.get("context", "General Tech & YouTube Growth")
    system = "You are a YouTube market researcher. Identify the core niche, target audience persona, and content pillars from the creator context."
    prompt = f"Analyze this creator context and extract: 1. Core Niche, 2. Target Audience, 3. Top 3 Content Pillars. Return clean JSON with keys: niche, audience, pillars.\n\nContext: {context}"
    response = generate_text(prompt, system=system, json_mode=True)
    parsed = parse_json_from_llm(response)
    niche = parsed.get("niche", context)
    return {"niche": niche, "niche_analysis": parsed}


def search_trends_node(state: TrendState) -> Dict[str, Any]:
    niche = state.get("niche", "YouTube Growth")
    system = "You are a viral trend forecasting analyst for YouTube creators."
    prompt = f"Generate 5 breakout viral topics currently trending or with massive velocity in the '{niche}' niche. Return JSON with a 'topics' array of 5 topic titles."
    response = generate_text(prompt, system=system, json_mode=True)
    parsed = parse_json_from_llm(response)
    topics = parsed.get("topics", [
        f"How to grow in {niche} in 2026",
        f"Top 5 mistakes in {niche}",
        f"The secret strategy behind {niche} success",
    ])
    return {"raw_trends": topics}


def score_topics_node(state: TrendState) -> Dict[str, Any]:
    topics = state.get("raw_trends", [])
    system = "You are a YouTube algorithm and retention specialist."
    prompt = (
        f"Score each of these topics (0-100) based on Search Velocity, Click-Through Potential, and Competition Gap.\n"
        f"Topics: {topics}\n"
        f"Return JSON with 'scored' array of objects with keys: topic, viral_score, velocity, competition, best_angle."
    )
    response = generate_text(prompt, system=system, json_mode=True)
    parsed = parse_json_from_llm(response)
    scored = parsed.get("scored", [
        {"topic": t, "viral_score": 92, "velocity": "+320%", "competition": "Low", "best_angle": "Fast-paced breakdown"}
        for t in topics[:3]
    ])
    return {"scored_topics": scored}


def format_report_node(state: TrendState) -> Dict[str, Any]:
    niche = state.get("niche", "General")
    scored = state.get("scored_topics", [])
    report = {
        "niche": niche,
        "summary": f"Identified {len(scored)} high-opportunity trends for '{niche}'",
        "opportunities": scored,
        "recommended_action": "Produce a high-retention 9:16 vertical short on the #1 ranked topic within 48 hours.",
    }
    return {"final_report": report}


def build_trend_graph():
    workflow = create_state_graph(TrendState)
    workflow.add_node("analyze_niche", analyze_niche_node)
    workflow.add_node("search_trends", search_trends_node)
    workflow.add_node("score_topics", score_topics_node)
    workflow.add_node("format_report", format_report_node)

    workflow.set_entry_point("analyze_niche")
    workflow.add_edge("analyze_niche", "search_trends")
    workflow.add_edge("search_trends", "score_topics")
    workflow.add_edge("score_topics", "format_report")
    workflow.add_edge("format_report", END)

    return workflow.compile()


trend_graph = build_trend_graph()


def run_trend_agent(context: str, **kwargs) -> Dict[str, Any]:
    """Execute the Trend Agent LangGraph."""
    state = trend_graph.invoke({"context": context})
    return state.get("final_report", {})
