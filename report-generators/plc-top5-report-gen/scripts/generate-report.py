"""
PLC Top 5 Report Generator
Produces a single combined .docx on the Desktop for all LSS RTX Kit/Tools programs.

Expected input:
  programs  list of dicts:
    { "name": str, "release_date": str, "overall_status": str, "items": [str, ...] }
"""

from datetime import date
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os


STATUS_COLORS = {
    "ON TRACK":  RGBColor(0x00, 0x80, 0x00),
    "AT RISK":   RGBColor(0xFF, 0x99, 0x00),
    "OFF TRACK": RGBColor(0xCC, 0x00, 0x00),
}


def generate(programs):
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    today_display = today.strftime("%d/%m/%Y")

    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    output_path = os.path.join(desktop, f"LSS_RTX_PLC_Top5_{today_str}.docx")

    doc = Document()

    for section in doc.sections:
        section.top_margin    = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin   = Inches(1)
        section.right_margin  = Inches(1)

    # Document title
    title = doc.add_heading(f"Top 5 Things - LSS RTX Kit/Tools PLC  {today_display}", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if title.runs:
        title.runs[0].font.color.rgb = RGBColor(0x76, 0xB9, 0x00)

    doc.add_paragraph()

    for i, prog in enumerate(programs):
        # Grey horizontal rule between programs
        if i > 0:
            p = doc.add_paragraph()
            pPr = p._p.get_or_add_pPr()
            pBdr = OxmlElement("w:pBdr")
            bottom = OxmlElement("w:bottom")
            bottom.set(qn("w:val"), "single")
            bottom.set(qn("w:sz"), "6")
            bottom.set(qn("w:space"), "1")
            bottom.set(qn("w:color"), "AAAAAA")
            pBdr.append(bottom)
            pPr.append(pBdr)

        # Program name
        prog_heading = doc.add_heading(prog["name"], level=1)
        if prog_heading.runs:
            prog_heading.runs[0].font.color.rgb = RGBColor(0x1F, 0x49, 0x7D)

        # Release Date
        rel_para = doc.add_paragraph()
        rel_para.add_run("Release Date:  ").bold = True
        rel_para.runs[0].font.size = Pt(10)
        rel_para.add_run(prog.get("release_date", "TBD")).font.size = Pt(10)

        # Overall Status
        status_para = doc.add_paragraph()
        status_para.add_run("Overall Status:  ").bold = True
        status_para.runs[0].font.size = Pt(10)
        status_run = status_para.add_run(prog["overall_status"])
        status_run.bold = True
        status_run.font.size = Pt(10)
        status_run.font.color.rgb = STATUS_COLORS.get(prog["overall_status"], RGBColor(0, 0, 0))

        doc.add_paragraph()

        # Top 5 items
        for item in prog["items"]:
            p = doc.add_paragraph(style="List Number")
            run = p.add_run(item)
            run.font.size = Pt(10)
            if item.startswith("⚠"):
                run.font.color.rgb = RGBColor(0xCC, 0x00, 0x00)

        doc.add_paragraph()

    # Signature
    doc.add_paragraph()
    doc.add_paragraph("Best Regards,\n\nSherry Faramarz").runs[0].font.size = Pt(10)

    doc.save(output_path)
    print(f"Saved: {output_path}")
    return output_path
