#!/usr/bin/env python3
"""Build editable scholarly manuscripts from the paired Markdown sources.
Run with the bundled document Python runtime documented in README.md.
"""
import re
from pathlib import Path
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
ROOT=Path(__file__).resolve().parent

def font(style,name,size,japanese=False):
 style.font.name=name;style.font.size=Pt(size);style.font.color.rgb=RGBColor(0,0,0)
 rf=style.element.get_or_add_rPr().get_or_add_rFonts();
 for attr in list(rf.attrib):
  if 'theme' in attr.lower():del rf.attrib[attr]
 rf.set(qn('w:ascii'),name);rf.set(qn('w:hAnsi'),name);rf.set(qn('w:eastAsia'),'Hiragino Mincho ProN' if japanese else name)

def inline(p,text):
 pattern=r'(\[[^\]]+\]\(https?://[^\s)]+\)|`[^`]+`|\*\*[^*]+\*\*)'
 for token in re.split(pattern,text):
  if not token:continue
  m=re.fullmatch(r'\[([^\]]+)\]\((https?://[^\s)]+)\)',token)
  if m:
   link=OxmlElement('w:hyperlink');link.set(qn('r:id'),p.part.relate_to(m[2],'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink',is_external=True));r=OxmlElement('w:r');props=OxmlElement('w:rPr');color=OxmlElement('w:color');color.set(qn('w:val'),'000000');props.append(color);u=OxmlElement('w:u');u.set(qn('w:val'),'single');props.append(u);r.append(props);t=OxmlElement('w:t');t.text=m[1];r.append(t);link.append(r);p._p.append(link)
  else:
   run=p.add_run(token[1:-1] if token.startswith('`') else token[2:-2] if token.startswith('**') else token)
   if token.startswith('`'):run.font.name='Courier New';run.font.size=Pt(9)
   if token.startswith('**'):run.bold=True

def build(lang):
 ja=lang=='ja';doc=Document();section=doc.sections[0];section.page_width=Inches(8.5);section.page_height=Inches(11)
 section.top_margin=Inches(.85);section.bottom_margin=Inches(.85);section.left_margin=Inches(.95);section.right_margin=Inches(.95);section.header_distance=Inches(.35);section.footer_distance=Inches(.35)
 for name,size in [('Normal',11),('Title',18),('Subtitle',12),('Heading 1',13),('Heading 2',11.5),('Heading 3',11),('Caption',10)]:font(doc.styles[name],'Times New Roman',size,ja)
 normal=doc.styles['Normal'].paragraph_format;normal.line_spacing=Pt(17) if ja else 1.12;normal.space_after=Pt(5);normal.widow_control=True
 for name in ['Heading 1','Heading 2','Heading 3']:
  s=doc.styles[name];s.font.bold=True;s.paragraph_format.space_before=Pt(11);s.paragraph_format.space_after=Pt(5);s.paragraph_format.keep_with_next=True
 doc.styles['Title'].paragraph_format.space_after=Pt(7);doc.styles['Title'].paragraph_format.keep_with_next=True
 doc.styles['Subtitle'].paragraph_format.keep_with_next=True
 header=section.header.paragraphs[0];header.text='業務主権と実装交換可能性' if ja else 'Business Sovereignty through Replaceable Implementations'
 for r in header.runs:r.font.size=Pt(8);r.font.color.rgb=RGBColor(0,0,0)
 footer=section.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
 field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
 lines=(ROOT/f'paper-{lang}.md').read_text().splitlines();buffer=[];code=False;front=True
 def flush():
  if buffer:
   p=doc.add_paragraph();inline(p,' '.join(buffer));
   if re.match(r'^\[\d+\]',buffer[0]):p.paragraph_format.line_spacing=1.0;p.paragraph_format.space_after=Pt(4)
   buffer.clear()
 for i,line in enumerate(lines):
  if line.startswith('```'):flush();code=not code;continue
  if code:
   p=doc.add_paragraph();p.paragraph_format.space_after=Pt(0);p.paragraph_format.keep_with_next=True;p.paragraph_format.left_indent=Inches(.15);r=p.add_run(line);r.font.name='Courier New';r.font.size=Pt(9);continue
  if line.startswith('# '):
   flush();p=doc.add_paragraph(line[2:].replace(' through Replaceable',' through\nReplaceable'),'Title');p.alignment=WD_ALIGN_PARAGRAPH.CENTER;continue
  if line.startswith('## ') and front:
   flush();p=doc.add_paragraph(line[3:],'Subtitle');p.alignment=WD_ALIGN_PARAGRAPH.CENTER;continue
  if front and (line=='Keiji Jin' or line=='神 敬二'):
   flush();p=doc.add_paragraph(line);p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.keep_with_next=True;continue
  if front and (line.startswith('Research manuscript') or line.startswith('研究論文草稿')):
   flush();p=doc.add_paragraph(line);p.alignment=WD_ALIGN_PARAGRAPH.CENTER
   for r in p.runs:r.font.size=Pt(9)
   front=False;continue
  if re.match(r'^#{2,3} ',line):
   flush();depth=len(line)-len(line.lstrip('#'));p=doc.add_paragraph(line[depth+1:],'Heading 1' if depth==2 else 'Heading 2');
   if line=='## 参考文献':p.paragraph_format.page_break_before=True
   continue
  if not line.strip():flush();continue
  buffer.append(line)
 flush()
 # Set proofing and East Asian typography without inventing an affiliation.
 for p in doc.paragraphs:
  for r in p.runs:
   rp=r._element.get_or_add_rPr();language=OxmlElement('w:lang');language.set(qn('w:val'),'ja-JP' if ja else 'en-US');language.set(qn('w:eastAsia'),'ja-JP');rp.append(language)
 for tree in [doc.styles.element,doc._element]:
  for border in tree.xpath('.//w:pBdr'):border.getparent().remove(border)
 doc.core_properties.author='Keiji Jin';doc.core_properties.title='業務主権を支える実装交換可能性' if ja else 'Business Sovereignty through Replaceable Implementations';doc.core_properties.subject='Exploratory software engineering manuscript';doc.core_properties.keywords='business sovereignty, implementation replacement, specification-driven development, AI'
 path=ROOT/f'paper-{lang}.docx';doc.save(path);print(path)
for lang in ['en','ja']:build(lang)
