#!/usr/bin/env python3
"""통합 PDF 재생성 — 최신 연도 먼저 (year 내림차순)"""
import json
from pathlib import Path
from dataclasses import dataclass, field
from fpdf import FPDF, XPos, YPos

BASE   = Path('/Users/ddoli1545/Desktop/test')
OUT    = BASE / '강의록별_기출문제_통합'
FONT_R = str(BASE / 'SDGothicNeo-Regular.ttf')
FONT_B = str(BASE / 'SDGothicNeo-Bold.ttf')

@dataclass
class Question:
    year: int = 0
    num: int = 0
    professor: str = ''
    topic: str = ''
    lecture_key: str = ''
    lecture_title: str = ''
    question_text: str = ''
    choices: list = field(default_factory=list)
    answer: str = ''
    explanation: str = ''
    is_complete: bool = True
    supplement_note: str = ''

MARGIN = 15
PAGE_W = 210

class KoreanPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font('K', '',  FONT_R)
        self.add_font('K', 'B', FONT_B)
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(MARGIN, MARGIN, MARGIN)
        self._lect_title = ''

    def header(self):
        self.set_font('K', 'B', 9)
        self.set_text_color(100, 116, 139)
        self.cell(0, 8, f'호흡기 기출문제 · {self._lect_title}',
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(226, 232, 240)
        self.line(MARGIN, self.get_y(), PAGE_W - MARGIN, self.get_y())
        self.ln(3)
        self.set_text_color(0)

    def footer(self):
        self.set_y(-13)
        self.set_font('K', '', 8)
        self.set_text_color(150)
        self.cell(0, 10, f'{self.page_no()}', align='C')
        self.set_text_color(0)

    def section_header(self, text, color=(59, 130, 246)):
        self.set_font('K', 'B', 10)
        self.set_fill_color(*color)
        self.set_text_color(255)
        self.cell(0, 9, f'  {text}', fill=True,
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(0)
        self.ln(2)

    def question_block(self, q):
        year_label = f'{q.year}년  Q{q.num}'
        if getattr(q, 'supplement_note', ''):
            year_label += '  ★보완'
        self.section_header(f'{year_label}   [{q.professor}]  {q.topic}')
        cw = PAGE_W - 2 * MARGIN

        self.set_font('K', 'B', 10)
        self.multi_cell(cw, 6.5, f'Q{q.num}. {q.question_text}',
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

        self.set_font('K', '', 10)
        for ch in q.choices:
            self.multi_cell(cw, 6, f'   {ch}',
                            new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(3)

        self.set_font('K', 'B', 10)
        self.set_fill_color(239, 246, 255)
        self.set_draw_color(191, 219, 254)
        self.set_line_width(0.3)
        self.cell(cw, 8, f'정답: {q.answer}', border=1, fill=True,
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

        if q.explanation:
            self.set_font('K', 'B', 9)
            self.set_text_color(30, 64, 175)
            self.cell(0, 7, '해설', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.set_text_color(0)
            self.set_font('K', '', 9.5)
            self.set_fill_color(248, 250, 252)
            self.multi_cell(cw, 6, q.explanation, fill=True,
                            new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(6)
        self.set_draw_color(241, 245, 249)
        self.line(MARGIN, self.get_y(), PAGE_W - MARGIN, self.get_y())
        self.ln(4)


def make_pdf(lecture_key, lecture_title, questions):
    if not questions:
        return
    pdf = KoreanPDF()
    pdf._lect_title = lecture_title

    # 표지
    pdf.add_page()
    pdf.set_font('K', 'B', 18)
    pdf.set_text_color(30, 41, 59)
    pdf.ln(30)
    pdf.multi_cell(0, 12, lecture_title, align='C',
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)
    pdf.set_font('K', '', 12)
    pdf.set_text_color(100, 116, 139)
    years = sorted({q.year for q in questions}, reverse=True)
    pdf.cell(0, 8,
             f'역대 기출문제  |  {", ".join(map(str, years))}년  |  총 {len(questions)}문제',
             align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0)

    # 최신 연도 먼저
    for q in sorted(questions, key=lambda x: (-x.year, x.num)):
        pdf.add_page()
        pdf.question_block(q)

    out_path = OUT / f'{lecture_key}.pdf'
    pdf.output(str(out_path))
    print(f'  ✓ {out_path.name}  ({len(questions)}문제, {years[-1]}~{years[0]}년)')


def main():
    json_path = OUT / '_all_questions.json'
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)

    # Question 객체로 변환
    all_qs = []
    for d in data:
        q = Question()
        for k, v in d.items():
            if hasattr(q, k):
                setattr(q, k, v)
        all_qs.append(q)

    # lecture_key별 그룹화
    grouped = {}
    for q in all_qs:
        if q.lecture_key:
            grouped.setdefault(q.lecture_key, []).append(q)

    print(f'총 {len(all_qs)}문제, {len(grouped)}개 강의록 PDF 재생성...')
    for lk, qs in sorted(grouped.items()):
        lt = qs[0].lecture_title
        make_pdf(lk, lt, qs)

    no_key = [q for q in all_qs if not q.lecture_key]
    if no_key:
        make_pdf('미분류', '미분류 문제', no_key)

    print(f'\n✅ 완료')


if __name__ == '__main__':
    main()
