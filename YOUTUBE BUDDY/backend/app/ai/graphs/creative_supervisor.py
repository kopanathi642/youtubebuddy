"""Native LangGraph supervisor for bounded creative work.

This graph performs no network requests or publishing. Real model workers are
explicitly injected by the service owner; absent workers fail closed. Planning
nodes label deterministic formatting rather than claiming model inference.
"""
import logging
from typing import Any, Callable, TypedDict

logger = logging.getLogger(__name__)

TASKS = ("brief", "storyboard", "generate", "quality", "delivery")


class CreativeState(TypedDict, total=False):
    objective: str
    tasks: list[str]
    cursor: int
    next_task: str
    status: str
    outputs: dict[str, Any]
    trace: list[dict[str, Any]]
    error: str


def validate_request(objective: str, tasks: list[str]) -> None:
    if not isinstance(objective, str) or not objective.strip() or len(objective) > 12000:
        raise ValueError("Provide a creative objective between 1 and 12,000 characters.")
    if not tasks or len(tasks) > len(TASKS) or len(tasks) != len(set(tasks)) or any(t not in TASKS for t in tasks):
        raise ValueError("Choose unique supported creative tasks.")
    if tasks != sorted(tasks, key=TASKS.index):
        raise ValueError("Tasks must follow brief, storyboard, generate, quality, delivery order.")


def compile_creative_supervisor(workers: dict[str, Callable[[CreativeState], dict[str, Any]]] | None = None):
    # Deliberately no compatibility fallback: runtime identity must be truthful.
    try:
        from langgraph.graph import StateGraph, START, END
    except ImportError as exc:
        raise RuntimeError("Native LangGraph is required. Install requirements-runtime.txt.") from exc

    workers = dict(workers or {})
    if any(name not in ("generate", "quality") for name in workers):
        raise ValueError("Only generation and artifact-quality workers can be registered.")

    def supervisor(state: CreativeState) -> dict[str, Any]:
        cursor = state.get("cursor", 0)
        if state.get("status") in ("blocked", "failed", "awaiting_review") or cursor >= len(state["tasks"]):
            return {"next_task": "finish"}
        return {"next_task": state["tasks"][cursor]}

    def node(task: str):
        def execute(state: CreativeState) -> dict[str, Any]:
            outputs = dict(state.get("outputs", {}))
            status, detail = "completed", ""
            try:
                if task == "brief":
                    output = {"objective": state["objective"].strip(), "method": "deterministic brief formatting"}
                    detail = "Recorded your objective; no model inference."
                elif task == "storyboard":
                    paragraphs = [p.strip() for p in state["objective"].split("\n\n") if p.strip()]
                    output = {"shots": [{"number": i + 1, "direction": p} for i, p in enumerate(paragraphs[:100])], "method": "paragraph breakdown", "generated_media": False}
                    detail = "Prepared editable shot directions from your paragraphs."
                elif task in ("generate", "quality"):
                    if task not in workers:
                        status, detail = "blocked", f"No {task} worker registered. Configure and validate a real model/artifact worker."
                        output = None
                    elif task == "quality" and not outputs.get("generate", {}).get("artifact"):
                        status, detail, output = "blocked", "Artifact quality checks require a real generation artifact.", None
                    else:
                        output = workers[task](state)
                        if not isinstance(output, dict) or output.get("simulated"):
                            raise ValueError("Worker must return a real structured result; simulated output rejected.")
                        if task == "generate" and not output.get("artifact"):
                            raise ValueError("Generation worker returned no artifact.")
                        if task == "quality" and output.get("passed") is not True:
                            status, detail = "blocked", "Artifact did not pass its quality gate."
                        else:
                            detail = "Registered worker returned a result."
                else:
                    status, detail = "awaiting_review", "Review export decisions and source rights. No upload, publication or external delivery was performed."
                    output = {"published": False, "requires_user_review": True}
                if output is not None:
                    outputs[task] = output
            except Exception:
                logger.exception("Creative supervisor worker failed: %s", task)
                status, detail = "failed", f"{task} worker failed. Check server logs; no later step executed."
            return {"outputs": outputs, "cursor": state.get("cursor", 0) + 1, "status": status, "trace": [*state.get("trace", []), {"task": task, "status": status, "detail": detail}]}
        return execute

    builder = StateGraph(CreativeState)
    builder.add_node("supervisor", supervisor)
    builder.add_edge(START, "supervisor")
    for task in TASKS:
        builder.add_node(task, node(task))
        builder.add_edge(task, "supervisor")
    builder.add_conditional_edges("supervisor", lambda state: state["next_task"], {**{t: t for t in TASKS}, "finish": END})
    return builder.compile()


def run_creative_supervisor(objective: str, tasks: list[str], workers=None) -> dict[str, Any]:
    validate_request(objective, tasks)
    graph = compile_creative_supervisor(workers)
    result = graph.invoke({"objective": objective, "tasks": tasks, "cursor": 0, "status": "running", "outputs": {}, "trace": []}, {"recursion_limit": 20})
    return {"runtime": "langgraph", "status": result["status"], "trace": result["trace"], "outputs": result["outputs"], "published": False}
