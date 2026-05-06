#!/usr/bin/env python3
"""
전체 연도 기출문제 통합 처리 스크립트
- 역대 야마/야마풀이 폴더 처리
- Claude API: 주제 분류 + 불완전 문제 보완
- 강의록별 통합 PDF 생성
"""

import os, re, json, textwrap
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

import pdfplumber
import anthropic
from fpdf import FPDF, XPos, YPos

# ── 경로 ────────────────────────────────────────────────
BASE   = Path('/Users/ddoli1545/Desktop/test')
EXAM   = BASE / '역대 야마'
SOL    = BASE / '역대 야마풀이'
OUT    = BASE / '강의록별_기출문제_통합'
FONT_R = str(BASE / 'SDGothicNeo-Regular.ttf')
FONT_B = str(BASE / 'SDGothicNeo-Bold.ttf')
OUT.mkdir(exist_ok=True)

client = anthropic.Anthropic()

# ── 데이터 구조 ────────────────────────────────────────
@dataclass
class Question:
    year: int
    num: int
    professor: str
    topic: str
    lecture_key: str = ''        # 강의록 파일 키 (분류 후)
    lecture_title: str = ''
    question_text: str = ''
    choices: list = field(default_factory=list)
    answer: str = ''
    explanation: str = ''
    is_complete: bool = True     # False면 Claude가 보완

# ── 강의 주제 → 강의록 매핑 ────────────────────────────
TOPIC_MAP = [
    # (키워드 목록, lecture_key, lecture_title)
    (["뒷가슴벽", "종격동", "금동윤"],
     "1216_뒷가슴벽구조_종격동", "뒷가슴벽의 구조 (종격동)"),
    (["가슴벽", "흉곽 구조", "thoracic wall", "채민철"],
     "1216_가슴벽의구조", "가슴벽의 구조"),
    (["폐의 구조", "흉강", "늑막", "lung structure"],
     "1216_폐의구조", "폐의 구조"),
    (["호흡기의 해부학", "기관", "기관지", "bronchus", "bronchi",
      "호흡기 해부학"],
     "1216_호흡기해부학적구조", "호흡기의 해부학적 구조"),
    (["호흡상피", "조직학", "폐포세포", "type1", "type2", "surfactant",
      "구조와 기능"],
     "1216_호흡상피조직학적구조와기능", "호흡상피의 조직학적 구조와 기능"),
    (["호흡생리", "호흡 생리", "compliance", "유순도", "환기", "환기-관류",
      "V/Q", "폐활량", "호흡역학", "배재훈"],
     "1217_호흡생리학", "호흡생리학"),
    (["동맥혈가스", "ABG", "저산소", "산염기", "hypoxemia", "박재석"],
     "1217_동맥혈가스분석_저산소혈증", "동맥혈가스분석과 저산소혈증"),
    (["폐기능 검사", "spirometry", "FEV", "FVC", "폐기능"],
     "1217_폐기능검사", "폐기능 검사"),
    (["주요증상", "호흡곤란", "기침", "객혈", "진찰", "진단방법",
      "호흡기 진찰", "호흡기 증상", "총론"],
     "1218_호흡기질환주요증상_진찰및진단방법",
     "호흡기 질환의 주요증상 / 진찰 및 진단방법"),
    (["정상 흉부 영상", "chest PA", "흉부 X선", "흉부 영상의학 소견 및 검사",
      "정상 흉부"],
     "1218_정상흉부영상의학", "정상 흉부 영상의학 소견 및 검사법"),
    (["영상의학 소견 유형", "흉부질환 영상", "결절", "공동", "간유리"],
     "1218_흉부질환영상의학소견유형분석",
     "흉부질환의 영상의학 소견 유형 분석"),
    (["상기도", "급성기관지염", "후비루", "비염", "상기도 질환", "김태훈"],
     "1218_상기도질환_급성기관지염", "상기도 질환과 급성기관지염"),
    (["지역사회획득폐렴", "CAP", "community"],
     "1218_지역사회획득폐렴", "지역사회획득폐렴"),
    (["병원획득폐렴", "HAP", "VAP", "흡인성 폐렴", "병원내 폐렴"],
     "1218_병원획득폐렴_흡인성폐렴", "병원획득폐렴 / 흡인성 폐렴"),
    (["치료약제 (1)", "치료약제(1)", "베타작용제", "ICS", "흡입제",
      "기관지확장제", "이성용"],
     "1218_1224_호흡기치료약제1", "호흡기질환의 치료약제 (1)"),
    (["폐농양", "기타 폐감염", "아스페르길루스", "진균", "곰팡이"],
     "1222_폐농양_기타폐감염", "폐농양과 기타 폐감염"),
    (["결핵의 진단", "폐결핵 진단", "tuberculosis 진단", "AFB"],
     "1222_폐결핵진단", "폐결핵의 진단"),
    (["결핵의 치료", "폐결핵 치료", "항결핵제", "INH", "rifampin",
      "isoniazid"],
     "1222_폐결핵치료", "폐결핵의 치료"),
    (["기관지확장증", "bronchiectasis"],
     "1222_기관지확장증", "기관지확장증"),
    (["폐색전증", "PE ", "pulmonary embolism", "DVT", "혈전"],
     "1223_폐색전증", "폐색전증"),
    (["천식", "기관지천식", "asthma"],
     "1223_천식_진단및치료", "기관지천식 — 진단 및 치료"),
    (["COPD", "만성폐쇄성", "만성 폐쇄성"],
     "1223_COPD", "만성폐쇄성폐질환 (COPD)"),
    (["폐 병리학", "TBL", "병리학 개요", "급성 폐 손상", "ARDS"],
     "1224_폐병리학개요", "폐 병리학 개요 (TBL1)"),
    (["감염성 폐질환", "세균성폐렴", "바이러스성폐렴", "황일선"],
     "1224_감염성폐질환", "감염성 폐질환"),
    (["기도 및 간질성", "간질성 폐질환", "폐부종", "ILD", "fibrosis"],
     "1224_기도간질성폐질환_폐부종_폐색전증영상의학",
     "기도·간질성 폐질환 / 폐부종·폐색전증 영상의학"),
    (["폐렴의 영상의학"],
     "1224_기도간질성폐질환_폐부종_폐색전증영상의학",
     "기도·간질성 폐질환 / 폐부종·폐색전증 영상의학"),
    (["환기장애", "수면무호흡", "OSA", "CPAP", "수면"],
     "1224_환기장애_수면무호흡", "환기장애와 수면 무호흡"),
    (["직업성", "환경성 폐질환", "진폐증", "석면"],
     "1224_직업성환경성폐질환", "직업성 및 환경성 폐질환"),
    (["치료약제 (2)", "치료약제(2)", "진해제", "거담제", "항히스타민",
      "장정희"],
     "1224_호흡기치료약제2", "호흡기질환의 치료약제 (2)"),
]


