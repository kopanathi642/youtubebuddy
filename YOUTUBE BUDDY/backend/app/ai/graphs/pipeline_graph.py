"""
Multi-Agent Creator Pipeline Graph (LangGraph).

Chains all agents end-to-end:
  Trend Analysis -> Script Writing -> SEO Optimization -> Upload Metadata & Thumbnail Prompt
"""
from typing import Any, Dict, TypedDict

from app.ai.graphs.base_graph import END, create_state_graph
from app.ai.graphs.script_graph import run_script_agent
from app.ai.graphs.seo_graph import run_seo_agent
from app.ai.graphs.trend_graph import run_trend_agent
from app.ai.graphs.upload_graph import run_upload_agent


class PipelineState(TypedDict, total=False):
    initial_topic: str
    trend_result: Dict[str, Any]
    selected_topic: str
    script_result: Dict[str, Any]
    seo_result: Dict[str, Any]
    upload_result: Dict[str, Any]
    pipeline_summary: Dict[str, Any]


def trend_step_node(state: PipelineState) -> Dict[str, Any]:
    topic = state.get("initial_topic", "Creator Tips")
    trend_data = run_trend_agent(topic)
    opportunities = trend_data.get("opportunities", [])
    if opportunities and isinstance(opportunities, list) and len(opportunities) > 0:
        top_topic = opportunities[0].get("topic", topic)
    else:
        top_topic = topic
    return {"trend_result": trend_data, "selected_topic": top_topic}


def script_step_node(state: PipelineState) -> Dict[str, Any]:
    selected_topic = state.get("selected_topic", "Viral Video")
    script_data = run_script_agent(selected_topic)
    return {"script_result": script_data}


def seo_step_node(state: PipelineState) -> Dict[str, Any]:
    selected_topic = state.get("selected_topic", "Viral Video")
    seo_data = run_seo_agent(selected_topic)
    return {"seo_result": seo_data}


def upload_step_node(state: PipelineState) -> Dict[str, Any]:
    selected_topic = state.get("selected_topic", "Viral Video")
    upload_data = run_upload_agent(selected_topic)
    return {"upload_result": upload_data}


def assemble_pipeline_node(state: PipelineState) -> Dict[str, Any]:
    return {
        "pipeline_summary": {
            "status": "completed",
            "topic": state.get("selected_topic"),
            "trend": state.get("trend_result"),
            "script": state.get("script_result"),
            "seo": state.get("seo_result"),
            "upload": state.get("upload_result"),
        }
    }


def build_pipeline_graph():
    workflow = create_state_graph(PipelineState)
    workflow.add_node("trend_step", trend_step_node)
    workflow.add_node("script_step", script_step_node)
    workflow.add_node("seo_step", seo_step_node)
    workflow.add_node("upload_step", upload_step_node)
    workflow.add_node("assemble_pipeline", assemble_pipeline_node)

    workflow.set_entry_point("trend_step")
    workflow.add_edge("trend_step", "script_step")
    workflow.add_edge("script_step", "seo_step")
    workflow.add_edge("seo_step", "upload_step")
    workflow.add_edge("upload_step", "assemble_pipeline")
    workflow.add_edge("assemble_pipeline", END)

    return workflow.compile()


pipeline_graph = build_pipeline_graph()


def run_full_pipeline(initial_topic: str) -> Dict[str, Any]:
    """Run the complete multi-agent pipeline."""
    state = pipeline_graph.invoke({"initial_topic": initial_topic})
    return state.get("pipeline_summary", {})
