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


from app.ai.providers.errors import ProviderUnavailable

@pytest.fixture
def engines_offline(monkeypatch):
    from app.ai.providers import ai_dispatcher
    from app.core.config import settings
    monkeypatch.setattr(ai_dispatcher, 'is_ollama_online', lambda: False)
    monkeypatch.setattr(settings, 'ALLOW_REMOTE_INFERENCE', False)
    monkeypatch.setattr(settings, 'LOCAL_IMAGE_MODEL_PATH', None)

def test_active_providers_telemetry(engines_offline):
    providers=get_active_providers()
    assert providers['offline_synthesizer'] is False
    assert providers['ollama_local'] is False
    assert not any(providers.values())

@pytest.mark.parametrize('run,args',[
    (generate_ai_text,('Generate titles',)),
    (run_trend_agent,('Video tools',)),
    (run_script_agent,('A tutorial',)),
    (run_seo_agent,('Creator workflow',)),
    (run_shorts_agent,('A supplied transcript',)),
    (run_upload_agent,('Editing guide',)),
    (run_full_pipeline,('Production planning',)),
])
def test_agents_fail_honestly_without_an_engine(engines_offline,run,args):
    with pytest.raises(ProviderUnavailable):run(*args)

def test_procedural_poster_is_not_returned_as_generated_media():
    with pytest.raises(RuntimeError):generate_fallback_image('A scene')

def test_whisper_unavailable_is_not_a_transcript():
    with pytest.raises(ProviderUnavailable):_get_fallback_transcription()

def test_caption_serializer_with_explicit_test_fixture():
    segments=[{'start':0.0,'end':1.5,'text':'Synthetic serializer fixture.'}]
    assert '-->' in generate_srt_from_segments(segments)