def classify_topic_local(topic: str, professor: str, q_text: str) -> tuple[str, str]:
    """로컬 키워드 매핑으로 강의록 분류"""
    combined = (topic + ' ' + professor + ' ' + q_text[:200]).lower()
    for keywords, key, title in TOPIC_MAP:
        for kw in keywords:
            if kw.lower() in combined:
                return key, title
    return '', topic  # 미분류


# ── PDF 텍스트 추출 ───────────────────────────────────
def extract_pdf_text(path: Path) -> str:
    try:
        with pdfplumber.open(str(path)) as pdf:
            return '\n'.join(
                (p.extract_text() or '') for p in pdf.pages
            )
    except Exception as e:
        print(f'  [PDF오류] {path.name}: {e}')
        return ''


# ── 파서: 2022/2023 형식 (문제 본문 포함) ─────────────
RE_QNO_FULL = re.compile(
    r'문제번호\s*(\d+)\s+교수님\s+(.+?)\n'
    r'주제\s+(.+?)(?:해설자|감수자)',
    re.DOTALL
)

def parse_full_format(year: int, text: str) -> list[Question]:
    """2022/2023/2025 풀이: 문제+정답+해설 모두 포함"""
    qs = []
    # 페이지 구분자로 분할 후 각 블록 처리
    blocks = re.split(r'(?=문제번호\s+\d+\s+교수님)', text)
    for block in blocks:
        if '문제번호' not in block:
            continue

        num_m   = re.search(r'문제번호\s+(\d+)', block)
        prof_m  = re.search(r'교수님\s+([^\n]+)', block)
        topic_m = re.search(r'주제\s+(.+?)(?:해설자|감수자|\n문제|\n답)', block, re.DOTALL)
        q_m     = re.search(r'문제\s+(\d+[.．]?\s*.+?)(?=\n\s*답\s|\n\s*1\)|$)',
                             block, re.DOTALL)
        # 선지 추출
        choices = re.findall(r'\n\s*([1-5①-⑤][).）])\s*(.+?)(?=\n\s*[1-5①-⑤][).）]|\n\s*답|\Z)',
                              block, re.DOTALL)
        ans_m   = re.search(r'\n답\s*([1-5①-⑤④⑤][)）]?)', block)
        sol_m   = re.search(r'해설\s+(.+?)(?=문제번호|\Z)', block, re.DOTALL)

        if not num_m:
            continue

        q_text   = q_m.group(1).strip() if q_m else ''
        ch_list  = [f'{c[0]} {c[1].strip()}' for c in choices]
        ans      = ans_m.group(1).strip() if ans_m else ''
        expl     = sol_m.group(1).strip() if sol_m else ''
        topic    = (topic_m.group(1).strip().split('\n')[0]
                    if topic_m else '')
        # 헤더 잔여물 제거
        topic = re.sub(r'\s*(해설자|감수자).+', '', topic).strip()
        prof  = (prof_m.group(1).strip().split('\n')[0]
                 if prof_m else '')

        lk, lt = classify_topic_local(topic, prof, q_text)
        q = Question(
            year=year, num=int(num_m.group(1)),
            professor=prof, topic=topic,
            lecture_key=lk, lecture_title=lt,
            question_text=q_text,
            choices=ch_list, answer=ans, explanation=expl,
            is_complete=bool(q_text and (ch_list or '객관식' in q_text))
        )
        qs.append(q)
    return qs


