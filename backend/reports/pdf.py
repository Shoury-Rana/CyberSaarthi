from __future__ import annotations

import html
import io
import os
from urllib.parse import quote
from django.core.signing import BadSignature, TimestampSigner
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from submissions.models import ScamSubmission

# Attempt to register standard Windows Unicode font; fallback to Helvetica safely
FONT_NAME = "Helvetica"
FONT_BOLD = "Helvetica-Bold"

for name, path in [
    ("Arial", "C:\\Windows\\Fonts\\arial.ttf"),
    ("Nirmala", "C:\\Windows\\Fonts\\Nirmala.ttf"),
    ("DejaVuSans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
]:
    if os.path.exists(path):
        try:
            pdfmetrics.registerFont(TTFont(name, path))
            FONT_NAME = name
            FONT_BOLD = name
            break
        except Exception:
            pass


def _defang(text: str) -> str:
    return text.replace("http", "hxxp").replace(".", "[.]")


def _safe_pdf_text(text: str) -> str:
    """Escapes XML entities and handles character sets safely for ReportLab."""
    if not text:
        return ""
    if FONT_NAME == "Helvetica":
        text = text.encode("latin-1", errors="replace").decode("latin-1")
    return html.escape(text)


def generate_pdf(scan_id: str) -> bytes:
    """Generate official Cyber Fraud Evidence Dossier via ReportLab."""
    submission = ScamSubmission.objects.get(id=scan_id)
    assessment = getattr(submission, "assessment", None)
    indicators = list(submission.indicators.all())

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DossierTitle",
        parent=styles["Heading1"],
        fontName=FONT_BOLD,
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#1e3a8a"),
    )
    h2_style = ParagraphStyle(
        "DossierH2",
        parent=styles["Heading2"],
        fontName=FONT_BOLD,
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=8,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "DossierBody",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#334155"),
    )
    alert_style = ParagraphStyle(
        "DossierAlert",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#b91c1c"),
    )

    story = []

    story.append(Paragraph("Cyber Fraud Evidence &amp; Complaint Preparation Dossier", title_style))
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "<b>Notice:</b> This document is an investigative preparation aid intended for submission "
            "at the National Cyber Crime Reporting Portal (<b>cybercrime.gov.in</b>).",
            body_style,
        )
    )
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563eb"), spaceAfter=8))

    if submission.reported_financial_loss:
        alert_data = [
            [
                Paragraph(
                    "<b>FINANCIAL LOSS REPORTED: IMMEDIATE ACTION REQUIRED</b><br/>"
                    "Call the National Cybercrime Helpline immediately: <b>1930</b>. "
                    "Contact your bank immediately to freeze involved accounts.",
                    alert_style,
                )
            ]
        ]
        t_alert = Table(alert_data, colWidths=[540])
        t_alert.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fee2e2")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#ef4444")),
                    ("PADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(t_alert)
        story.append(Spacer(1, 8))

    meta_data = [
        [
            Paragraph(f"<b>Scan ID:</b> {_safe_pdf_text(str(submission.id))}", body_style),
            Paragraph(f"<b>Date:</b> {submission.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}", body_style),
        ],
        [
            Paragraph(f"<b>Channel:</b> {_safe_pdf_text(submission.channel.upper())}", body_style),
            Paragraph(f"<b>Classification:</b> {_safe_pdf_text(assessment.classification if assessment else 'N/A')}", body_style),
        ],
    ]
    t_meta = Table(meta_data, colWidths=[270, 270])
    t_meta.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(t_meta)

    story.append(Paragraph("1. Suspicious Content (Submitted Message / Text)", h2_style))
    safe_content = _safe_pdf_text(submission.raw_content or "[No raw content preserved]").replace("\n", "<br/>")
    story.append(Paragraph(safe_content[:1500], body_style))

    story.append(Paragraph("2. Extracted Indicators (Defanged for Safety)", h2_style))
    if indicators:
        ind_data = [["Indicator Type", "Defanged Representation"]]
        for ind in indicators:
            ind_data.append([ind.indicator_type, _defang(_safe_pdf_text(ind.normalised_value))])
        t_ind = Table(ind_data, colWidths=[120, 420])
        t_ind.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                    ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("PADDING", (0, 0), (-1, -1), 4),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(t_ind)
    else:
        story.append(Paragraph("No structural URLs, Phone numbers or UPI IDs detected.", body_style))

    story.append(Paragraph("3. Heuristic Rules &amp; Triggered Signals", h2_style))
    if assessment and assessment.rule_ids:
        story.append(Paragraph(f"<b>Triggered Heuristics:</b> {', '.join(assessment.rule_ids)}", body_style))
        story.append(Paragraph(f"<b>Ruleset Version:</b> {assessment.ruleset_version} | <b>Confidence:</b> {assessment.confidence}", body_style))
    else:
        story.append(Paragraph("No automated fraud heuristics triggered.", body_style))

    story.append(Paragraph("4. Citizen Filing Checklist (Official Guidance)", h2_style))
    checklist_text = (
        "• Take complete screenshots of the SMS / WhatsApp message with sender IDs visible.<br/>"
        "• If financial transaction occurred, note down Bank UTR Number and Transaction Reference ID.<br/>"
        "• Keep the cybercrime acknowledgement number safe after filing at <b>cybercrime.gov.in</b>."
    )
    story.append(Paragraph(checklist_text, body_style))

    doc.build(story)
    return buffer.getvalue()


def signed_url(scan_id: str, max_age: int = 900) -> dict:
    signer = TimestampSigner(salt="report")
    token = signer.sign_object({"scan_id": str(scan_id)})
    return {
        "url": f"/api/v1/scans/{scan_id}/report.pdf?token={quote(token)}",
        "expires_in": max_age,
    }


def verify_token(token: str, scan_id: str, max_age: int = 900) -> bool:
    try:
        signer = TimestampSigner(salt="report")
        data = signer.unsign_object(token, max_age=max_age)
        return str(data.get("scan_id")) == str(scan_id)
    except BadSignature:
        return False