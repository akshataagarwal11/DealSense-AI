"""
Email delivery — currently stubbed. Logs what would be sent (to/cc/subject/
attachment) and returns True, so the pipeline's control flow and CC-on-High-Risk
logic can be exercised end-to-end before a real provider (SMTP/SendGrid/etc.)
is wired in. To go live later, replace the body of send_risk_report_email()
with an actual send call — the signature and caller (main.py) don't need to change.
"""
import logging
import os

logger = logging.getLogger(__name__)

SCORE_EMOJI = {"High": "\U0001F534", "Medium": "\U0001F7E1", "Low": "\U0001F7E2"}


def send_risk_report_email(score_result: dict, pdf_path: str, manager_email: str = None) -> bool:
    """
    Log the risk report email that would be sent (recipient, CC, subject, attachment).
    CCs the manager when the score is High or the deal needs human review.
    Returns True — mirrors the interface a real sender would have.
    """
    score = score_result["final_score"]
    emoji = SCORE_EMOJI.get(score, "")
    deal_name = score_result["deal_name"]
    account = score_result["account_name"]
    owner_email = score_result.get("owner_email") or "(no owner email extracted)"
    confidence = score_result["confidence"]

    subject = f"{emoji} DealSense AI Risk Report — {deal_name} ({account}) — {score} RISK"

    cc = None
    if (score == "High" or score_result.get("needs_human_review")) and manager_email:
        cc = manager_email

    logger.info(
        f"[EMAIL STUB] Would send to={owner_email} cc={cc or '-'} "
        f"subject='{subject}' confidence={confidence}% attachment={os.path.basename(pdf_path)}"
    )
    return True
