"""Professional certificate PDF template using ReportLab.

This module defines the visual layout for the certificate.
It uses ReportLab's canvas drawing API to create a clean,
professional-looking certificate with borders, text, and decorations.
"""

from datetime import date

from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch, cm
from reportlab.pdfgen.canvas import Canvas


# ── Colour palette ──────────────────────────────────────────────
NAVY = HexColor("#1B2A4A")
GOLD = HexColor("#C9A84C")
DARK_GRAY = HexColor("#333333")
MEDIUM_GRAY = HexColor("#666666")
LIGHT_GRAY = HexColor("#999999")
BORDER_GOLD = HexColor("#B8941F")


def draw_certificate(
    canvas: Canvas,
    *,
    organization_name: str,
    certificate_title: str,
    recipient_name: str,
    event_name: str,
    issue_date: date,
    certificate_id: str,
) -> None:
    """Draw a single-page professional certificate onto the given canvas.

    Args:
        canvas: ReportLab Canvas object (landscape A4).
        organization_name: Issuing organization.
        certificate_title: e.g. "Certificate of Participation".
        recipient_name: Full name of the recipient.
        event_name: Event or course name.
        issue_date: Date the certificate is issued.
        certificate_id: Unique ID printed at the bottom.
    """
    width, height = landscape(A4)
    mid_x = width / 2

    # ── Outer border ────────────────────────────────────────────
    canvas.setStrokeColor(BORDER_GOLD)
    canvas.setLineWidth(3)
    margin = 0.5 * inch
    canvas.rect(margin, margin, width - 2 * margin, height - 2 * margin)

    # Inner decorative border
    canvas.setLineWidth(1)
    inner = 0.7 * inch
    canvas.rect(inner, inner, width - 2 * inner, height - 2 * inner)

    # ── Corner ornaments ────────────────────────────────────────
    ornament_size = 0.25 * inch
    ornament_offset = 0.6 * inch
    canvas.setFillColor(GOLD)
    for x in [ornament_offset, width - ornament_offset]:
        for y in [ornament_offset, height - ornament_offset]:
            canvas.circle(x, y, ornament_size / 2, fill=1, stroke=0)

    # ── Organisation name ───────────────────────────────────────
    canvas.setFont("Helvetica-Bold", 16)
    canvas.setFillColor(NAVY)
    canvas.drawCentredString(mid_x, height - 1.5 * inch, organization_name.upper())

    # ── Decorative gold line ────────────────────────────────────
    line_y = height - 1.75 * inch
    line_w = 3 * inch
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(2)
    canvas.line(mid_x - line_w / 2, line_y, mid_x + line_w / 2, line_y)

    # ── Certificate title ───────────────────────────────────────
    canvas.setFont("Helvetica-Bold", 32)
    canvas.setFillColor(NAVY)
    canvas.drawCentredString(mid_x, height - 2.4 * inch, certificate_title)

    # ── "This is proudly presented to" ──────────────────────────
    canvas.setFont("Helvetica", 13)
    canvas.setFillColor(MEDIUM_GRAY)
    canvas.drawCentredString(mid_x, height - 3.0 * inch, "This is proudly presented to")

    # ── Recipient name ──────────────────────────────────────────
    canvas.setFont("Helvetica-Bold", 28)
    canvas.setFillColor(NAVY)
    canvas.drawCentredString(mid_x, height - 3.6 * inch, recipient_name)

    # Underline beneath recipient name
    name_width = canvas.stringWidth(recipient_name, "Helvetica-Bold", 28)
    underline_y = height - 3.7 * inch
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(1.5)
    canvas.line(
        mid_x - name_width / 2 - 0.3 * inch,
        underline_y,
        mid_x + name_width / 2 + 0.3 * inch,
        underline_y,
    )

    # ── Event / course description ──────────────────────────────
    canvas.setFont("Helvetica", 13)
    canvas.setFillColor(DARK_GRAY)
    canvas.drawCentredString(
        mid_x,
        height - 4.2 * inch,
        f"for the successful completion of",
    )
    canvas.setFont("Helvetica-Bold", 16)
    canvas.setFillColor(NAVY)
    canvas.drawCentredString(mid_x, height - 4.55 * inch, event_name)

    # ── Issue date ──────────────────────────────────────────────
    formatted_date = issue_date.strftime("%B %d, %Y")
    canvas.setFont("Helvetica", 12)
    canvas.setFillColor(MEDIUM_GRAY)
    canvas.drawCentredString(mid_x, height - 5.1 * inch, f"Issued on {formatted_date}")

    # ── Signature area ──────────────────────────────────────────
    sig_y = 1.4 * inch
    sig_line_width = 2.5 * inch

    # Left: authorized signature
    left_x = width * 0.3
    canvas.setStrokeColor(DARK_GRAY)
    canvas.setLineWidth(1)
    canvas.line(left_x - sig_line_width / 2, sig_y, left_x + sig_line_width / 2, sig_y)
    canvas.setFont("Helvetica", 10)
    canvas.setFillColor(MEDIUM_GRAY)
    canvas.drawCentredString(left_x, sig_y - 0.2 * inch, "Authorized Signature")

    # Right: date
    right_x = width * 0.7
    canvas.line(right_x - sig_line_width / 2, sig_y, right_x + sig_line_width / 2, sig_y)
    canvas.drawCentredString(right_x, sig_y - 0.2 * inch, "Date")

    # ── Certificate ID ──────────────────────────────────────────
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(LIGHT_GRAY)
    canvas.drawCentredString(mid_x, 0.65 * inch, f"Certificate ID: {certificate_id}")
