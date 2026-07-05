import os
from dotenv import load_dotenv

load_dotenv()

# -----------------------------
# Claude (via Claude Code CLI — no API key needed)
# -----------------------------
CLAUDE_CLI_PATH = os.getenv("CLAUDE_CLI_PATH", "claude")
CLAUDE_CLI_TIMEOUT = int(os.getenv("CLAUDE_CLI_TIMEOUT", "180"))

# -----------------------------
# Paths
# -----------------------------
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
KNOWLEDGE_BASE_PATH = os.getenv(
    "KNOWLEDGE_BASE_PATH",
    "./knowledge_base/documents"
)
INBOX_PATH = os.getenv("INBOX_PATH", "./inbox")
PROCESSED_PATH = os.getenv("PROCESSED_PATH", "./processed")
OUTPUTS_PATH = os.getenv("OUTPUTS_PATH", "./outputs")
POLICY_VERSION = os.getenv("POLICY_VERSION", "1.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# -----------------------------
# Email (stubbed — no provider wired up yet)
# -----------------------------
EMAIL_FROM = os.getenv("EMAIL_FROM", "dealsense@example.com")
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "DealSense AI")

# -----------------------------
# Guardrail Thresholds
# -----------------------------
GUARDRAIL_HIGH_RISK_DAYS_IN_STAGE = 45
GUARDRAIL_HIGH_RISK_DAYS_NO_ACTIVITY = 21
GUARDRAIL_AMOUNT_DROP_PCT = -20
GUARDRAIL_ENTERPRISE_REVIEW_THRESHOLD = 500000
GUARDRAIL_LOW_RISK_RECENT_ACTIVITY_DAYS = 3
