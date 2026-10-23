"""
Upload Metadata & Scheduling Agent Graph (LangGraph).

Pipeline:
  analyze_content -> generate_metadata -> thumbnail_prompt -> schedule_plan
"""
from typing import Any, Dict, List, TypedDict

from app.ai.graphs.base_graph import END, create_state_graph, parse_json_from_llm
from app.ai.providers.ai_dispatcher import generate_ai_text as generate_text


class UploadState(TypedDict, total=False):
    context: str
    upload_name: str
    metadata: Dict[str, Any]
    thumbnail_spec: Dict[str, Any]
    schedule: Dict[str, Any]
    final_result: Dict[str, Any]


def analyze_content_node(state: UploadState) -> Dict[str, Any]:
    context = state.get("context", "")
    upload_name = state.get("upload_name", "upload")
    return {"clean_topic": context or upload_name}


def generate_metadata_node(state: UploadState) -> Dict[str, Any]:
    topic = state.get("clean_topic", "Creator Video")
    system = "You are a professional YouTube channel publishing manager."
    prompt = (
        f"Generate complete YouTube upload metadata for '{topic}'.\n"
        f"Return JSON with: title, description, tags (array), category, language."
    )
    resp = generate_text(prompt, system=system, json_mode=True)
    parsed = parse_json_from_llm(resp)
    meta = {
        "title": parsed.get("title", f"{topic.title()} — The Complete Creator Guide"),
        "description": parsed.get("description", f"Watch this complete guide on {topic} to elevate your channel.\n\nSubscribe for daily creator tips!"),
        "tags": parsed.get("tags", [topic.lower(), "shorts", "creator tips", "youtube"]),
        "category": parsed.get("category", "Science & Technology"),
        "language": "en",
    }
    return {"metadata": meta}


def thumbnail_prompt_node(state: UploadState) -> Dict[str, Any]:
    topic = state.get("clean_topic", "Creator Video")
    system = "You design high-CTR thumbnail concepts for YouTube creators."
    prompt = f"Design an ultra high-CTR thumbnail prompt for Stable Diffusion XL for topic: '{topic}'. Return JSON with: visual_prompt, text_overlay, color_theme."
    resp = generate_text(prompt, system=system, json_mode=True)
    parsed = parse_json_from_llm(resp)
    spec = {
        "visual_prompt": parsed.get("visual_prompt", f"Cinematic close-up portrait with glowing neon rim light, expressing shock at {topic}"),
        "text_overlay": parsed.get("text_overlay", "DON'T MISS THIS!"),
        "color_theme": "High-contrast Yellow & Deep Navy",
    }
    return {"thumbnail_spec": spec}


def schedule_plan_node(state: UploadState) -> Dict[str, Any]:
    meta = state.get("metadata", {})
    spec = state.get("thumbnail_spec", {})

    result = {
        "raw": f"Metadata generated for {meta.get('title')}",
        "parsed": {
            **meta,
            "thumbnail_concept": spec,
            "scheduled_time": "Tomorrow at 3:00 PM EST",
            "visibility": "public",
            "made_for_kids": False,
        },
    }
    return {"final_result": result}


def build_upload_graph():
    workflow = create_state_graph(UploadState)
    workflow.add_node("analyze_content", analyze_content_node)
    workflow.add_node("generate_metadata", generate_metadata_node)
    workflow.add_node("thumbnail_prompt", thumbnail_prompt_node)
    workflow.add_node("schedule_plan", schedule_plan_node)

    workflow.set_entry_point("analyze_content")
    workflow.add_edge("analyze_content", "generate_metadata")
    workflow.add_edge("generate_metadata", "thumbnail_prompt")
    workflow.add_edge("thumbnail_prompt", "schedule_plan")
    workflow.add_edge("schedule_plan", END)

    return workflow.compile()


upload_graph = build_upload_graph()


def run_upload_agent(context: str, upload_name: str = "new-upload", **kwargs) -> Dict[str, Any]:
    """Execute the Upload Metadata LangGraph."""
    state = upload_graph.invoke({"context": context, "upload_name": upload_name})
    return state.get("final_result", {})
