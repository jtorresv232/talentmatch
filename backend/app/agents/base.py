import logging
import time
from typing import Any, TypedDict

logger = logging.getLogger(__name__)


class NodeLog(TypedDict):
    node: str
    input_summary: str
    output_summary: str
    duration_ms: float


class NodeLogger:
    """Utility for logging LangGraph node execution consistently."""

    def __init__(self, graph_name: str):
        self.graph_name = graph_name

    def log(
        self,
        node: str,
        input_summary: str,
        output_summary: str,
        start_time: float,
    ) -> NodeLog:
        duration_ms = (time.perf_counter() - start_time) * 1000
        entry: NodeLog = {
            "node": node,
            "input_summary": input_summary,
            "output_summary": output_summary,
            "duration_ms": round(duration_ms, 2),
        }
        logger.info(
            "[%s] node=%s | in=%s | out=%s | %.1fms",
            self.graph_name,
            node,
            input_summary,
            output_summary,
            duration_ms,
        )
        return entry


class BaseState(TypedDict, total=False):
    """Fields common to all agent graphs."""
    trace: list[NodeLog]
    error: str | None


def get_trace(state: dict[str, Any]) -> list[NodeLog]:
    return state.get("trace") or []
