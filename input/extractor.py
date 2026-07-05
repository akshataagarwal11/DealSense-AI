"""
Turns a freeform deal PDF (proposal, deal memo, account brief — whatever a
rep or CSM wrote) into the normalized deal dict that guardrails, scoring,
and the report generator all expect.

Field extraction is delegated to Claude (via claude_cli) since the source
text is unstructured prose, not a fixed template. Date math (days since
activity, days to close, etc.) is computed here in Python against the real
current date, rather than trusting the model to do arithmetic.
"""
import logging
import os
from datetime import datetime

from pypdf import PdfReader

import config
from claude_cli.client import run_json_prompt, ClaudeCLIError

logger = logging.getLogger(__name__)

# Fields we ask Claude to pull out of the raw document text. Anything not
# mentioned in the document must come back as null — never guessed.
EXTRACTION_FIELDS = [
    "deal_name", "account_name", "stage", "amount", "probability",
    "close_date", "last_activity_date", "created_date", "lead_source",
    "next_step", "description", "owner_name", "owner_email", "num_employees",
]


def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    reader = PdfReader(pdf_path)
    for page in reader.pages:
        text += (page.extract_text() or "") + " "
    return text.strip()


def build_extraction_prompt(raw_text: str) -> str:
    return f'''You are a data extraction assistant for a sales operations tool.
Read the deal document below and extract structured fields from it.

Rules:
- Only extract information that is actually stated or clearly implied in the text.
- If a field is not mentioned, set it to null. Never invent or estimate values.
- Dates must be formatted as YYYY-MM-DD. If a date is relative (e.g. "3 weeks ago"),
  you may leave it null unless an absolute date is also given elsewhere in the text.
- amount and num_employees must be plain numbers (no currency symbols or commas).
- probability must be a number 0-100 if stated, otherwise null.
- Respond with ONLY valid JSON. No preamble, no markdown, no explanation.

=== DOCUMENT TEXT ===
{raw_text}
=== END DOCUMENT TEXT ===

Respond with ONLY this JSON structure:
{{
  "deal_name": "" ,
  "account_name": "",
  "stage": "",
  "amount": null,
  "probability": null,
  "close_date": null,
  "last_activity_date": null,
  "created_date": null,
  "lead_source": null,
  "next_step": null,
  "description": null,
  "owner_name": null,
  "owner_email": null,
  "num_employees": null
}}'''


def categorize_company_size(employees) -> str:
    if not employees or employees <= 0:
        return "Unknown"
    if employees < 100:
        return "SMB"
    if employees < 1000:
        return "Mid-Market"
    return "Enterprise"


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def normalize_deal(fields: dict, source_filename: str) -> dict:
    """
    Convert raw extracted fields into the normalized deal dict consumed by
    guardrails, scoring, and the report generator. Missing data gets safe,
    conservative defaults (e.g. unknown activity is treated as stale) rather
    than crashing the pipeline or silently pretending a deal is healthy.
    """
    today = datetime.now().date()

    last_activity = _parse_date(fields.get("last_activity_date"))
    created = _parse_date(fields.get("created_date"))
    close_date = _parse_date(fields.get("close_date"))

    days_since_activity = (today - last_activity).days if last_activity else 999
    days_since_created = (today - created).days if created else 0
    days_to_close = (close_date - today).days if close_date else None

    # No stage-change history is available from a freeform document, so we
    # approximate days-in-stage from days-since-created, same placeholder
    # approach the original spec used pending real CRM history.
    days_in_stage = days_since_created

    num_employees = fields.get("num_employees") or 0
    try:
        num_employees = int(num_employees)
    except (TypeError, ValueError):
        num_employees = 0

    amount = fields.get("amount") or 0
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        amount = 0.0

    probability = fields.get("probability")
    try:
        probability = float(probability) if probability is not None else 0.0
    except (TypeError, ValueError):
        probability = 0.0

    deal_id = os.path.splitext(source_filename)[0]

    low_confidence_extraction = not all([
        fields.get("stage"), fields.get("amount"), last_activity,
    ])

    deal = {
        "id": deal_id,
        "source_file": source_filename,
        "name": fields.get("deal_name") or deal_id,
        "account_name": fields.get("account_name") or "Unknown",
        "stage": fields.get("stage") or "Unknown",
        "amount": amount,
        "probability": probability,
        "close_date": str(close_date) if close_date else "Not set",
        "days_to_close": days_to_close,
        "days_since_activity": days_since_activity,
        "days_since_created": days_since_created,
        "days_in_stage": days_in_stage,
        "last_activity_date": str(last_activity) if last_activity else "Never",
        "lead_source": fields.get("lead_source") or "Unknown",
        "next_step": fields.get("next_step") or "Not specified",
        "description": fields.get("description") or "",
        "owner_name": fields.get("owner_name") or "Unknown",
        "owner_email": fields.get("owner_email") or "",
        "company_size": categorize_company_size(num_employees),
        "num_employees": num_employees,
        "low_confidence_extraction": low_confidence_extraction,
    }

    logger.info(
        f"Extracted deal '{deal['name']}' from {source_filename} "
        f"(low_confidence={low_confidence_extraction})"
    )
    return deal


def extract_deal_from_pdf(pdf_path: str) -> dict:
    """Full extraction pipeline: PDF -> raw text -> Claude fields -> normalized deal."""
    filename = os.path.basename(pdf_path)
    raw_text = extract_text_from_pdf(pdf_path)

    if not raw_text:
        raise ValueError(f"No extractable text found in {filename}")

    prompt = build_extraction_prompt(raw_text)

    try:
        fields = run_json_prompt(prompt)
    except (ClaudeCLIError, ValueError) as e:
        logger.error(f"Field extraction failed for {filename}: {e}")
        fields = {}

    return normalize_deal(fields, filename)
