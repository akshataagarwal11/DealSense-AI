"""Assembles the 3-page DealSense AI risk report PDF using ReportLab + matplotlib charts."""
import logging
import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable, Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
    Table, TableStyle,
)

import config
from reports.charts import generate_gauge_chart, generate_risk_factor_chart

logger = logging.getLogger(__name__)

SCORE_COLORS = {
    "High": colors.HexColor("#C0392B"),
    "Medium": colors.HexColor("#D68910"),
    "Low": colors.HexColor("#1E7B34"),
}
NAVY = colors.HexColor("#1F3864")
ACCENT = colors.HexColor("#2E75B6")
LIGHT_GRAY = colors.HexColor("#F5F5F5")

SCORE_HEX = {"High": "#C0392B", "Medium": "#D68910", "Low": "#1E7B34"}

CONTENT_WIDTH = letter[0] - 2 * inch

styles = getSampleStyleSheet()
STYLE_TITLE = ParagraphStyle(
    "DSTitle", parent=styles["Title"], textColor=NAVY, fontSize=20, spaceAfter=4,
)
STYLE_SUBTITLE = ParagraphStyle(
    "DSSubtitle", parent=styles["Normal"], textColor=colors.HexColor("#666666"),
    fontSize=9, spaceAfter=14,
)
STYLE_H2 = ParagraphStyle(
    "DSH2", parent=styles["Heading2"], textColor=NAVY, fontSize=14,
    spaceBefore=10, spaceAfter=8,
)
STYLE_BODY = ParagraphStyle("DSBody", parent=styles["Normal"], fontSize=10, leading=14)
STYLE_SMALL = ParagraphStyle(
    "DSSmall", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#888888"),
)


def _score_color(score: str):
    return SCORE_COLORS.get(score, NAVY)


def _header_flowables(score_result: dict) -> list:
    flow = [
        Paragraph("DealSense AI", STYLE_TITLE),
        Paragraph(
            f"Deal Risk Report &nbsp;&middot;&nbsp; Generated "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M')} &nbsp;&middot;&nbsp; "
            f"Policy v{score_result.get('policy_version', config.POLICY_VERSION)}",
            STYLE_SUBTITLE,
        ),
        HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=14),
    ]
    return flow


def _deal_overview_table(deal: dict) -> Table:
    rows = [
        ["Deal Name", deal.get("name", "Unknown"), "Owner", deal.get("owner_name", "Unknown")],
        ["Account", deal.get("account_name", "Unknown"), "Stage", deal.get("stage", "Unknown")],
        ["Deal Value", f"${deal.get('amount', 0):,.0f}", "Close Date", deal.get("close_date", "Not set")],
        ["Company Size", deal.get("company_size", "Unknown"), "Last Activity", deal.get("last_activity_date", "Never")],
    ]
    col_w = CONTENT_WIDTH / 4
    table = Table(rows, colWidths=[col_w * 0.8, col_w * 1.2, col_w * 0.8, col_w * 1.2])
    table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#888888")),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#888888")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#E0E0E0")),
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
        ("LEFTPADDING", (0, 0), (0, -1), 10),
        ("RIGHTPADDING", (-1, 0), (-1, -1), 10),
    ]))
    return table


def _score_badge(score_result: dict) -> Table:
    score = score_result["final_score"]
    confidence = score_result["confidence"]
    badge = Table(
        [[Paragraph(f"<b>{score.upper()} RISK</b>", ParagraphStyle(
            "Badge", fontSize=16, textColor=colors.white, alignment=TA_CENTER))]],
        colWidths=[2.2 * inch],
    )
    badge.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _score_color(score)),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    return badge


def _flags_paragraphs(flags: list) -> list:
    flow = []
    for flag in flags:
        color = "#C0392B" if flag.startswith("CRITICAL") else (
            "#D68910" if flag.startswith("WARNING") or flag.startswith("ESCALATION") else "#1E7B34"
        )
        flow.append(Paragraph(f'<font color="{color}">&#9679;</font> {flag}', STYLE_BODY))
        flow.append(Spacer(1, 4))
    return flow or [Paragraph("None", STYLE_BODY)]


