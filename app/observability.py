"""Structured JSON Logging, Intent vs. Outcome Telemetry, and PII Redaction for InstaTrend Agent."""

from __future__ import annotations

import datetime
import json
import logging
import re
import sys
from typing import Any

# Optional OpenTelemetry integration
try:
    from opentelemetry import trace

    HAS_OTEL = True
except ImportError:
    HAS_OTEL = False


# =====================================================================
# PII Redaction Engine
# =====================================================================

# Regex patterns for detecting and masking sensitive user information
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
PHONE_REGEX = re.compile(r"(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
HANDLE_REGEX = re.compile(r"@(?!(?:everyone|channel|here)\b)[A-Za-z0-9_]{3,30}\b")
SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CREDIT_CARD_REGEX = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")
IP_REGEX = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
)


def redact_pii_string(text: str) -> str:
    """Scrubs sensitive Personally Identifiable Information (PII) from strings using regex patterns.

    Args:
        text: The raw string to sanitize.

    Returns:
        Sanitized string with PII replaced by redaction tags.
    """
    if not isinstance(text, str):
        return text

    sanitized = EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)
    sanitized = PHONE_REGEX.sub("[REDACTED_PHONE]", sanitized)
    sanitized = SSN_REGEX.sub("[REDACTED_SSN]", sanitized)
    sanitized = CREDIT_CARD_REGEX.sub("[REDACTED_CARD]", sanitized)
    sanitized = IP_REGEX.sub("[REDACTED_IP]", sanitized)
    sanitized = HANDLE_REGEX.sub("[REDACTED_HANDLE]", sanitized)
    return sanitized


def redact_pii(data: Any) -> Any:
    """Recursively traverses dictionaries, lists, and strings to redact PII.

    Args:
        data: Arbitrary data structure to scrub.

    Returns:
        Deep-scrubbed copy of the data structure.
    """
    if isinstance(data, str):
        return redact_pii_string(data)
    elif isinstance(data, dict):
        return {k: redact_pii(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [redact_pii(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(redact_pii(item) for item in data)
    return data


# =====================================================================
# Structured JSON Logging Formatter
# =====================================================================


class JsonFormatter(logging.Formatter):
    """Custom logging formatter outputting single-line parsable JSON with OpenTelemetry trace correlation."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "severity": record.levelname,
            "logger": record.name,
            "message": redact_pii_string(record.getMessage()),
        }

        # Inject OpenTelemetry trace and span IDs if available
        if HAS_OTEL:
            span = trace.get_current_span()
            span_ctx = span.get_span_context()
            if span_ctx and span_ctx.is_valid:
                log_data["trace_id"] = f"{span_ctx.trace_id:032x}"
                log_data["span_id"] = f"{span_ctx.span_id:016x}"

        # Inject custom intent vs. outcome fields if passed via extra
        if hasattr(record, "intent"):
            log_data["intent"] = redact_pii(record.intent)
        if hasattr(record, "outcome"):
            log_data["outcome"] = redact_pii(record.outcome)
        if hasattr(record, "component"):
            log_data["component"] = record.component
        if hasattr(record, "details"):
            log_data["details"] = redact_pii(record.details)

        # Include exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def configure_structured_logging(log_level: int = logging.INFO) -> None:
    """Configures the root logger with the JsonFormatter to ensure 100% structured JSON logging."""
    root = logging.getLogger()
    root.setLevel(log_level)

    # Remove existing stream handlers
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)


# =====================================================================
# Telemetry Helpers for Intent vs. Outcome
# =====================================================================

_logger = logging.getLogger("instatrend.telemetry")


def log_intent(
    component: str, intent_name: str, payload: dict[str, Any] | None = None
) -> None:
    """Logs the explicit target intent before invoking a tool, node, or LLM call.

    Args:
        component: The calling agent node or tool name.
        intent_name: Descriptive action intent (e.g. 'parsing_visual_semantics', 'fetch_tiktok_trends').
        payload: Sanitized input metadata or parameters.
    """
    _logger.info(
        f"Intent started: {intent_name} in {component}",
        extra={
            "component": component,
            "intent": intent_name,
            "details": redact_pii(payload or {}),
        },
    )


def log_outcome(
    component: str,
    outcome_status: str,
    details: dict[str, Any] | None = None,
    error: str | None = None,
) -> None:
    """Logs the explicit execution outcome after a tool or node completes.

    Args:
        component: The calling agent node or tool name.
        outcome_status: Outcome status (e.g. 'success', 'retry', 'error', 'approved').
        details: Sanitized result metrics or execution summary.
        error: Error message if failed.
    """
    level = logging.ERROR if outcome_status == "error" else logging.INFO
    _logger.log(
        level,
        f"Outcome finished: {outcome_status} in {component}",
        extra={
            "component": component,
            "outcome": outcome_status,
            "details": redact_pii(details or {}),
            "error": redact_pii_string(error) if error else None,
        },
    )
