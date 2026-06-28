# create_test_pdf.py
# Creates a test PDF with text, table, AND an image
# Image is generated programmatically — no download needed
# Run: uv run python create_test_pdf.py

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing
import io

doc    = SimpleDocTemplate("test_sample.pdf", pagesize=letter)
styles = getSampleStyleSheet()
story  = []

# ── Title ─────────────────────────────────────────────────────
story.append(Paragraph("DocuMind AI — Annual Report 2026", styles["Title"]))
story.append(Spacer(1, 0.2 * inch))

# ── Text paragraph 1 ──────────────────────────────────────────
story.append(Paragraph("Executive Summary", styles["Heading1"]))
story.append(Paragraph(
    "DocuMind AI delivered exceptional performance in fiscal year 2026. "
    "Revenue grew 23% year-over-year driven by strong adoption of our "
    "multi-modal RAG platform across enterprise customers in banking, "
    "healthcare, and legal sectors. Our hybrid retrieval system with "
    "cross-encoder reranking achieved state-of-the-art accuracy on "
    "internal benchmarks, outperforming competitors by 18 percentage points.",
    styles["Normal"]
))
story.append(Spacer(1, 0.2 * inch))

story.append(Paragraph(
    "The company expanded operations to 3 new markets including Singapore, "
    "Dubai, and London. Customer retention rate remained strong at 94% "
    "reflecting high satisfaction with our document intelligence platform. "
    "We onboarded 47 enterprise clients in Q4 alone, bringing total "
    "client count to 312 organizations worldwide.",
    styles["Normal"]
))
story.append(Spacer(1, 0.3 * inch))

# ── Bar chart image (generated with ReportLab) ────────────────
story.append(Paragraph("Revenue Performance Chart", styles["Heading1"]))
story.append(Spacer(1, 0.1 * inch))

# Create a bar chart using ReportLab's built-in chart tools
drawing = Drawing(400, 200)
chart   = VerticalBarChart()

chart.x          = 50
chart.y          = 30
chart.width      = 300
chart.height     = 150
chart.data       = [[12.4, 15.1, 18.6, 22.3]]
chart.categoryAxis.categoryNames = ["Q1", "Q2", "Q3", "Q4"]
chart.valueAxis.valueMin         = 0
chart.valueAxis.valueMax         = 25
chart.bars[0].fillColor          = colors.darkblue

# Add title text to the chart
drawing.add(chart)
drawing.add(String(
    200, 190,
    "Quarterly Revenue 2026 ($M)",
    textAnchor="middle",
    fontSize=12,
    fontName="Helvetica-Bold"
))

story.append(drawing)
story.append(Spacer(1, 0.1 * inch))
story.append(Paragraph(
    "Figure 1: Quarterly revenue performance showing consistent growth "
    "across all four quarters of fiscal year 2026. Q4 achieved the "
    "highest revenue at $22.3M representing 20% quarter-over-quarter growth.",
    styles["Normal"]
))
story.append(Spacer(1, 0.3 * inch))

# ── Table ─────────────────────────────────────────────────────
story.append(Paragraph("Quarterly Financial Results", styles["Heading1"]))
story.append(Spacer(1, 0.1 * inch))

data = [
    ["Quarter", "Revenue",  "Growth", "Clients"],
    ["Q1 2026", "$12.4M",   "+15%",   "218"],
    ["Q2 2026", "$15.1M",   "+22%",   "251"],
    ["Q3 2026", "$18.6M",   "+23%",   "289"],
    ["Q4 2026", "$22.3M",   "+20%",   "312"],
    ["Total",   "$68.4M",   "+20%",   "312"],
]

table = Table(data, colWidths=[1.2*inch, 1.2*inch, 1.0*inch, 1.0*inch])
table.setStyle(TableStyle([
    ("BACKGROUND",    (0, 0),  (-1, 0),  colors.darkblue),
    ("TEXTCOLOR",     (0, 0),  (-1, 0),  colors.whitesmoke),
    ("FONTNAME",      (0, 0),  (-1, 0),  "Helvetica-Bold"),
    ("BACKGROUND",    (0, -1), (-1, -1), colors.lightgrey),
    ("FONTNAME",      (0, -1), (-1, -1), "Helvetica-Bold"),
    ("GRID",          (0, 0),  (-1, -1), 1, colors.black),
    ("FONTSIZE",      (0, 0),  (-1, -1), 11),
    ("ALIGN",         (1, 0),  (-1, -1), "CENTER"),
    ("ROWBACKGROUNDS",(0, 1),  (-1, -2), [colors.white, colors.lightblue]),
]))

story.append(table)
story.append(Spacer(1, 0.3 * inch))

# ── Text paragraph 2 ──────────────────────────────────────────
story.append(Paragraph("Outlook for 2027", styles["Heading1"]))
story.append(Paragraph(
    "Management expects continued strong growth in 2027 with projected "
    "revenue of $95M representing 39% year-over-year growth. Key growth "
    "drivers include expansion of our LangGraph multi-agent platform, "
    "launch of the MCP server ecosystem, and penetration into the "
    "government and defence sectors across Asia Pacific regions.",
    styles["Normal"]
))

# ── Build PDF ─────────────────────────────────────────────────
doc.build(story)
print("✅ test_sample.pdf created with text + chart image + table!")