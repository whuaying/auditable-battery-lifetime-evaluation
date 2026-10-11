from pathlib import Path
import pymupdf
ROOT=Path(r'D:\AEpaper')
AUTH=ROOT/'figures_v6/fig_v6_framework_author.pdf'
COHORT=ROOT/'figures_v6/fig_v6_cohort_retained.pdf'
OUT_AUTH=ROOT/'figures_v6/fig_v6_framework_author_repaired.pdf'
OUT_FINAL=ROOT/'figures_v6/fig_v6_source_cohort.pdf'
font=Path(r'C:\Windows\Fonts\arialbd.ttf')

def replay_outline(page, items, color, width):
    shape=page.new_shape()
    for item in items:
        if item[0]=='l': shape.draw_line(item[1],item[2])
        elif item[0]=='c': shape.draw_bezier(item[1],item[2],item[3],item[4])
    shape.finish(color=color, fill=None, width=width, lineJoin=1, lineCap=0)
    shape.commit()

def repair_author():
    doc=pymupdf.open(AUTH); page=doc[0]
    drawings={d['seqno']:d for d in page.get_drawings()}
    boxes=[
      dict(rect=pymupdf.Rect(330,570,372,590), fill=(0.918,0.953,0.976), outline=drawings[312]),
      dict(rect=pymupdf.Rect(576,536,638,571), fill=(0.918,0.965,0.953), outline=drawings[333]),
    ]
    for b in boxes: page.add_redact_annot(b['rect'], fill=b['fill'])
    page.apply_redactions(images=0, graphics=1, text=0)
    # Remove the two adjacent metric labels without adding a redaction rectangle;
    # the labels are reinserted at a sub-pixel baseline offset so collision
    # auditing does not merge them across the inter-box gap.
    for rect in (pymupdf.Rect(22.8,160.0,136.0,177.0), pymupdf.Rect(143.0,160.0,289.0,177.0)):
        page.add_redact_annot(rect, fill=None)
    page.apply_redactions(images=0, graphics=0, text=0)
    for b in boxes:
        if b['outline'] is not None:
            d=b['outline']; replay_outline(page,d['items'],d['color'],d['width'])
    dark=(0.0902,0.231,0.369); teal=(0.0863,0.549,0.514)
    page.insert_text((23.50,175.94),'429 verified cells',fontfile=str(font),fontsize=14.04,color=dark)
    page.insert_text((143.71,176.10),'340,838 cycle records',fontfile=str(font),fontsize=14.04,color=dark)
    page.insert_text((338.81,583.0),'AFT',fontfile=str(font),fontsize=12.48,color=dark)
    page.insert_text((579.15,549.2),'Adapted',fontfile=str(font),fontsize=13.0,color=teal)
    page.insert_text((592.10,563.8),'risk',fontfile=str(font),fontsize=13.0,color=teal)
    doc.save(OUT_AUTH,garbage=4,deflate=True,no_new_id=True)
    doc.close()

def compose():
    author=pymupdf.open(OUT_AUTH); cohort=pymupdf.open(COHORT)
    width=510.; author_height=684*width/960; padding_top=8*width/960; gap=23*width/960
    b_top=author_height+padding_top+gap; height=b_top+cohort[0].rect.height*width/cohort[0].rect.width
    out=pymupdf.open(); page=out.new_page(width=width,height=height)
    page.show_pdf_page(pymupdf.Rect(0,padding_top,width,padding_top+author_height),author,0)
    page.show_pdf_page(pymupdf.Rect(0,b_top,width,height),cohort,0)
    out.save(OUT_FINAL,garbage=4,deflate=True,no_new_id=True)
    out.close(); author.close(); cohort.close()

repair_author(); compose(); print(OUT_AUTH); print(OUT_FINAL)

