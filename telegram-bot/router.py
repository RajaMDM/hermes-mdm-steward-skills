"""
Intent router for the HERMES MDM Steward Telegram bot.

Uses Claude (Haiku model for speed/cost) to classify a free-text user message
into one of the HERMES MDM skill agent IDs. Falls back to GENERAL if classification
is uncertain.
"""

import json
import logging

import anthropic

from agents import AgentID
from config import CLAUDE_ROUTER_MODEL

logger = logging.getLogger(__name__)

_ROUTER_SYSTEM = """
You are a routing classifier for the HERMES MDM Steward assistant.
Given a user message, output ONLY a JSON object — nothing else.

Available agents:
- "dqaudit"   → data quality audit, DQ check, audit master data, profile data, completeness check,
                 format violations, duplicate scan, nightly audit
- "dedup"     → duplicate detection, match/merge decision, same supplier check, dedupe, entity resolution,
                 are these the same entity, two records same entity
- "golden"    → golden record, survivorship, consolidation, winning values, source of truth,
                 compose golden record, cross-reference
- "location"  → address validation, address cleanup, PO Box, emirate, region, governorate,
                 GCC address, location master, coordinates, standardize address
- "briefing"  → steward briefing, morning briefing, what needs attention today, daily update,
                 SLA watch, exception queue, trending issues
- "supplier"  → supplier name cleanup, normalize supplier, standardize name, legal entity suffix,
                 LLC formatting, trading name, DBA, supplier record formatting
- "general"   → general help, navigation, questions about MDM, unclear intent, what can you do

Return exactly:
{"agent": "<agent_id>", "confidence": <0.0-1.0>}

If confidence < 0.6, use "general".
"""


async def classify_intent(
    client: anthropic.AsyncAnthropic,
    user_message: str,
) -> AgentID:
    """
    Classify a natural-language message into the most appropriate HERMES MDM agent.

    Returns AgentID.GENERAL on any error or low-confidence classification.
    """
    try:
        response = await client.messages.create(
            model=CLAUDE_ROUTER_MODEL,
            max_tokens=64,
            system=_ROUTER_SYSTEM,
            messages=[{"role": "user", "content": user_message}],
        )
        raw = response.content[0].text.strip()

        # Strip any accidental markdown fences
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        parsed = json.loads(raw)
        agent_str: str = parsed.get("agent", "general")
        confidence: float = float(parsed.get("confidence", 0.0))

        if confidence < 0.6:
            logger.debug(
                "Router low confidence (%.2f) for '%s' → general",
                confidence,
                user_message[:60],
            )
            return AgentID.GENERAL

        try:
            agent_id = AgentID(agent_str)
        except ValueError:
            logger.warning("Router returned unknown agent '%s'", agent_str)
            return AgentID.GENERAL

        logger.debug(
            "Router classified '%s' → %s (confidence %.2f)",
            user_message[:60],
            agent_id,
            confidence,
        )
        return agent_id

    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        logger.warning("Router parse error: %s | raw='%s'", exc, locals().get("raw", ""))
        return AgentID.GENERAL
    except anthropic.APIError as exc:
        logger.error("Router API error: %s", exc)
        return AgentID.GENERAL
