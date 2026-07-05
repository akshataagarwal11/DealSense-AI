from datetime import datetime
import logging
import config

logger = logging.getLogger(__name__)


def run_guardrails(deal: dict) -> dict:
    """
    Apply all hard business rules to the deal.

    Guardrails are enterprise policies that the AI cannot override.
    If a CRITICAL rule triggers, the final AI score must respect it.
    """

    flags = []
    critical_flags = []
    positive_signals = []

    pre_score = "Medium"
    force_score = None
    needs_human_review = False

    # --------------------------------------------------------
    # CRITICAL RULE: No recent customer activity
    # --------------------------------------------------------
    if deal.get("days_since_activity", 999) > config.GUARDRAIL_HIGH_RISK_DAYS_NO_ACTIVITY:
        msg = (
            f"CRITICAL: No activity for "
            f"{deal['days_since_activity']} days "
            f"(threshold: {config.GUARDRAIL_HIGH_RISK_DAYS_NO_ACTIVITY})"
        )

        critical_flags.append(msg)
        force_score = "High"

    # --------------------------------------------------------
    # CRITICAL RULE: Deal stalled in current stage
    # --------------------------------------------------------
    if deal.get("days_in_stage", 0) > config.GUARDRAIL_HIGH_RISK_DAYS_IN_STAGE:

        msg = (
            f"CRITICAL: Deal stalled "
            f"{deal.get('days_in_stage')} days "
            f"in stage '{deal.get('stage')}'"
        )

        critical_flags.append(msg)
        force_score = "High"

    # --------------------------------------------------------
    # CRITICAL RULE: Close date already passed
    # --------------------------------------------------------
    if deal.get("days_to_close") is not None:

        if deal["days_to_close"] < 0:

            critical_flags.append(
                f"CRITICAL: Close date passed "
                f"{abs(deal['days_to_close'])} days ago"
            )

            force_score = "High"

    # --------------------------------------------------------
    # WARNING RULES
    # --------------------------------------------------------

    # Future enhancement:
    # Compare current amount vs OpportunityHistory
    # to detect scope reduction.

    if not deal.get("next_step") or deal["next_step"] == "Not specified":

        flags.append(
            "WARNING: No next step defined — deal may lack momentum."
        )

    if (
        deal.get("probability", 0) < 20
        and deal.get("stage")
        not in ["Prospecting", "Qualification"]
    ):

        flags.append(
            f"WARNING: Low probability "
            f"({deal.get('probability')}%) "
            f"for stage '{deal.get('stage')}'."
        )

    # --------------------------------------------------------
    # POSITIVE SIGNALS
    # --------------------------------------------------------

    if (
        deal.get("days_since_activity", 999)
        <= config.GUARDRAIL_LOW_RISK_RECENT_ACTIVITY_DAYS
    ):

        positive_signals.append(
            f"POSITIVE: Recent customer activity "
            f"({deal['days_since_activity']} days ago)."
        )

        if force_score is None:
            pre_score = "Low"

    if (
        deal.get("stage")
        in ["Negotiation", "Closing", "Proposal/Price Quote"]
        and deal.get("days_since_activity", 999) < 7
    ):

        positive_signals.append(
            "POSITIVE: Late-stage opportunity with recent customer engagement."
        )

    # --------------------------------------------------------
    # ESCALATION RULE
    # --------------------------------------------------------

    if deal.get("amount", 0) >= config.GUARDRAIL_ENTERPRISE_REVIEW_THRESHOLD:

        needs_human_review = True

        flags.append(
            f"ESCALATION: Deal value "
            f"${deal['amount']:,.0f} exceeds "
            f"${config.GUARDRAIL_ENTERPRISE_REVIEW_THRESHOLD:,.0f}. "
            f"Human review required."
        )

    # --------------------------------------------------------
    # Final Pre-Score
    # --------------------------------------------------------

    if force_score:
        pre_score = force_score

    all_flags = critical_flags + flags + positive_signals

    result = {
        "pre_score": pre_score,
        "force_score": force_score,
        "flags": all_flags,
        "critical_flags": critical_flags,
        "positive_signals": positive_signals,
        "needs_human_review": needs_human_review,
        "guardrail_triggered": bool(critical_flags),
    }

    logger.info(
        f"Guardrails | Deal='{deal.get('name')}' "
        f"| Score={pre_score} "
        f"| Critical={len(critical_flags)} "
        f"| Flags={len(flags)} "
        f"| Positive={len(positive_signals)} "
        f"| HumanReview={needs_human_review}"
    )

    return result