def _build_page_1(score_result: dict, deal: dict, temp_paths: list) -> list:
    story = _header_flowables(score_result)
    story.append(Paragraph("Deal Overview", STYLE_H2))
    story.append(_deal_overview_table(deal))
    story.append(Spacer(1, 16))

    gauge_path = os.path.join(config.OUTPUTS_PATH, f"temp_gauge_{deal['id']}.png")
    generate_gauge_chart(score_result["final_score"], score_result["confidence"], gauge_path)
    temp_paths.append(gauge_path)

    top_row = Table(
        [[_score_badge(score_result), Image(gauge_path, width=2.6 * inch, height=1.7 * inch)]],
        colWidths=[2.6 * inch, CONTENT_WIDTH - 2.6 * inch],
    )
    top_row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.append(top_row)
    story.append(Spacer(1, 16))

    story.append(Paragraph("Top Flags", STYLE_H2))
    top_flags = score_result.get("guardrail_flags", [])[:3]
    story.extend(_flags_paragraphs(top_flags))

    if score_result.get("low_confidence_extraction"):
        story.append(Spacer(1, 8))
        story.append(Paragraph(
            '<font color="#D68910">&#9888; Some deal fields could not be confidently '
            "extracted from the source document. This score should be verified against "
            "the original deal record.</font>", STYLE_BODY,
        ))

    return story


def _build_page_2(score_result: dict, deal: dict, temp_paths: list) -> list:
    story = [Paragraph("Risk Factors", STYLE_H2)]

    risk_factors = score_result.get("risk_factors", [])
    if risk_factors:
        chart_path = os.path.join(config.OUTPUTS_PATH, f"temp_factors_{deal['id']}.png")
        generate_risk_factor_chart(risk_factors, chart_path)
        temp_paths.append(chart_path)
        story.append(Image(chart_path, width=CONTENT_WIDTH, height=1.8 * inch))
        story.append(Spacer(1, 12))

    for rf in risk_factors:
        hex_color = SCORE_HEX.get(rf["severity"], "#000000")
        story.append(Paragraph(
            f'<font color="{hex_color}"><b>[{rf["severity"].upper()}]</b></font> '
            f'<b>{rf["factor"]}</b>', STYLE_BODY,
        ))
        story.append(Paragraph(rf["explanation"], STYLE_BODY))
        story.append(Spacer(1, 8))

    story.append(Paragraph("Guardrail Flags", STYLE_H2))
    story.extend(_flags_paragraphs(score_result.get("guardrail_flags", [])))
    return story


def _build_page_3(score_result: dict, deal: dict) -> list:
    story = [Paragraph("Recommended Actions", STYLE_H2)]

    for action in score_result.get("recommended_actions", []):
        card = Table(
            [[Paragraph(
                f'<b>{action["action"]}</b><br/>'
                f'<font color="#666666">Timeline: {action["timeline"]} &nbsp;&middot;&nbsp; '
                f'Owner: {action["owner"]}</font>', STYLE_BODY,
            )]],
            colWidths=[CONTENT_WIDTH],
        )
        card.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(card)
        story.append(Spacer(1, 8))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Full Narrative", STYLE_H2))
    for para in score_result.get("narrative_summary", "").split("\n"):
        if para.strip():
            story.append(Paragraph(para.strip(), STYLE_BODY))
            story.append(Spacer(1, 6))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Policy References", STYLE_H2))
    refs = score_result.get("policy_references", [])
    if refs:
        for ref in refs:
            story.append(Paragraph(f"&#8226; {ref}", STYLE_BODY))
    else:
        story.append(Paragraph("None cited.", STYLE_BODY))

    story.append(Spacer(1, 24))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#DDDDDD")))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} &nbsp;&middot;&nbsp; "
        f"Policy v{score_result.get('policy_version', config.POLICY_VERSION)} "
        f"&nbsp;&middot;&nbsp; Deal ID: {score_result.get('deal_id', 'Unknown')}",
        STYLE_SMALL,
    ))
    return story


def generate_pdf_report(score_result: dict, deal: dict, output_path: str) -> str:
    """Build the full 3-page PDF report and save it to output_path."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    doc = SimpleDocTemplate(
        output_path, pagesize=letter,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch,
        leftMargin=1 * inch, rightMargin=1 * inch,
    )

    temp_paths = []
    story = []
    story.extend(_build_page_1(score_result, deal, temp_paths))
    story.append(PageBreak())
    story.extend(_build_page_2(score_result, deal, temp_paths))
    story.append(PageBreak())
    story.extend(_build_page_3(score_result, deal))

    doc.build(story)
    cleanup_temp_charts(temp_paths)

    logger.info(f"Generated PDF report: {output_path}")
    return output_path


def cleanup_temp_charts(file_paths: list):
    """Delete temp chart PNG files after the PDF has been generated."""
    for path in file_paths:
        try:
            os.remove(path)
        except OSError:
            pass
