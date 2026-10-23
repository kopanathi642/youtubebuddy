"""
AI Agent Manager — Powered by LangGraph.

Delegates agent pipelines to compiled LangGraph state graphs.
"""
import logging
from typing import Any, Dict

from app.ai.graphs import (
    run_full_pipeline,
    run_script_agent as lg_run_script,
    run_seo_agent as lg_run_seo,
    run_shorts_agent as lg_run_shorts,
    run_trend_agent as lg_run_trend,
    run_upload_agent as lg_run_upload,
)

logger = logging.getLogger(__name__)


def run_trend_agent(context: str, provider: str = "ollama") -> dict:
    logger.info("Running LangGraph trend agent")
    return lg_run_trend(context)


def run_script_agent(topic: str, provider: str = "ollama", duration: str = "10", style: str = "educational") -> dict:
    logger.info("Running LangGraph script agent | topic=%s", topic[:60])
    return lg_run_script(topic, duration=duration, style=style)


def run_seo_agent(topic: str, provider: str = "ollama") -> dict:
    logger.info("Running LangGraph SEO agent | topic=%s", topic[:60])
    return lg_run_seo(topic)


def run_shorts_agent(upload_name: str, provider: str = "ollama") -> dict:
    logger.info("Running LangGraph shorts agent | upload=%s", upload_name)
    return lg_run_shorts(upload_name)


def run_upload_agent(context: str, provider: str = "ollama") -> dict:
    logger.info("Running LangGraph upload agent")
    return lg_run_upload(context)


def run_pipeline(initial_topic: str) -> dict:
    logger.info("Running LangGraph creator pipeline for: %s", initial_topic)
    return run_full_pipeline(initial_topic)
