import io
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, PageBreak)
from .drawing import item_drawing
from .settings_service import get_setting
from ..database import DATA_DIR

INK, STEEL, PAPER = colors.HexColor("#1B2430"), colors.HexColor("#2F5D7C"), colors.HexColor("#EEF1F3")


def money(v, cur):
    return f"{cur} {v:,.2f}"


def build_pdf(db, q) -> bytes:
    co = get_setting(db, "company")
    ss = getSampleStyleSheet()
    base = ParagraphStyle("b", parent=ss["Normal"], fontSize=9, leading=12, textColor=INK)
    small = ParagraphStyle("s", parent=base, fontSize=8, leading=10, textColor=colors.HexColor("#4B5865"))
    h = ParagraphStyle("h", parent=base, fontSize=11, leading=14, fontName="Helvetica-Bold", textColor=STEEL, spaceBefore=8, spaceAfter=3)
    title = ParagraphStyle("t", parent=base, fontSize=20, leading=24, fontName="Helvetica-Bold", alignment=2)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm, topMargin=14 * mm,
                            bottomMargin=16 * mm, title=f"Quotation {q.number}", author=co["name"])
    W = A4[0] - 32 * mm
    cur = q.currency
    story = []

    logo = None
    if co.get("logo") and (DATA_DIR / co["logo"]).exists():
        try:
            logo = Image(str(DATA_DIR / co["logo"]), width=34 * mm, height=34 * mm, kind="proportional")
        except Exception:
            logo = None
    head_left = [logo] if logo else []
    head_left.append(Paragraph(f"<b>{co['name']}</b><br/>{co['address'].replace(chr(10), '<br/>')}<br/>{co['phone']}  |  {co['email']}", base))
    head = Table([[head_left, [Paragraph("QUOTATION", title), Paragraph(f"<b>{q.number}</b>", ParagraphStyle("r", parent=base, alignment=2, fontSize=11)),
                               Paragraph(f"Date: {q.quote_date:%d %b %Y}<br/>Valid until: {q.expiry_date:%d %b %Y}" if q.expiry_date else f"Date: {q.quote_date:%d %b %Y}", ParagraphStyle("r2", parent=base, alignment=2))]]],
                 colWidths=[W * .55, W * .45])
    head.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, 0), 1.2, STEEL), ("BOTTOMPADDING", (0, 0), (-1, 0), 8)]))
    story += [head, Spacer(1, 6)]

    cust = f"<b>{q.customer_name}</b><br/>" + (f"{q.company}<br/>" if q.company else "") + \
           (f"{q.address.replace(chr(10), '<br/>')}<br/>" if q.address else "") + \
           " | ".join(x for x in (q.phone, q.email) if x)
    proj = "".join(f"<b>{k}:</b> {v}<br/>" for k, v in (("Project", q.project_name), ("Delivery", q.delivery_location), ("Status", q.status)) if v)
    info = Table([[Paragraph("<b>Quotation for</b><br/>" + cust, base), Paragraph(proj, base)]], colWidths=[W * .55, W * .45])
    info.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PAPER), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOX", (0, 0), (-1, -1), .4, colors.HexColor("#C9D1D8")), ("PADDING", (0, 0), (-1, -1), 6)]))
    story += [info, Spacer(1, 8)]

    for i, it in enumerate(q.items, 1):
        calc = it.calc
        dims = calc.get("dimensions", {})
        if it.kind == "aluminium":
            dtxt = f"{it.params['width']:g} x {it.params['height']:g} {it.params.get('unit', 'mm')}, {dims.get('panels')} panel(s), {dims.get('glass_thickness_mm')} mm glass"
        else:
            u = dims.get("unit", "mm")
            ov = it.params.get("overall", {})
            dtxt = f"W {ov.get('W')} x H {ov.get('H')} x D {ov.get('D')} {u}, {len(calc.get('components', []))} component types"
        # material breakdown shows quantities only (no internal cost / profit)
        mat_rows = [["Material", "Qty", "Unit"]]
        for l in calc["lines"]:
            if l["category"] != "wastage":
                mat_rows.append([f"{l['code']}  {l['description']}"[:70], f"{l['quantity']:,.2f}", l["unit"]])
        mt = Table(mat_rows, colWidths=[62 * mm, 18 * mm, 14 * mm], repeatRows=1)
        mt.setStyle(TableStyle([("FONTSIZE", (0, 0), (-1, -1), 7), ("BACKGROUND", (0, 0), (-1, 0), PAPER), ("TEXTCOLOR", (0, 0), (-1, -1), INK),
                                ("LINEBELOW", (0, 0), (-1, -1), .25, colors.HexColor("#D5DADF")), ("ALIGN", (1, 0), (1, -1), "RIGHT"), ("PADDING", (0, 0), (-1, -1), 2)]))
        block = Table([[item_drawing(it, 78 * mm, 60 * mm), mt]], colWidths=[82 * mm, W - 82 * mm])
        block.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("PADDING", (0, 0), (-1, -1), 0)]))
        price = Table([[Paragraph(f"<b>{i}. {it.name}</b><br/><font size=8 color='#4B5865'>{dtxt}</font>", base), f"{it.quantity}", money(it.unit_price, cur), money(it.total_price, cur)]],
                      colWidths=[W - 94 * mm, 14 * mm, 40 * mm, 40 * mm])
        price.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PAPER), ("ALIGN", (1, 0), (-1, -1), "RIGHT"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("FONTSIZE", (1, 0), (-1, -1), 9), ("PADDING", (0, 0), (-1, -1), 5)]))
        story.append(KeepTogether([price, Spacer(1, 3), block, Spacer(1, 8)]))

    if not q.items:
        story.append(Paragraph("No items have been added to this quotation yet.", base))

    tot = [["Subtotal", money(q.subtotal, cur)]]
    if q.discount_amount:
        lab = f"Discount ({q.discount_value:g}%)" if q.discount_mode == "percent" else "Discount"
        tot.append([lab, "- " + money(q.discount_amount, cur)])
    if q.tax_amount:
        tot.append([f"Tax ({q.tax_percent:g}%)", money(q.tax_amount, cur)])
    tot.append(["GRAND TOTAL", money(q.total, cur)])
    t = Table(tot, colWidths=[40 * mm, 48 * mm], hAlign="RIGHT")
    t.setStyle(TableStyle([("ALIGN", (1, 0), (1, -1), "RIGHT"), ("FONTSIZE", (0, 0), (-1, -1), 9), ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                           ("BACKGROUND", (0, -1), (-1, -1), STEEL), ("TEXTCOLOR", (0, -1), (-1, -1), colors.white), ("LINEBELOW", (0, 0), (-1, -2), .25, colors.HexColor("#D5DADF")), ("PADDING", (0, 0), (-1, -1), 5)]))
    story += [Spacer(1, 4), t]

    if q.notes:
        story += [Paragraph("Notes", h), Paragraph(q.notes.replace("\n", "<br/>"), base)]
    story += [Paragraph("Terms and conditions", h), Paragraph((q.terms or "").replace("\n", "<br/>"), small), Spacer(1, 26)]
    sig = Table([["", ""], ["Authorised signature", "Customer acceptance (signature / date)"]], colWidths=[W * .45, W * .45], rowHeights=[16 * mm, 6 * mm], hAlign="LEFT")
    sig.setStyle(TableStyle([("LINEABOVE", (0, 1), (0, 1), .6, INK), ("LINEABOVE", (1, 1), (1, 1), .6, INK), ("FONTSIZE", (0, 1), (-1, 1), 8)]))
    story.append(KeepTogether([sig]))

    def footer(c, d):
        c.saveState()
        c.setFont("Helvetica", 7.5)
        c.setFillColor(colors.HexColor("#6B7886"))
        c.drawString(16 * mm, 9 * mm, f"{co['name']}  -  {q.number}")
        c.drawRightString(A4[0] - 16 * mm, 9 * mm, f"Page {d.page}")
        c.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()
