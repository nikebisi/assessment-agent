"""Unit tests verifying structured JSON logging, Intent vs. Outcome tracking, and PII redaction."""

import json
import logging
from io import StringIO

from app.observability import (
    JsonFormatter,
    log_intent,
    log_outcome,
    redact_pii,
    redact_pii_string,
)


def test_pii_redaction_strings():
    """Verify regex scrubber masks emails, phone numbers, handles, SSNs, cards, and IPs."""
    raw_text = (
        "Contact me at creator_alice@viralmail.com or call +1-555-234-5678. "
        "My handle is @real_alice_99, SSN 123-45-6789, card 4111-2222-3333-4444, IP 192.168.1.100."
    )
    cleaned = redact_pii_string(raw_text)

    assert "[REDACTED_EMAIL]" in cleaned
    assert "creator_alice@viralmail.com" not in cleaned

    assert "[REDACTED_PHONE]" in cleaned
    assert "555-234-5678" not in cleaned

    assert "[REDACTED_HANDLE]" in cleaned
    assert "@real_alice_99" not in cleaned

    assert "[REDACTED_SSN]" in cleaned
    assert "123-45-6789" not in cleaned

    assert "[REDACTED_CARD]" in cleaned
    assert "4111-2222-3333-4444" not in cleaned

    assert "[REDACTED_IP]" in cleaned
    assert "192.168.1.100" not in cleaned


def test_pii_redaction_recursive_structures():
    """Verify deep PII redaction across nested dictionaries and lists."""
    payload = {
        "user_email": "jane.doe@example.org",
        "contacts": ["+1-800-555-0199", "regular text"],
        "metadata": {"nested_ip": "10.0.0.1", "creator_tag": "@tiktok_guru"},
    }
    scrubbed = redact_pii(payload)

    assert scrubbed["user_email"] == "[REDACTED_EMAIL]"
    assert scrubbed["contacts"][0] == "[REDACTED_PHONE]"
    assert scrubbed["contacts"][1] == "regular text"
    assert scrubbed["metadata"]["nested_ip"] == "[REDACTED_IP]"
    assert scrubbed["metadata"]["creator_tag"] == "[REDACTED_HANDLE]"


def test_json_formatter_valid_structure():
    """Verify JsonFormatter outputs valid, parseable JSON with expected fields and scrubbed PII."""
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())

    test_logger = logging.getLogger("test.observability.logger")
    test_logger.handlers = [handler]
    test_logger.setLevel(logging.INFO)

    test_logger.info(
        "User @john_doe created session with john@gmail.com",
        extra={
            "intent": "session_initiation",
            "outcome": "success",
            "component": "auth_node",
            "details": {"client_ip": "172.16.254.1"},
        },
    )

    output = stream.getvalue().strip()
    log_record = json.loads(output)

    assert log_record["severity"] == "INFO"
    assert log_record["logger"] == "test.observability.logger"
    assert "[REDACTED_HANDLE]" in log_record["message"]
    assert "[REDACTED_EMAIL]" in log_record["message"]
    assert log_record["intent"] == "session_initiation"
    assert log_record["outcome"] == "success"
    assert log_record["component"] == "auth_node"
    assert log_record["details"]["client_ip"] == "[REDACTED_IP]"
    assert "timestamp" in log_record


def test_intent_and_outcome_telemetry_helpers():
    """Verify log_intent and log_outcome functions execute without error and produce structured logs."""
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())

    telemetry_logger = logging.getLogger("instatrend.telemetry")
    telemetry_logger.handlers = [handler]
    telemetry_logger.setLevel(logging.INFO)

    log_intent(
        "scrub_ai_cliches", "auditing_caption_batch", {"sample": "test@domain.com"}
    )
    log_outcome("scrub_ai_cliches", "success", {"is_clean": True})

    lines = [line for line in stream.getvalue().strip().split("\n") if line]
    assert len(lines) >= 2

    intent_json = json.loads(lines[0])
    assert intent_json["intent"] == "auditing_caption_batch"
    assert intent_json["component"] == "scrub_ai_cliches"
    assert intent_json["details"]["sample"] == "[REDACTED_EMAIL]"

    outcome_json = json.loads(lines[1])
    assert outcome_json["outcome"] == "success"
    assert outcome_json["component"] == "scrub_ai_cliches"
    assert outcome_json["details"]["is_clean"] is True