# ── 파서: 2021 형식 (해설만, 문제 없음) ───────────────
def parse_sol_only(year: int, sol_text: str) -> list[dict]:
    """2017/2019/2021 풀이: 답+해설만 있음 → 나중에 문제 텍스트 병합"""
    items = []
    blocks = re.split(r'(?=문제번호\s+\d+)', sol_text)
    for block in blocks:
        if '문제번호' not in block:
            continue
        num_m   = re.search(r'문제번호\s+(\d+)', block)
        prof_m  = re.search(r'교수님\s+([^\n]+)', block)
        topic_m = re.search(r'주제\s+(.+?)(?:\n해설자|\n답|\n감수자)', block, re.DOTALL)
        ans_m   = re.search(r'답\s*([1-5①-⑤④⑤][)）]?)', block)
        sol_m   = re.search(r'해설\s+(.+?)(?=문제번호|\Z)', block, re.DOTALL)
        if not num_m:
            continue
        topic = (topic_m.group(1).strip().split('\n')[0]
                 if topic_m else '')
        topic = re.sub(r'\s*(해설자|감수자).+', '', topic).strip()
        items.append({
            'num':         int(num_m.group(1)),
            'professor':   (prof_m.group(1).strip() if prof_m else ''),
            'topic':       topic,
            'answer':      (ans_m.group(1).strip() if ans_m else ''),
            'explanation': (sol_m.group(1).strip() if sol_m else ''),
        })
    return items


# ── 파서: 시험지 문제 추출 ─────────────────────────────
def parse_exam_questions(year: int, text: str) -> dict[int, dict]:
    """시험지에서 문제번호 → {question_text, choices} 딕셔너리"""
    result = {}
    # 문제 블록: "1. 문제텍스트\n1) ...\n2) ...\n"
    pattern = re.compile(
        r'(?:^|\n)\s*(\d+)[.．]\s+(.+?)(?=\n\s*\d+[.．]\s|\Z)',
        re.DOTALL
    )
    for m in pattern.finditer(text):
        num     = int(m.group(1))
        body    = m.group(2).strip()
        # 선지 분리
        ch_pat  = re.compile(r'([1-5①-⑤][).）])\s*(.+?)(?=[1-5①-⑤][).）]|\Z)',
                              re.DOTALL)
        choices = [f'{c[0]} {c[1].strip()}' for c in ch_pat.findall(body)]
        # 선지 앞 본문만
        q_text  = re.split(r'\n\s*1[).）]', body)[0].strip()
        if 1 <= num <= 80:
            result[num] = {'question_text': q_text, 'choices': choices}
    return result


