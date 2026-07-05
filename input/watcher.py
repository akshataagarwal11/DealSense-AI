"""
Scans the inbox/ folder for deal PDFs that haven't been processed yet.

Any .pdf still sitting in inbox/ is considered unprocessed — main.py moves
a file to processed/ only after the full pipeline succeeds for it, so a
mid-run failure simply leaves the file in place to retry on the next run.
"""
import logging
import os
import shutil

import config

logger = logging.getLogger(__name__)


def find_new_pdfs() -> list[str]:
    """Return sorted absolute paths of all PDFs waiting in the inbox."""
    os.makedirs(config.INBOX_PATH, exist_ok=True)

    pdfs = sorted(
        os.path.join(config.INBOX_PATH, f)
        for f in os.listdir(config.INBOX_PATH)
        if f.lower().endswith(".pdf")
    )

    logger.info(f"Found {len(pdfs)} deal PDF(s) waiting in inbox")
    return pdfs


def move_to_processed(pdf_path: str) -> str:
    """Move a successfully processed PDF out of the inbox."""
    os.makedirs(config.PROCESSED_PATH, exist_ok=True)

    filename = os.path.basename(pdf_path)
    dest = os.path.join(config.PROCESSED_PATH, filename)

    # Avoid clobbering an existing file of the same name in processed/
    if os.path.exists(dest):
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(dest):
            dest = os.path.join(config.PROCESSED_PATH, f"{base}_{counter}{ext}")
            counter += 1

    shutil.move(pdf_path, dest)
    logger.info(f"Moved {filename} to processed/")
    return dest
