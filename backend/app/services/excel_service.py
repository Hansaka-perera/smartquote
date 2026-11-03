import io
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

HEAD = PatternFill("solid", fgColor="2F5D7C")


def _hdr(ws, row, vals):
    for i, v in enumerate(vals, 1):
        c = ws.cell(row=row, column=i, value=v)
        c.font, c.fill = Font(bold=True, color="FFFFFF"), HEAD


def build_xlsx(q) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Quotation"
    ws["A1"], ws["A1"].font = f"Quotation {q.number}", Font(bold=True, size=14)
    for r, (k, v) in enumerate([("Customer", q.customer_name), ("Company", q.company), ("Project", q.project_name),
                                ("Date", str(q.quote_date)), ("Valid until", str(q.expiry_date)), ("Status", q.status)], 3):
        ws.cell(row=r, column=1, value=k).font = Font(bold=True)
        ws.cell(row=r, column=2, value=v)
    _hdr(ws, 10, ["#", "Item", "Type", "Qty", f"Unit price ({q.currency})", f"Total ({q.currency})"])
    r = 11
    for i in q.items:
        for c, v in enumerate([i.position, i.name, i.kind, i.quantity, i.unit_price, i.total_price], 1):
            ws.cell(row=r, column=c, value=v)
        r += 1
    r += 1
    for label, val in (("Subtotal", q.subtotal), ("Discount", -q.discount_amount), ("Tax", q.tax_amount), ("Grand total", q.total)):
        ws.cell(row=r, column=5, value=label).font = Font(bold=True)
        ws.cell(row=r, column=6, value=val).number_format = "#,##0.00"
        r += 1
    for row in ws.iter_rows(min_row=11, min_col=5, max_col=6):
        for c in row:
            c.number_format = "#,##0.00"
    ws2 = wb.create_sheet("Material breakdown")
    _hdr(ws2, 1, ["Item", "Category", "Code", "Description", "Qty", "Unit", "Unit price", "Amount"])
    r = 2
    for i in q.items:
        for b in i.breakdown:
            for c, v in enumerate([i.name, b.category, b.code, b.description, b.quantity, b.unit, b.unit_price, b.amount], 1):
                ws2.cell(row=r, column=c, value=v)
            r += 1
    for sh in (ws, ws2):
        for col in range(1, 9):
            sh.column_dimensions[get_column_letter(col)].width = 18
    ws.column_dimensions["B"].width = 36
    ws2.column_dimensions["D"].width = 44
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