# ── 파서: 2016 풀이 형식 ──────────────────────────────
def parse_2016_format(text: str) -> list[Question]:
    """2016 호흡기학 1차 문제 및 풀이 형식"""
    qs = []
    # "1. 문제텍스트\n선지들\n답: N\n해설:" 패턴
    blocks = re.split(r'(?=\n\d+[.．]\s)', '\n' + text)
    for block in blocks:
        m = re.match(r'\n(\d+)[.．]\s+(.+?)(?=\n\d+[.．]\s|\Z)', block, re.DOTALL)
        if not m:
            continue
        num   = int(m.group(1))
        body  = m.group(2)
        ans_m = re.search(r'답\s*[：:]\s*(\S+)', body)
        sol_m = re.search(r'해설\s*[：:]?\s*(.+?)(?=\n\d+[.．]|\Z)', body, re.DOTALL)
        ch_m  = re.findall(r'([1-5①-⑤][).）])\s*(.+?)(?=[1-5①-⑤][).）]|답\s*[：:]|\Z)',
                            body, re.DOTALL)
        q_text = re.split(r'\n\s*1[).）]', body)[0].strip()
        ch_list = [f'{c[0]} {c[1].strip()}' for c in ch_m]
        lk, lt = classify_topic_local('', '', q_text)
        qs.append(Question(
            year=2016, num=num,
            professor='', topic='',
            lecture_key=lk, lecture_title=lt,
            question_text=q_text, choices=ch_list,
            answer=(ans_m.group(1) if ans_m else ''),
            explanation=(sol_m.group(1).strip() if sol_m else ''),
            is_complete=bool(q_text and ch_list),
        ))
    return qs


# ── Claude API: 구조화 + 보완 ─────────────────────────
SYSTEM_PROMPT = """당신은 의학 시험 문제를 구조화하고 보완하는 전문가입니다.
주어진 텍스트에서 문제를 정확히 파싱하고, 불완전한 부분은 의학적 지식으로 보완하세요."""

def claude_extract_and_supplement(year: int, raw_text: str, source_label: str) -> list[dict]:
    """Claude API로 텍스트에서 구조화된 문제 목록 추출 + 불완전 부분 보완"""
    prompt = f"""다음은 {year}년 호흡기 1차 시험 관련 문서입니다 ({source_label}).

각 문제를 다음 JSON 형식의 배열로 추출하세요:
{{
  "num": 문제번호(정수),
  "professor": "교수님 이름",
  "topic": "강의 주제",
  "question_text": "문제 본문 (번호 제외, 완전한 문장으로)",
  "choices": ["1) ...", "2) ...", "3) ...", "4) ...", "5) ..."],
  "answer": "정답 번호(예: 3)",
  "explanation": "해설 내용",
  "supplement_note": "보완한 내용이 있으면 명시, 없으면 빈 문자열"
}}

중요:
- 문제 본문이나 선지가 불완전하거나 잘려있으면, 호흡기내과 의학 지식으로 자연스럽게 완성하세요.
- 선지가 아예 없는 문제는 의학적으로 적합한 5개 선지를 만들어주세요.
- 선지가 일부만 있으면 나머지를 추가하세요.
- 정답 번호는 '1'~'5' 형식으로만 표기하세요.
- JSON 배열만 반환하고 다른 텍스트는 쓰지 마세요.

문서:
{raw_text[:12000]}"""

    try:
        resp = client.messages.create(
            model='claude-sonnet-4-6',
            max_tokens=8000,
            messages=[{'role': 'user', 'content': prompt}]
        )
        raw = resp.content[0].text.strip()
        # JSON 배열 추출
        json_m = re.search(r'\[.+\]', raw, re.DOTALL)
        if json_m:
            return json.loads(json_m.group())
    except Exception as e:
        print(f'  [Claude 오류] {e}')
    return []


