"""
Full per-deal scoring pipeline: RAG context -> guardrails -> prompt -> Claude
-> validated JSON -> guardrail force-score enforcement, with a safe fallback
if Claude or the CLI call fails for any reason.
"""
import logging

from pydantic import ValidationError

import config
from claude_cli.client import run_json_prompt, ClaudeCLIError
from guardrails.engine import run_guardrails
from knowledge_base.retriever import retrieve_context
from scoring.models import ScoreResult
from scoring.prompt_builder import build_scoring_prompt

logger = logging.getLogger(__name__)


def score_deal(deal: dict) -> dict:
    """
    Score one normalized deal dict (as produced by input.extractor.extract_deal_from_pdf).

    1. Retrieve RAG context from the knowledge base
    2. Run guardrails (hard rules)
    3. Build the scoring prompt
    4. Call Claude via the CLI
    5. Validate the JSON response against ScoreResult
    6. Enforce guardrail force_score — AI cannot override a CRITICAL flag
    """
    logger.info(f"Scoring deal: {deal['name']}")

    rag_context = retrieve_context(deal)
    guardrail_output = run_guardrails(deal)
    prompt = build_scoring_prompt(deal, guardrail_output, rag_context)

    try:
        raw_result = run_json_prompt(prompt, timeout=config.CLAUDE_CLI_TIMEOUT)
        validated = ScoreResult(**raw_result)
        score_result = validated.model_dump()
    except (ClaudeCLIError, ValueError, ValidationError) as e:
        logger.error(f"Scoring failed for {deal['name']}: {e}")
        return fallback_score(deal, guardrail_output)

    if guardrail_output["force_score"]:
        score_result["final_score"] = guardrail_output["force_score"]
        score_result["guardrail_override"] = True
    else:
        score_result["guardrail_override"] = False

    score_result["needs_human_review"] = guardrail_output["needs_human_review"]
    score_result["guardrail_flags"] = guardrail_output["flags"]
    score_result["deal_name"] = deal["name"]
    score_result["account_name"] = deal["account_name"]
    score_result["owner_email"] = deal["owner_email"]
    score_result["owner_name"] = deal["owner_name"]
    score_result["deal_id"] = deal["id"]
    score_result["policy_version"] = config.POLICY_VERSION
    score_result["low_confidence_extraction"] = deal.get("low_confidence_extraction", False)

    logger.info(
        f"Score for {deal['name']}: {score_result['final_score']} "
        f"({score_result['confidence']}% confidence)"
    )
    return score_result


def fallback_score(deal: dict, guardrail_output: dict) -> dict:
    """Safe fallback using guardrail output only, used when Claude scoring fails."""
    return {
        "final_score": guardrail_output["pre_score"],
        "confidence": 40,
        "risk_factors": [{
            "factor": "Scoring engine error",
            "severity": "Medium",
            "explanation": "AI scoring was unavailable. Score is based on guardrails only.",
        }],
        "recommended_actions": [{
            "action": "Manual review required",
            "timeline": "Today",
            "owner": "Sales Manager",
        }],
        "policy_references": [],
        "narrative_summary": "Automated scoring failed. Guardrail pre-score applied.",
        "confidence_explanation": "Fallback score — low confidence.",
        "guardrail_override": bool(guardrail_output["force_score"]),
        "needs_human_review": True,
        "guardrail_flags": guardrail_output["flags"],
        "deal_name": deal["name"],
        "account_name": deal["account_name"],
        "owner_email": deal["owner_email"],
        "owner_name": deal["owner_name"],
        "deal_id": deal["id"],
        "policy_version": config.POLICY_VERSION,
        "low_confidence_extraction": deal.get("low_confidence_extraction", False),
    }
