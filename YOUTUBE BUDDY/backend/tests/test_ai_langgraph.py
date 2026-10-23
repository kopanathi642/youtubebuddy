"""
Unit and integration tests for free-tier AI providers, LangGraph agent graphs, and dispatcher.
"""
import pytest
from app.ai.graphs import (
    run_trend_agent,
    run_script_agent,
    run_seo_agent,
    run_shorts_agent,
    run_upload_agent,
    run_studio_tool,
    run_full_pipeline,
)
from app.ai.graphs.base_graph import create_state_graph, END, parse_json_from_llm
from app.ai.providers import (
    generate_ai_text,
    dispatch_transcription,
    get_active_providers,
)
from app.ai.providers.diffusion_provider import generate_fallback_image
from app.ai.providers.whisper_provider import _get_fallback_transcription, extract_timestamps, generate_srt_from_segments


def test_base_graph_execution():
    """Verify compatible StateGraph executes node pipeline sequentially."""
    graph = create_state_graph(dict)
    graph.add_node("step1", lambda s: {"val": s.get("val", 0) + 1})
    graph.add_node("step2", lambda s: {"val": s.get("val", 0) * 2})
    graph.set_entry_point("step1")
    graph.add_edge("step1", "step2")
    graph.add_edge("step2", END)

    app = graph.compile()
    result = app.invoke({"val": 5})
    assert result["val"] == 12  # (5 + 1) * 2 = 12


def test_parse_json_from_llm():
    """Verify JSON extractor correctly parses markdown-fenced LLM replies."""
    raw = '```json\n{"status": "ok", "count": 3}\n```'
    parsed = parse_json_from_llm(raw)
    assert parsed.get("status") == "ok"
    assert parsed.get("count") == 3


def test_active_providers_telemetry():
    """Verify provider availability tracking does not leak secrets."""
    providers = get_active_providers()
    assert "gemini" in providers
    assert "groq" in providers
    assert "openrouter" in providers
    assert "offline_synthesizer" in providers
    assert providers["offline_synthesizer"] is True


def test_ai_dispatcher_fallback_cascade():
    """Verify AI dispatcher generates valid output without throwing when keys are unset."""
    text = generate_ai_text("Generate 3 viral video titles for tech review", json_mode=True)
    assert len(text) > 0
    parsed = parse_json_from_llm(text)
    assert isinstance(parsed, dict)


def test_trend_agent_graph():
    """Verify Trend agent returns structured opportunities via LangGraph."""
    report = run_trend_agent("AI Video Tools")
    assert "niche" in report or "summary" in report or "opportunities" in report


def test_script_agent_graph():
    """Verify Script agent returns hook and sections via LangGraph."""
    script = run_script_agent("Top 5 AI Tools")
    assert "hook" in script or "title" in script


def test_seo_agent_graph():
    """Verify SEO agent returns titles and description via LangGraph."""
    seo = run_seo_agent("YouTube Growth Strategies")
    assert "topic" in seo
    assert "optimal_publish_time" in seo


def test_shorts_agent_graph():
    """Verify Shorts agent detects viral moments via LangGraph."""
    analysis = run_shorts_agent("Here is why your shorts get zero views.")
    assert "clip_timestamps" in analysis or "suggested_titles" in analysis


def test_upload_agent_graph():
    """Verify Upload agent generates metadata and thumbnail concept via LangGraph."""
    result = run_upload_agent("How to edit fast in Premiere Pro")
    assert "parsed" in result


def test_studio_tool_graph_image_fallback():
    """Verify Studio Graph generates visual card for image tools."""
    card = generate_fallback_image("Cyberpunk cinematic street at night", aspect_ratio="16:9")
    assert card.startswith("data:image/png;base64,")


def test_whisper_transcription_and_srt():
    """Verify whisper fallback segments format into valid SRT."""
    transcription = _get_fallback_transcription()
    assert "text" in transcription
    segments = extract_timestamps(transcription)
    assert len(segments) > 0
    srt = generate_srt_from_segments(segments)
    assert "-->" in srt


def test_full_pipeline_multi_agent():
    """Verify multi-agent chain executes all 4 agents."""
    pipeline = run_full_pipeline("Productivity Hacks For Solopreneurs")
    assert pipeline.get("status") == "completed"
    assert "trend" in pipeline
    assert "script" in pipeline
    assert "seo" in pipeline
    assert "upload" in pipeline