def claude_supplement_sparse(year: int, sparse_entries: list[dict]) -> list[dict]:
    """2020 복기 등 매우 짧은 문제 설명을 완전한 문제로 보완"""
    if not sparse_entries:
        return []
    entries_str = json.dumps(sparse_entries, ensure_ascii=False, indent=2)
    prompt = f"""다음은 {year}년 호흡기 1차 시험 문제의 간략한 복기 메모입니다.
각 메모를 실제 시험 문제 형식으로 완전히 재구성해주세요.

복기 메모:
{entries_str}

각 항목에 대해 다음 JSON 형식으로 반환하세요:
{{
  "num": 문제번호,
  "professor": "교수님",
  "topic": "주제",
  "question_text": "완전한 문제 본문 (환자 증례 포함)",
  "choices": ["1) ...", "2) ...", "3) ...", "4) ...", "5) ..."],
  "answer": "정답 번호",
  "explanation": "해설",
  "supplement_note": "보완 내용 설명"
}}

- 복기 메모의 핵심 정보(증상, 검사 수치, 정답)는 반드시 유지하세요.
- 문제는 호흡기내과 임상 시험 스타일로 작성하세요.
- JSON 배열만 반환하세요."""

    try:
        resp = client.messages.create(
            model='claude-sonnet-4-6',
            max_tokens=6000,
            messages=[{'role': 'user', 'content': prompt}]
        )
        raw = resp.content[0].text.strip()
        json_m = re.search(r'\[.+\]', raw, re.DOTALL)
        if json_m:
            return json.loads(json_m.group())
    except Exception as e:
        print(f'  [Claude 보완 오류] {e}')
    return []


# ── PDF 생성 ──────────────────────────────────────────
MARGIN = 15
PAGE_W = 210

class KoreanPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font('K',  '', FONT_R)
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

    def section_header(self, text: str, color=(59, 130, 246)):
        self.set_font('K', 'B', 10)
        self.set_fill_color(*color)
        self.set_text_color(255)
        self.cell(0, 9, f'  {text}', fill=True,
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(0)
        self.ln(2)

    def question_block(self, q: Question):
        """문제 + 선지 + 정답 + 해설 블록"""
        # ─ 문제 헤더 바 ─
        year_label = f'{q.year}년  Q{q.num}'
        if q.supplement_note if hasattr(q, 'supplement_note') else False:
            year_label += '  ★보완'
        self.section_header(f'{year_label}   [{q.professor}]  {q.topic}')

        content_w = PAGE_W - 2 * MARGIN

        # ─ 문제 본문 ─
        self.set_font('K', 'B', 10)
        self.multi_cell(content_w, 6.5,
                        f'Q{q.num}. {q.question_text}',
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

        # ─ 선지 ─
        self.set_font('K', '', 10)
        for ch in q.choices:
            self.multi_cell(content_w, 6,
                            f'   {ch}',
                            new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.ln(3)

        # ─ 정답 박스 ─
        ans_text = f'정답: {q.answer}'
        self.set_font('K', 'B', 10)
        self.set_fill_color(239, 246, 255)
        self.set_draw_color(191, 219, 254)
        self.set_line_width(0.3)
        self.cell(content_w, 8, ans_text, border=1, fill=True,
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

        # ─ 해설 ─
        if q.explanation:
            self.set_font('K', 'B', 9)
            self.set_text_color(30, 64, 175)
            self.cell(0, 7, '해설',
                      new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.set_text_color(0)
            self.set_font('K', '', 9.5)
            self.set_fill_color(248, 250, 252)
            self.multi_cell(content_w, 6, q.explanation,
                            fill=True,
                            new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.ln(6)
        # 구분선
        self.set_draw_color(241, 245, 249)
        self.line(MARGIN, self.get_y(), PAGE_W - MARGIN, self.get_y())
        self.ln(4)


def make_lecture_pdf(lecture_key: str, lecture_title: str,
                     questions: list[Question]):
    """강의록별 PDF 생성"""
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
    years = sorted({q.year for q in questions})
    pdf.cell(0, 8,
             f'역대 기출문제  |  {", ".join(map(str,years))}년  '
             f'|  총 {len(questions)}문제',
             align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0)

    # 문제 페이지 (연도 순)
    for q in sorted(questions, key=lambda x: (x.year, x.num)):
        pdf.add_page()
        pdf.question_block(q)

    out_path = OUT / f'{lecture_key}.pdf'
    pdf.output(str(out_path))
    print(f'  ✓ {out_path.name}  ({len(questions)}문제, '
          f'{years[0]}~{years[-1]}년)')


# ── 메인 파이프라인 ────────────────────────────────────
def dicts_to_questions(year: int, dicts: list[dict]) -> list[Question]:
    """Claude 반환 dict → Question 객체"""
    result = []
    for d in dicts:
        if not isinstance(d, dict):
            continue
        topic = str(d.get('topic', ''))
        prof  = str(d.get('professor', ''))
        q_txt = str(d.get('question_text', ''))
        lk, lt = classify_topic_local(topic, prof, q_txt)
        q = Question(
            year=year,
            num=int(d.get('num', 0)),
            professor=prof,
            topic=topic,
            lecture_key=lk,
            lecture_title=lt,
            question_text=q_txt,
            choices=d.get('choices', []),
            answer=str(d.get('answer', '')),
            explanation=str(d.get('explanation', '')),
            is_complete=not bool(d.get('supplement_note', '')),
        )
        # supplement_note 보존
        if d.get('supplement_note'):
            q.supplement_note = d['supplement_note']
        result.append(q)
    return result


def merge_sol_exam(sol_items: list[dict], exam_qs: dict,
                   year: int) -> list[Question]:
    """해설-only 풀이 + 시험지 병합"""
    result = []
    for s in sol_items:
        num = s['num']
        ex  = exam_qs.get(num, {})
        topic = s['topic']
        prof  = s['professor']
        q_txt = ex.get('question_text', '')
        choices = ex.get('choices', [])
        lk, lt  = classify_topic_local(topic, prof, q_txt)
        result.append(Question(
            year=year, num=num,
            professor=prof, topic=topic,
            lecture_key=lk, lecture_title=lt,
            question_text=q_txt, choices=choices,
            answer=s['answer'], explanation=s['explanation'],
            is_complete=bool(q_txt),
        ))
    return result


def main():
    all_questions: list[Question] = []

    # ── 2025 풀이 (full format) ────────────────────────
    print('\n[2025] 풀이 파싱...')
    t25 = extract_pdf_text(SOL / '2025 호흡기 1차 풀이.pdf')
    qs25 = parse_full_format(2025, t25)
    print(f'  → {len(qs25)}문제')
    all_questions.extend(qs25)

    # ── 2023 풀이 (full format) ────────────────────────
    print('\n[2023] 풀이 파싱...')
    t23 = extract_pdf_text(SOL / '2023 호흡기 1차 풀이.pdf')
    qs23 = parse_full_format(2023, t23)
    print(f'  → {len(qs23)}문제')
    all_questions.extend(qs23)

    # ── 2022 풀이 (full format) ────────────────────────
    print('\n[2022] 풀이 파싱...')
    t22 = extract_pdf_text(SOL / '2022 호흡기 1차 풀이.pdf')
    qs22 = parse_full_format(2022, t22)
    print(f'  → {len(qs22)}문제')
    all_questions.extend(qs22)

    # ── 2021 풀이 + 시험지 병합 ───────────────────────
    print('\n[2021] 풀이+시험지 병합...')
    t21s = extract_pdf_text(SOL / '2021 호흡기 1차 풀이.pdf')
    t21e = extract_pdf_text(EXAM / '2021 호흡기 1차.pdf')
    sol21  = parse_sol_only(2021, t21s)
    exam21 = parse_exam_questions(2021, t21e)
    qs21   = merge_sol_exam(sol21, exam21, 2021)
    # 미매핑 문제는 Claude로 보완
    incomplete21 = [q for q in qs21 if not q.question_text]
    if incomplete21:
        print(f'  → {len(incomplete21)}문제 Claude 보완 중...')
        # 해당 시험지 텍스트를 Claude에게 전달
        extra = claude_extract_and_supplement(2021, t21e, '2021 시험지')
        extra_map = {d.get('num', 0): d for d in extra if isinstance(d, dict)}
        for q in incomplete21:
            if q.num in extra_map:
                d = extra_map[q.num]
                q.question_text = d.get('question_text', '')
                q.choices       = d.get('choices', [])
                if not q.answer:
                    q.answer = str(d.get('answer', ''))
                q.is_complete = True
    print(f'  → {len(qs21)}문제')
    all_questions.extend(qs21)

    # ── 2019 풀이 + 시험지 ────────────────────────────
    print('\n[2019] 풀이+시험지 병합...')
    t19s = extract_pdf_text(SOL / '2019 호흡기학 1차 풀이.pdf')
    t19e = extract_pdf_text(EXAM / '2019 호흡기학 1차.pdf')
    sol19  = parse_sol_only(2019, t19s)
    exam19 = parse_exam_questions(2019, t19e)
    qs19   = merge_sol_exam(sol19, exam19, 2019)
    incomplete19 = [q for q in qs19 if not q.question_text]
    if incomplete19:
        print(f'  → {len(incomplete19)}문제 Claude 보완 중...')
        extra = claude_extract_and_supplement(2019, t19e, '2019 시험지')
        extra_map = {d.get('num', 0): d for d in extra if isinstance(d, dict)}
        for q in incomplete19:
            if q.num in extra_map:
                d = extra_map[q.num]
                q.question_text = d.get('question_text', '')
                q.choices       = d.get('choices', [])
                if not q.answer:
                    q.answer = str(d.get('answer', ''))
                q.is_complete = True
    print(f'  → {len(qs19)}문제')
    all_questions.extend(qs19)

    # ── 2017 풀이 + 시험지 ────────────────────────────
    print('\n[2017] 풀이+시험지 병합...')
    t17s = extract_pdf_text(SOL / '2017 호흡기학 1차 풀이.pdf')
    t17e = extract_pdf_text(EXAM / '2017 호흡기학 1차.pdf')
    sol17  = parse_sol_only(2017, t17s)
    exam17 = parse_exam_questions(2017, t17e)
    qs17   = merge_sol_exam(sol17, exam17, 2017)
    incomplete17 = [q for q in qs17 if not q.question_text]
    if incomplete17:
        print(f'  → {len(incomplete17)}문제 Claude 보완 중...')
        extra = claude_extract_and_supplement(2017, t17e, '2017 시험지')
        extra_map = {d.get('num', 0): d for d in extra if isinstance(d, dict)}
        for q in incomplete17:
            if q.num in extra_map:
                d = extra_map[q.num]
                q.question_text = d.get('question_text', '')
                q.choices       = d.get('choices', [])
                if not q.answer:
                    q.answer = str(d.get('answer', ''))
                q.is_complete = True
    print(f'  → {len(qs17)}문제')
    all_questions.extend(qs17)

    # ── 2016 풀이 ─────────────────────────────────────
    print('\n[2016] 풀이 파싱...')
    t16 = extract_pdf_text(SOL / '2016 호흡기학 1차 풀이.pdf')
    qs16 = parse_2016_format(t16)
    # 미완성은 Claude 처리
    incomplete16 = [q for q in qs16 if not q.is_complete]
    if incomplete16 or not qs16:
        print(f'  → Claude로 재파싱...')
        dicts16 = claude_extract_and_supplement(2016, t16, '2016 풀이')
        qs16 = dicts_to_questions(2016, dicts16)
    print(f'  → {len(qs16)}문제')
    all_questions.extend(qs16)

    # ── 2015 풀이 ─────────────────────────────────────
    print('\n[2015] 풀이 파싱 (Claude)...')
    t15 = extract_pdf_text(SOL / '2015 호흡기학 1차 풀이.pdf')
    t15b = extract_pdf_text(SOL / '2015 호흡기학 1차 피드백.pdf')
    combined15 = t15 + '\n' + t15b
    dicts15 = claude_extract_and_supplement(2015, combined15, '2015 풀이+피드백')
    qs15 = dicts_to_questions(2015, dicts15)
    print(f'  → {len(qs15)}문제')
    all_questions.extend(qs15)

    # ── 2020 복기 (매우 불완전 → Claude 보완) ─────────
    print('\n[2020] 복기 보완 (Claude)...')
    t20 = extract_pdf_text(EXAM / '2020 호흡기학 1차 복기.pdf')
    # 복기는 짧은 메모 형식이므로 sparse 보완 사용
    # 우선 간단히 섹션별로 파싱
    sparse20 = []
    lines = [l.strip() for l in t20.split('\n') if l.strip()]
    cur = {}
    qno = 0
    for line in lines:
        nm = re.match(r'^(\d+)[.．]\s+(.+)', line)
        if nm:
            if cur:
                sparse20.append(cur)
            qno += 1
            cur = {'num': int(nm.group(1)), 'memo': nm.group(2),
                   'answer': '', 'choices_hint': ''}
        elif cur:
            if '답:' in line or '답 :' in line:
                cur['answer'] = re.sub(r'답\s*[：:]?\s*', '', line).strip()
            elif '선지:' in line or '선지 :' in line:
                cur['choices_hint'] = re.sub(r'선지\s*[：:]?\s*', '', line).strip()
            else:
                cur['memo'] = cur.get('memo', '') + ' ' + line
    if cur:
        sparse20.append(cur)

    if sparse20:
        dicts20 = claude_supplement_sparse(2020, sparse20)
        qs20 = dicts_to_questions(2020, dicts20)
        print(f'  → {len(qs20)}문제')
        all_questions.extend(qs20)

    # ── 미분류 문제 Claude로 재분류 ──────────────────
    unclassified = [q for q in all_questions if not q.lecture_key]
    if unclassified:
        print(f'\n[재분류] 미분류 {len(unclassified)}문제 Claude 분류 중...')
        topics_str = '\n'.join(
            f'Q{q.year}-{q.num}: professor={q.professor}, '
            f'topic={q.topic}, text_preview={q.question_text[:80]}'
            for q in unclassified
        )
        resp = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=4000,
            messages=[{'role': 'user', 'content':
                f"""다음 호흡기 시험 문제들의 강의 분류 키를 JSON으로 반환하세요.
가능한 lecture_key 목록: {[k for _, k, _ in TOPIC_MAP]}

문제들:
{topics_str}

반환 형식 (JSON array): [{{"year":2021,"num":3,"lecture_key":"1217_호흡생리학"}}]
JSON만 반환하세요."""}]
        )
        try:
            arr = json.loads(
                re.search(r'\[.+\]', resp.content[0].text, re.DOTALL).group()
            )
            lk_map = {(d['year'], d['num']): d.get('lecture_key', '')
                      for d in arr if isinstance(d, dict)}
            for q in unclassified:
                lk = lk_map.get((q.year, q.num), '')
                if lk:
                    for _, key, title in TOPIC_MAP:
                        if key == lk:
                            q.lecture_key, q.lecture_title = key, title
                            break
        except Exception as e:
            print(f'  [재분류 오류] {e}')

    # ── 강의록별 그룹화 및 PDF 생성 ───────────────────
    print(f'\n[PDF 생성] 총 {len(all_questions)}문제 → 강의록별 PDF...')
    grouped: dict[str, list[Question]] = {}
    no_key = []
    for q in all_questions:
        if q.lecture_key:
            grouped.setdefault(q.lecture_key, []).append(q)
        else:
            no_key.append(q)

    for lk, qs in sorted(grouped.items()):
        lt = qs[0].lecture_title
        make_lecture_pdf(lk, lt, qs)

    if no_key:
        print(f'\n  [미분류 {len(no_key)}문제] → 미분류.pdf')
        make_lecture_pdf('미분류', '미분류 문제', no_key)

    # 결과 저장 JSON
    json_out = OUT / '_all_questions.json'
    with open(json_out, 'w', encoding='utf-8') as f:
        json.dump([asdict(q) for q in all_questions],
                  f, ensure_ascii=False, indent=2)

    print(f'\n✅ 완료: {OUT}')
    print(f'   총 {len(all_questions)}문제 / {len(grouped)}개 강의록 PDF')
    if no_key:
        print(f'   미분류 {len(no_key)}문제')


if __name__ == '__main__':
    main()
