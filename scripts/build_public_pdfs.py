"""Build publicly shareable demonstration PDFs from the author-written Markdown notes."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

source_dir = ROOT / 'data' / 'sample_notes'
out_dir = ROOT / 'data' / 'public_pdfs'
out_dir.mkdir(exist_ok=True)
styles = getSampleStyleSheet()
title_style = ParagraphStyle('PlainTitle', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=18, leading=22, spaceAfter=14)
body_style = ParagraphStyle('Body', parent=styles['BodyText'], fontName='Helvetica', fontSize=11, leading=15, spaceAfter=10)

for note in sorted(source_dir.glob('*.md')):
    story = []
    for block in note.read_text(encoding='utf-8').split('\n---\n'):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        heading = lines.pop(0).lstrip('# ').replace('&', '&amp;')
        story += [Paragraph(heading, title_style)]
        for line in lines:
            story += [Paragraph(line.replace('&', '&amp;'), body_style)]
        story += [Spacer(1, 0.12 * inch)]
    doc = SimpleDocTemplate(str(out_dir / f'{note.stem}.pdf'), pagesize=A4, rightMargin=0.85*inch, leftMargin=0.85*inch, topMargin=0.8*inch, bottomMargin=0.8*inch, title=note.stem)
    doc.build(story)
    print(out_dir / f'{note.stem}.pdf')
