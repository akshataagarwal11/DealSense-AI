"""
DealSense AI — main pipeline orchestrator.

Watches inbox/ for freeform deal PDFs and, for each one, extracts deal
fields via Claude, runs the guardrails + RAG + Claude scoring pipeline,
generates a 3-page PDF report to outputs/, logs what email would be sent,
and moves the source PDF to processed/ only once the whole thing succeeds.
"""
import logging
import os
from datetime import datetime

import config
from input.extractor import extract_deal_from_pdf
from input.watcher import find_new_pdfs, move_to_processed
from knowledge_base.ingest import ingest_all_documents
from reports.email_sender import send_risk_report_email
from reports.pdf_generator import generate_pdf_report
from scoring.scorer import score_deal

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
)
logger = logging.getLogger(__name__)


def run_pipeline(ingest: bool = False, manager_email: str = None) -> list:
    """
    Full DealSense AI pipeline.

    Args:
        ingest: If True, re-ingest knowledge base documents before scoring.
                Set True on first run and whenever the policy docs change.
        manager_email: CC address for High Risk deals and escalations.
    """
    logger.info("=== DealSense AI Pipeline Starting ===")

    os.makedirs(config.OUTPUTS_PATH, exist_ok=True)
    os.makedirs(config.INBOX_PATH, exist_ok=True)
    os.makedirs(config.PROCESSED_PATH, exist_ok=True)

    if ingest:
        logger.info("Ingesting knowledge base documents...")
        ingest_all_documents()

    pdf_paths = find_new_pdfs()
    logger.info(f"Processing {len(pdf_paths)} deal PDF(s)")

    results = []

    for pdf_path in pdf_paths:
        filename = os.path.basename(pdf_path)
        try:
            # 1. Extract deal fields from the PDF
            deal = extract_deal_from_pdf(pdf_path)

            # 2. Score (RAG + guardrails + Claude)
            score_result = score_deal(deal)

            # 3. Generate PDF report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = deal["name"].replace(" ", "_")[:40]
            pdf_filename = f"DealSense_{safe_name}_{timestamp}.pdf"
            report_path = os.path.join(config.OUTPUTS_PATH, pdf_filename)
            generate_pdf_report(score_result, deal, report_path)

            # 4. Email (stubbed — logs only for now)
            email_sent = send_risk_report_email(score_result, report_path, manager_email)

            # 5. Only move the source PDF once everything above succeeded
            move_to_processed(pdf_path)

            results.append({
                "deal": deal["name"],
                "source_file": filename,
                "score": score_result["final_score"],
                "confidence": score_result["confidence"],
                "needs_human_review": score_result.get("needs_human_review", False),
                "email_logged": email_sent,
                "report": pdf_filename,
            })
        except Exception as e:
            logger.error(f"Pipeline failed for {filename}: {e}", exc_info=True)
            continue

    high = sum(1 for r in results if r["score"] == "High")
    medium = sum(1 for r in results if r["score"] == "Medium")
    low = sum(1 for r in results if r["score"] == "Low")

    logger.info("=== Pipeline Complete ===")
    logger.info(
        f"Results: {len(results)} scored | High: {high} | Medium: {medium} | Low: {low}"
    )
    return results


if __name__ == "__main__":
    run_pipeline(
        ingest=True,        # Set False after the first run to skip re-ingestion
        manager_email=None,  # Add a manager email here to CC on High Risk / escalations
    )
