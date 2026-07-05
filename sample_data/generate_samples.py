"""
Generates 10 fictional freeform deal-brief PDFs into sample_data/deals/ for
end-to-end testing of the DealSense AI pipeline (extraction -> guardrails ->
scoring -> report) without needing a real CRM export.

Each brief is prose, not a key:value template, so it exercises the same
freeform extraction path a real deal document would. Dates are computed
relative to today so the guardrail math (days since activity, etc.) lines
up with the intended scenario for each deal.

Run: python sample_data/generate_samples.py
"""
import os
from datetime import date, timedelta

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

TODAY = date.today()
OUT_DIR = os.path.join(os.path.dirname(__file__), "deals")

styles = getSampleStyleSheet()
STYLE_TITLE = ParagraphStyle("Title2", parent=styles["Title"], fontSize=16)
STYLE_BODY = ParagraphStyle("Body2", parent=styles["Normal"], fontSize=11, leading=16, spaceAfter=10)


def d(days_ago: int) -> str:
    return (TODAY - timedelta(days=days_ago)).strftime("%B %-d, %Y")


DEALS = [
    dict(
        filename="acme_corp_enterprise_suite.pdf",
        title="Deal Brief: Acme Corp - Enterprise Suite",
        body=f"""Account: Acme Corporation (Enterprise, ~3,200 employees)<br/>
Deal owner: Jane Smith (jane.smith@example.com)<br/>
Stage: Proposal<br/>
Deal value: $280,000<br/>
Win probability: 55%<br/>
Expected close date: {d(-25)}<br/>
Lead source: Website<br/><br/>

We opened this opportunity around {d(50)} after Acme's procurement team reached out
about replacing their legacy platform. Things moved quickly through discovery, but
the deal has been sitting in Proposal since early June with no meaningful movement.
Our last real conversation with the buying team was on {d(23)}, when we sent over
the updated pricing sheet. Several follow-up emails since then have gone unanswered.
Next step: schedule a pricing review call with procurement, though no date has been
confirmed yet.""",
    ),
    dict(
        filename="techstart_inc_starter_plan.pdf",
        title="Deal Brief: TechStart Inc - Starter Plan",
        body=f"""Account: TechStart Inc (SMB, 35 employees)<br/>
Deal owner: Marcus Lee (marcus.lee@example.com)<br/>
Stage: Negotiation<br/>
Deal value: $15,000<br/>
Win probability: 80%<br/>
Expected close date: {d(-10)}<br/>
Lead source: Referral<br/><br/>

TechStart has been a dream deal from the start &mdash; fast decision cycle, engaged
founder, and clear budget. We had a great call with their CEO on {d(2)} where they
confirmed they're ready to sign as soon as legal finishes reviewing the contract
redlines. Next step: send final redlined contract for signature this week.""",
    ),
    dict(
        filename="global_systems_platform.pdf",
        title="Deal Brief: Global Systems - Platform",
        body=f"""Account: Global Systems (Mid-Market, ~450 employees)<br/>
Deal owner: Priya Nair (priya.nair@example.com)<br/>
Stage: Qualification<br/>
Deal value: $95,000<br/>
Win probability: 25%<br/>
Expected close date: {d(-40)}<br/>
Lead source: Outbound<br/><br/>

This opportunity was created about {d(70)} after an initial outbound conversation
at a trade show. Unfortunately, we've been unable to get the champion back on the
phone since our discovery call on {d(67)}. Multiple emails and voicemails have gone
unanswered. Next step: not specified &mdash; we honestly aren't sure who to reach out
to next since our original contact went quiet.""",
    ),
    dict(
        filename="bright_solutions_analytics.pdf",
        title="Deal Brief: Bright Solutions - Analytics",
        body=f"""Account: Bright Solutions (SMB, 60 employees)<br/>
Deal owner: Marcus Lee (marcus.lee@example.com)<br/>
Stage: Closing<br/>
Deal value: $45,000<br/>
Win probability: 90%<br/>
Expected close date: {d(-5)}<br/>
Lead source: Website<br/><br/>

Bright Solutions is about as healthy as deals get. We finished their POC last month
and the buying committee is fully aligned. Our champion messaged us just yesterday
({d(1)}) confirming the paperwork is with their finance team for final sign-off.
Next step: confirm PO number and get the signed order form back.""",
    ),
    dict(
        filename="meridian_bank_security.pdf",
        title="Deal Brief: Meridian Bank - Security",
        body=f"""Account: Meridian Bank (Enterprise, ~8,000 employees)<br/>
Deal owner: Jane Smith (jane.smith@example.com)<br/>
Stage: Proposal<br/>
Deal value: $620,000<br/>
Win probability: 60%<br/>
Expected close date: {d(-45)}<br/>
Lead source: Partner referral<br/><br/>

This is our largest active opportunity this quarter. Meridian's security and
compliance teams have been engaged since we opened the deal about {d(25)}. Our last
substantive touchpoint with their VP of Infrastructure was on {d(15)}, when we
walked through the proposed architecture. Given the size of this deal, it's already
been flagged internally for extra oversight. Next step: schedule a security review
session with Meridian's InfoSec team.""",
    ),
    dict(
        filename="nova_health_compliance.pdf",
        title="Deal Brief: Nova Health - Compliance",
        body=f"""Account: Nova Health (Mid-Market, ~600 employees)<br/>
Deal owner: Priya Nair (priya.nair@example.com)<br/>
Stage: Prospecting<br/>
Deal value: $38,000<br/>
Win probability: 15%<br/>
Expected close date: {d(-60)}<br/>
Lead source: Inbound<br/><br/>

Nova Health downloaded one of our compliance whitepapers about {d(30)} and briefly
engaged with our SDR team, but the conversation has gone completely cold since our
one and only call on {d(30)}. We haven't been able to get anyone on the phone since.
Next step: not specified.""",
    ),
    dict(
        filename="apex_retail_commerce.pdf",
        title="Deal Brief: Apex Retail - Commerce",
        body=f"""Account: Apex Retail (Mid-Market, ~300 employees)<br/>
Deal owner: Marcus Lee (marcus.lee@example.com)<br/>
Stage: Negotiation<br/>
Deal value: $72,000<br/>
Win probability: 65%<br/>
Expected close date: {d(-20)}<br/>
Lead source: Website<br/><br/>

Apex Retail's e-commerce team has been engaged and responsive throughout this deal,
which we opened about {d(35)}. We're currently working through contract terms with
their legal team; our last exchange with them was on {d(5)}, discussing a data
processing addendum. Next step: finalize DPA language with Apex legal and
re-circulate the contract.""",
    ),
    dict(
        filename="summit_energy_operations.pdf",
        title="Deal Brief: Summit Energy - Operations",
        body=f"""Account: Summit Energy (Enterprise, ~2,100 employees)<br/>
Deal owner: Jane Smith (jane.smith@example.com)<br/>
Stage: Proposal<br/>
Deal value: $155,000<br/>
Win probability: 45%<br/>
Expected close date: {d(-30)}<br/>
Lead source: Outbound<br/><br/>

Summit Energy's operations team requested a formal proposal after a strong initial
discovery process; the opportunity was opened about {d(40)}. We sent over the
proposal and had a good working session with their ops director on {d(8)}. Next
step: incorporate their feedback into a revised proposal and schedule a follow-up
review.""",
    ),
    dict(
        filename="cedar_labs_developer.pdf",
        title="Deal Brief: Cedar Labs - Developer",
        body=f"""Account: Cedar Labs (SMB, 22 employees)<br/>
Deal owner: Marcus Lee (marcus.lee@example.com)<br/>
Stage: Qualification<br/>
Deal value: $22,000<br/>
Win probability: 40%<br/>
Expected close date: {d(-28)}<br/>
Lead source: Referral<br/><br/>

Cedar Labs' engineering lead reached out after a colleague's recommendation, and
we opened this opportunity about {d(20)}. We had a solid technical discovery call
on {d(12)} covering their integration requirements. Next step: send a technical
scoping document and schedule a follow-up with their broader engineering team.""",
    ),
    dict(
        filename="ironclad_manufacturing_erp.pdf",
        title="Deal Brief: Ironclad Manufacturing - ERP",
        body=f"""Account: Ironclad Manufacturing (Enterprise, ~5,400 employees)<br/>
Deal owner: Priya Nair (priya.nair@example.com)<br/>
Stage: Closing<br/>
Deal value: $410,000<br/>
Win probability: 50%<br/>
Expected close date: {d(-10)}<br/>
Lead source: Partner referral<br/><br/>

This ERP replacement deal looked extremely promising when we entered Closing about
{d(50)} after a strong evaluation process. Since then, though, things have gone
quiet &mdash; our last real contact with Ironclad's steering committee was on
{d(45)}, right after they said they needed "a bit more time" to finalize budget
approval. We haven't heard back since despite several check-in attempts. Next
step: not specified.""",
    ),
]


def build_pdf(deal: dict, path: str):
    doc = SimpleDocTemplate(path, pagesize=letter,
                             topMargin=1 * inch, bottomMargin=1 * inch,
                             leftMargin=1 * inch, rightMargin=1 * inch)
    story = [
        Paragraph(deal["title"], STYLE_TITLE),
        Spacer(1, 16),
        Paragraph(deal["body"], STYLE_BODY),
    ]
    doc.build(story)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for deal in DEALS:
        path = os.path.join(OUT_DIR, deal["filename"])
        build_pdf(deal, path)
        print(f"Generated {path}")


if __name__ == "__main__":
    main()
