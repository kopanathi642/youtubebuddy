"""
Studio Tool Router Graph (LangGraph).

Routes studio requests through proper prompt expansion, quality enforcement,
and dispatches to either Stable Diffusion XL (image tools) or Ollama (text/script tools).
"""
import logging
from typing import Any, Dict, TypedDict

from app.ai.graphs.base_graph import END, create_state_graph, parse_json_from_llm
from app.ai.prompt_templates import (
    build_image_prompt,
    build_text_prompt,
    get_negative_prompt,
    get_system_prompt,
)
from app.ai.providers.diffusion_provider import generate_image
from app.ai.providers.ai_dispatcher import generate_ai_text as generate_text

logger = logging.getLogger(__name__)

IMAGE_TOOLS = {
    "create",
    "cineshot",
    "moodboard",
    "character",
    "persona",
    "aesthetic",
    "relight",
    "inpaint",
    "faceswap",
    "charswap",
    "fashion",
    "upscale",
    "draw",
}


class StudioState(TypedDict, total=False):
    tool_id: str
    user_prompt: str
    style: str
    aspect_ratio: str
    duration: int
    camera_movement: str
    expanded_prompt: str
    system_prompt: str
    negative_prompt: str
    is_image_tool: bool
    result: Dict[str, Any]


def prepare_prompt_node(state: StudioState) -> Dict[str, Any]:
    tool_id = state.get("tool_id", "script")
    prompt = state.get("user_prompt", "")
    style = state.get("style", "cinematic")
    aspect_ratio = state.get("aspect_ratio", "16:9")
    duration = str(state.get("duration", 6))
    camera = state.get("camera_movement", "smooth dolly")

    is_image = tool_id in IMAGE_TOOLS

    if is_image:
        expanded = build_image_prompt(
            tool_id,
            prompt,
            aspect_ratio=aspect_ratio,
            style=style,
            duration=duration,
            camera_movement=camera,
        )
        neg = get_negative_prompt(tool_id)
        sys_p = get_system_prompt(tool_id)
    else:
        expanded = build_text_prompt(
            tool_id,
            prompt,
            aspect_ratio=aspect_ratio,
            style=style,
            duration=duration,
            camera_movement=camera,
        )
        neg = ""
        sys_p = get_system_prompt(tool_id)

    return {
        "is_image_tool": is_image,
        "expanded_prompt": expanded,
        "negative_prompt": neg,
        "system_prompt": sys_p,
    }


def execute_tool_node(state: StudioState) -> Dict[str, Any]:
    tool_id = state.get("tool_id", "script")
    is_image = state.get("is_image_tool", False)
    prompt = state.get("expanded_prompt", "")
    aspect_ratio = state.get("aspect_ratio", "16:9")

    if is_image:
        neg = state.get("negative_prompt", "")
        simulated = False
        try:
            preview_url = generate_image(
                prompt=prompt,
                negative_prompt=neg,
                aspect_ratio=aspect_ratio,
            )
        except Exception as exc:
            logger.warning("Local SDXL unavailable (%s), using procedural visual card.", exc)
            from app.ai.providers.diffusion_provider import generate_fallback_image
            preview_url = generate_fallback_image(
                prompt,
                aspect_ratio=aspect_ratio,
                style=state.get("style", "Cinematic"),
            )
            simulated = True

        return {
            "result": {
                "tool_id": tool_id,
                "preview_url": preview_url,
                "generated_text": None,
                "model_output": {"prompt": prompt, "aspect_ratio": aspect_ratio, "status": "generated"},
                "simulated": simulated,
            }
        }
    else:
        system = state.get("system_prompt", "")
        raw_text = generate_text(prompt, system=system, json_mode=True)
        parsed = parse_json_from_llm(raw_text)
        return {
            "result": {
                "tool_id": tool_id,
                "preview_url": None,
                "generated_text": raw_text,
                "model_output": parsed,
                "simulated": False,
            }
        }


def build_studio_graph():
    workflow = create_state_graph(StudioState)
    workflow.add_node("prepare_prompt", prepare_prompt_node)
    workflow.add_node("execute_tool", execute_tool_node)

    workflow.set_entry_point("prepare_prompt")
    workflow.add_edge("prepare_prompt", "execute_tool")
    workflow.add_edge("execute_tool", END)

    return workflow.compile()


studio_graph = build_studio_graph()


def run_studio_tool(
    tool_id: str,
    prompt: str,
    style: str | None = None,
    aspect_ratio: str | None = None,
    duration: int | None = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Execute any studio tool through the Studio LangGraph router."""
    state = studio_graph.invoke({
        "tool_id": tool_id,
        "user_prompt": prompt,
        "style": style or "Cinematic",
        "aspect_ratio": aspect_ratio or "16:9",
        "duration": duration or 6,
    })
    return state.get("result", {})
