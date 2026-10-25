"""Capability-specific gateway. Explicit choices never silently switch providers."""
from typing import Any
from pathlib import Path
from app.core.config import settings
from app.ai.providers.errors import ProviderUnavailable
from app.ai.providers.ollama_provider import generate_text as ollama_generate, is_ollama_online
from app.ai.providers.gemini_provider import generate_text as gemini_generate, is_gemini_available
from app.ai.providers.groq_provider import generate_text as groq_generate, is_groq_available, transcribe_audio_groq
from app.ai.providers.openrouter_provider import generate_text as openrouter_generate, is_openrouter_available


def get_active_providers():
    remote = settings.ALLOW_REMOTE_INFERENCE
    return {"gemini":remote and is_gemini_available(),"groq":remote and is_groq_available(),"openrouter":remote and is_openrouter_available(),"ollama_local":is_ollama_online(),"offline_synthesizer":False}


def provider_status():
    active=get_active_providers()
    return {"active_default":next((k for k,v in active.items() if v),None),"remote_inference_allowed":settings.ALLOW_REMOTE_INFERENCE,"providers":{name:{"name":name,"configured":bool(enabled),"available":bool(enabled) if name=="ollama_local" else False,"status":("service_reachable" if enabled else "requires_configuration") if name=="ollama_local" else ("requires_verification" if enabled else "requires_configuration"),"verification":"Ollama service probe" if name=='ollama_local' else "Configuration only; live credentials and quotas not verified"} for name,enabled in active.items() if name!='offline_synthesizer'},"image":{"available":False,"configured":bool(settings.LOCAL_IMAGE_MODEL_PATH and Path(settings.LOCAL_IMAGE_MODEL_PATH).is_dir()),"status":"requires_configuration","message":"Installed checkpoint and successful GPU inference must be verified."},"video":{"available":False,"status":"requires_configuration","message":"No generative video adapter installed."}}


def generate_ai_text(prompt: str, system: str | None=None, preferred_provider: str | None=None, temperature: float=.7, max_tokens: int=2048, json_mode: bool=False) -> str:
    if not prompt.strip() or len(prompt)>30000:raise ValueError("Prompt must contain 1–30,000 characters.")
    target=(preferred_provider or settings.AI_PROVIDER_DEFAULT or 'auto').lower()
    entries={'ollama':(is_ollama_online,ollama_generate),'gemini':(is_gemini_available,gemini_generate),'groq':(is_groq_available,groq_generate),'openrouter':(is_openrouter_available,openrouter_generate)}
    if target not in {*entries,'auto'}:raise ProviderUnavailable(f"Provider {target} has no configured text adapter.","text")
    candidates=['ollama'] if target=='auto' else [target]
    if target=='auto' and settings.ALLOW_REMOTE_INFERENCE:candidates+=['gemini','groq','openrouter']
    for name in candidates:
        if name!='ollama' and not settings.ALLOW_REMOTE_INFERENCE:raise ProviderUnavailable("Remote inference is disabled. An owner must explicitly enable it after reviewing cost and privacy.","text")
        available,run=entries[name]
        if not available():continue
        try:
            result=run(prompt,system=system,temperature=temperature,max_tokens=max_tokens,json_mode=json_mode)
            if not isinstance(result,str) or not result.strip():raise RuntimeError("Provider returned empty text.")
            return result
        except Exception as exc:
            # Do not quietly send the same private input to a different provider after failure.
            raise ProviderUnavailable(f"Selected text engine failed: {type(exc).__name__}. Retry or change configuration.","text") from exc
    raise ProviderUnavailable("No compatible text engine is available. Start Ollama and install a licensed local model, or explicitly configure a permitted provider.","text")


def dispatch_transcription(audio_path: str, language: str='en') -> dict[str,Any]:
    if not Path(audio_path).is_file():raise FileNotFoundError("Audio source does not exist.")
    if settings.ALLOW_REMOTE_INFERENCE and is_groq_available():
        result=transcribe_audio_groq(audio_path,language=language)
    else:
        from app.ai.providers.whisper_provider import transcribe_audio
        result=transcribe_audio(audio_path,language=language)
    if result.get('simulated'):raise ProviderUnavailable("Simulated transcription is rejected.","transcription")
    return result
