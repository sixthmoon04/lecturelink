#!/usr/bin/env python3
"""2016, 2020 연도 재처리 + 기존 통합 PDF에 추가"""

import os, re, json
from pathlib import Path
from dataclasses import dataclass, field, asdict

import pdfplumber
import anthropic
from fpdf import FPDF, XPos, YPos

BASE   = Path('/Users/ddoli1545/Desktop/test')
EXAM   = BASE / '역대 야마'
SOL    = BASE / '역대 야마풀이'
OUT    = BASE / '강의록별_기출문제_통합'
FONT_R = str(BASE / 'SDGothicNeo-Regular.ttf')
FONT_B = str(BASE / 'SDGothicNeo-Bold.ttf')
OUT.mkdir(exist_ok=True)

client = anthropic.Anthropic()

@dataclass
class Question:
    year: int
    num: int
    professor: str
    topic: str
    lecture_key: str = ''
    lecture_title: str = ''
    question_text: str = ''
    choices: list = field(default_factory=list)
    answer: str = ''
    explanation: str = ''
    is_complete: bool = True

TOPIC_MAP = [
    (["뒷가슴벽", "종격동", "금동윤"],
     "1216_뒷가슴벽구조_종격동", "뒷가슴벽의 구조 (종격동)"),
    (["가슴벽", "흉곽 구조", "thoracic wall", "채민철"],
     "1216_가슴벽의구조", "가슴벽의 구조"),
    (["폐의 구조", "흉강", "늑막", "lung structure"],
     "1216_폐의구조", "폐의 구조"),
    (["호흡기의 해부학", "기관", "기관지", "bronchus", "bronchi", "호흡기 해부학"],
     "1216_호흡기해부학적구조", "호흡기의 해부학적 구조"),
    (["호흡상피", "조직학", "폐포세포", "type1", "type2", "surfactant", "구조와 기능"],
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
    (["정상 흉부 영상", "chest PA", "흉부 X선", "흉부 영상의학 소견 및 검사", "정상 흉부"],
     "1218_정상흉부영상의학", "정상 흉부 영상의학 소견 및 검사법"),
    (["영상의학 소견 유형", "흉부질환 영상", "결절", "공동", "간유리"],
     "1218_흉부질환영상의학소견유형분석", "흉부질환의 영상의학 소견 유형 분석"),
    (["상기도", "급성기관지염", "후비루", "비염", "상기도 질환", "김태훈"],
     "1218_상기도질환_급성기관지염", "상기도 질환과 급성기관지염"),
    (["지역사회획득폐렴", "CAP", "community"],
     "1218_지역사회획득폐렴", "지역사회획득폐렴"),
    (["병원획득폐렴", "HAP", "VAP", "흡인성 폐렴", "병원내 폐렴"],
     "1218_병원획득폐렴_흡인성폐렴", "병원획득폐렴 / 흡인성 폐렴"),
    (["치료약제 (1)", "치료약제(1)", "베타작용제", "ICS", "흡입제", "기관지확장제", "이성용"],
     "1218_1224_호흡기치료약제1", "호흡기질환의 치료약제 (1)"),
    (["폐농양", "기타 폐감염", "아스페르길루스", "진균", "곰팡이"],
     "1222_폐농양_기타폐감염", "폐농양과 기타 폐감염"),
    (["결핵의 진단", "폐결핵 진단", "tuberculosis 진단", "AFB"],
     "1222_폐결핵진단", "폐결핵의 진단"),
    (["결핵의 치료", "폐결핵 치료", "항결핵제", "INH", "rifampin", "isoniazid"],
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
    (["환기장애", "수면무호흡", "OSA", "CPAP", "수면"],
     "1224_환기장애_수면무호흡", "환기장애와 수면 무호흡"),
    (["직업성", "환경성 폐질환", "진폐증", "석면"],
     "1224_직업성환경성폐질환", "직업성 및 환경성 폐질환"),
    (["치료약제 (2)", "치료약제(2)", "진해제", "거담제", "항히스타민", "장정희"],
     "1224_호흡기치료약제2", "호흡기질환의 치료약제 (2)"),
]


def classify_topic_local(topic, professor, q_text):
    combined = (topic + ' ' + professor + ' ' + q_text[:200]).lower()
    for keywords, key, title in TOPIC_MAP:
        for kw in keywords:
            if kw.lower() in combined:
                return key, title
    return '', topic


def extract_pdf_text(path):
    try:
        with pdfplumber.open(str(path)) as pdf:
            return '\n'.join((p.extract_text() or '') for p in pdf.pages)
    except Exception as e:
        print(f'  [PDF오류] {path.name}: {e}')
        return ''


def claude_extract_chunked(year: int, raw_text: str, source_label: str, chunk_size=6000) -> list[dict]:
    """텍스트를 청크로 나눠서 Claude 호출 → 결과 병합"""
    all_results = []
    chunks = [raw_text[i:i+chunk_size] for i in range(0, len(raw_text), chunk_size)]
    print(f'  → {len(chunks)}개 청크로 분할 처리...')

    for idx, chunk in enumerate(chunks):
        print(f'  → 청크 {idx+1}/{len(chunks)} 처리 중...')
        prompt = f"""다음은 {year}년 호흡기 1차 시험 관련 문서입니다 ({source_label}, 파트 {idx+1}/{len(chunks)}).

각 문제를 다음 JSON 형식의 배열로 추출하세요:
{{
  "num": 문제번호(정수),
  "professor": "교수님 이름 (없으면 빈 문자열)",
  "topic": "강의 주제 (없으면 빈 문자열)",
  "question_text": "문제 본문 (완전한 문장으로)",
  "choices": ["1) ...", "2) ...", "3) ...", "4) ...", "5) ..."],
  "answer": "정답 번호(예: 3)",
  "explanation": "해설 내용 (없으면 빈 문자열)",
  "supplement_note": "보완한 내용이 있으면 명시, 없으면 빈 문자열"
}}

규칙:
- 문제 본문이나 선지가 불완전하면 호흡기내과 의학 지식으로 완성하세요.
- 선지가 없는 문제는 의학적으로 적합한 5개 선지를 만들어주세요.
- 정답 번호는 '1'~'5' 숫자만 사용하세요.
- 이 청크에 완전한 문제가 없으면 빈 배열 []을 반환하세요.
- 반드시 올바른 JSON 배열만 반환하고 다른 텍스트는 쓰지 마세요.

문서:
{chunk}"""

        try:
            resp = client.messages.create(
                model='claude-sonnet-4-6',
                max_tokens=16000,
                messages=[{'role': 'user', 'content': prompt}]
            )
            raw = resp.content[0].text.strip()
            # ```json ... ``` 블록 제거
            raw = re.sub(r'^```(?:json)?\s*', '', raw)
            raw = re.sub(r'\s*```$', '', raw)
            json_m = re.search(r'\[.*\]', raw, re.DOTALL)
            if json_m:
                parsed = json.loads(json_m.group())
                all_results.extend(parsed)
                print(f'     → {len(parsed)}문제 추출')
            else:
                print(f'     → 문제 없음')
        except json.JSONDecodeError as e:
            print(f'  [JSON 오류] 청크 {idx+1}: {e}')
            # 부분적으로 파싱 시도
            try:
                # 마지막 완전한 객체까지만 파싱
                raw_fixed = re.sub(r',\s*\{[^}]*$', '', json_m.group() if json_m else '[]') + ']'
                parsed = json.loads(raw_fixed)
                all_results.extend(parsed)
                print(f'     → 복구 후 {len(parsed)}문제 추출')
            except Exception:
                pass
        except Exception as e:
            print(f'  [Claude 오류] 청크 {idx+1}: {e}')

    # 중복 제거 (같은 num)
    seen = {}
    for d in all_results:
        if isinstance(d, dict) and d.get('num'):
            n = int(d['num'])
            if n not in seen:
                seen[n] = d
    return list(seen.values())


def claude_supplement_sparse_chunked(year: int, sparse_entries: list[dict]) -> list[dict]:
    """복기 메모를 청크로 나눠 Claude로 완전한 문제로 보완"""
    if not sparse_entries:
        return []

    all_results = []
    chunk_size = 10  # 메모 10개씩 처리
    chunks = [sparse_entries[i:i+chunk_size] for i in range(0, len(sparse_entries), chunk_size)]
    print(f'  → {len(sparse_entries)}개 메모, {len(chunks)}개 청크로 분할...')

    for idx, chunk in enumerate(chunks):
        print(f'  → 청크 {idx+1}/{len(chunks)} 처리 중...')
        entries_str = json.dumps(chunk, ensure_ascii=False, indent=2)
        prompt = f"""다음은 {year}년 호흡기 1차 시험 문제의 간략한 복기 메모입니다.
각 메모를 실제 시험 문제 형식으로 완전히 재구성해주세요.

복기 메모:
{entries_str}

각 항목에 대해 다음 JSON 형식으로 반환하세요:
[
  {{
    "num": 문제번호(정수),
    "professor": "교수님 이름 (알 수 없으면 빈 문자열)",
    "topic": "주제",
    "question_text": "완전한 문제 본문 (환자 증례 포함)",
    "choices": ["1) ...", "2) ...", "3) ...", "4) ...", "5) ..."],
    "answer": "정답 번호(숫자만, 예: 3)",
    "explanation": "해설",
    "supplement_note": "보완 내용 설명"
  }}
]

규칙:
- 복기 메모의 핵심 정보(증상, 검사 수치, 정답)는 반드시 유지하세요.
- 문제는 호흡기내과 임상 시험 스타일로 작성하세요.
- 반드시 올바른 JSON 배열만 반환하세요."""

        try:
            resp = client.messages.create(
                model='claude-sonnet-4-6',
                max_tokens=16000,
                messages=[{'role': 'user', 'content': prompt}]
            )
            raw = resp.content[0].text.strip()
            raw = re.sub(r'^```(?:json)?\s*', '', raw)
            raw = re.sub(r'\s*```$', '', raw)
            json_m = re.search(r'\[.*\]', raw, re.DOTALL)
            if json_m:
                parsed = json.loads(json_m.group())
                all_results.extend(parsed)
                print(f'     → {len(parsed)}문제 재구성')
        except json.JSONDecodeError as e:
            print(f'  [JSON 오류] 청크 {idx+1}: {e}')
        except Exception as e:
            print(f'  [Claude 오류] 청크 {idx+1}: {e}')

    return all_results


def dicts_to_questions(year, dicts):
    result = []
    for d in dicts:
        if not isinstance(d, dict):
            continue
        topic = str(d.get('topic', ''))
        prof  = str(d.get('professor', ''))
        q_txt = str(d.get('question_text', ''))
        lk, lt = classify_topic_local(topic, prof, q_txt)
        q = Question(
            year=year, num=int(d.get('num', 0)),
            professor=prof, topic=topic,
            lecture_key=lk, lecture_title=lt,
            question_text=q_txt,
            choices=d.get('choices', []),
            answer=str(d.get('answer', '')),
            explanation=str(d.get('explanation', '')),
            is_complete=not bool(d.get('supplement_note', '')),
        )
        if d.get('supplement_note'):
            q.supplement_note = d['supplement_note']
        result.append(q)
    return result


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

        content_w = PAGE_W - 2 * MARGIN
        self.set_font('K', 'B', 10)
        self.multi_cell(content_w, 6.5, f'Q{q.num}. {q.question_text}',
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

        self.set_font('K', '', 10)
        for ch in q.choices:
            self.multi_cell(content_w, 6, f'   {ch}',
                            new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(3)

        self.set_font('K', 'B', 10)
        self.set_fill_color(239, 246, 255)
        self.set_draw_color(191, 219, 254)
        self.set_line_width(0.3)
        self.cell(content_w, 8, f'정답: {q.answer}', border=1, fill=True,
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

        if q.explanation:
            self.set_font('K', 'B', 9)
            self.set_text_color(30, 64, 175)
            self.cell(0, 7, '해설', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.set_text_color(0)
            self.set_font('K', '', 9.5)
            self.set_fill_color(248, 250, 252)
            self.multi_cell(content_w, 6, q.explanation, fill=True,
                            new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(6)
        self.set_draw_color(241, 245, 249)
        self.line(MARGIN, self.get_y(), PAGE_W - MARGIN, self.get_y())
        self.ln(4)


def make_lecture_pdf(lecture_key, lecture_title, questions):
    if not questions:
        return
    pdf = KoreanPDF()
    pdf._lect_title = lecture_title

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
             f'역대 기출문제  |  {", ".join(map(str,years))}년  |  총 {len(questions)}문제',
             align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0)

    for q in sorted(questions, key=lambda x: (x.year, x.num)):
        pdf.add_page()
        pdf.question_block(q)

    out_path = OUT / f'{lecture_key}.pdf'
    pdf.output(str(out_path))
    print(f'  ✓ {out_path.name}  ({len(questions)}문제, {years[0]}~{years[-1]}년)')


def main():
    # ── 기존 JSON 로드 ─────────────────────────────────
    json_path = OUT / '_all_questions.json'
    existing_qs = []
    if json_path.exists():
        with open(json_path, encoding='utf-8') as f:
            data = json.load(f)
        for d in data:
            q = Question(**{k: d[k] for k in Question.__dataclass_fields__ if k in d})
            existing_qs.append(q)
        print(f'기존 {len(existing_qs)}문제 로드됨')

    new_qs = []

    # ── 2016 풀이 (청크 방식) ─────────────────────────
    print('\n[2016] 풀이 파싱 (Claude 청크)...')
    t16 = extract_pdf_text(SOL / '2016 호흡기학 1차 풀이.pdf')
    print(f'  텍스트 길이: {len(t16)}자')
    dicts16 = claude_extract_chunked(2016, t16, '2016 풀이')
    qs16 = dicts_to_questions(2016, dicts16)
    print(f'  → {len(qs16)}문제')
    new_qs.extend(qs16)

    # ── 2020 복기 (청크 방식) ─────────────────────────
    print('\n[2020] 복기 보완 (Claude 청크)...')
    t20 = extract_pdf_text(EXAM / '2020 호흡기학 1차 복기.pdf')
    print(f'  텍스트 길이: {len(t20)}자')

    # 복기 메모 파싱
    sparse20 = []
    lines = [l.strip() for l in t20.split('\n') if l.strip()]
    cur = {}
    for line in lines:
        nm = re.match(r'^(\d+)[.．]\s+(.+)', line)
        if nm:
            if cur:
                sparse20.append(cur)
            cur = {'num': int(nm.group(1)), 'memo': nm.group(2), 'answer': '', 'choices_hint': ''}
        elif cur:
            if re.search(r'답\s*[：:]', line):
                cur['answer'] = re.sub(r'답\s*[：:]?\s*', '', line).strip()
            elif re.search(r'선지\s*[：:]', line):
                cur['choices_hint'] = re.sub(r'선지\s*[：:]?\s*', '', line).strip()
            else:
                cur['memo'] = cur.get('memo', '') + ' ' + line
    if cur:
        sparse20.append(cur)

    print(f'  → {len(sparse20)}개 복기 메모 발견')
    if sparse20:
        dicts20 = claude_supplement_sparse_chunked(2020, sparse20)
        qs20 = dicts_to_questions(2020, dicts20)
        print(f'  → {len(qs20)}문제')
        new_qs.extend(qs20)

    if not new_qs:
        print('\n추가된 문제가 없습니다.')
        return

    # ── 기존 문제와 합치기 ─────────────────────────────
    # 중복 제거: (year, num) 기준
    existing_keys = {(q.year, q.num) for q in existing_qs}
    added = [q for q in new_qs if (q.year, q.num) not in existing_keys]
    print(f'\n새로 추가: {len(added)}문제 (중복 제외)')

    all_qs = existing_qs + added

    # ── 영향받는 강의록 PDF 재생성 ────────────────────
    affected_keys = {q.lecture_key for q in added if q.lecture_key}
    print(f'\n[PDF 재생성] {len(affected_keys)}개 강의록...')

    grouped = {}
    for q in all_qs:
        if q.lecture_key:
            grouped.setdefault(q.lecture_key, []).append(q)

    for lk in sorted(affected_keys):
        qs = grouped.get(lk, [])
        lt = qs[0].lecture_title if qs else lk
        make_lecture_pdf(lk, lt, qs)

    # 미분류 처리
    no_key = [q for q in added if not q.lecture_key]
    if no_key:
        print(f'\n미분류 {len(no_key)}문제:')
        for q in no_key:
            print(f'  {q.year}년 Q{q.num}: {q.topic} / {q.question_text[:50]}')
        all_no_key = [q for q in all_qs if not q.lecture_key]
        make_lecture_pdf('미분류', '미분류 문제', all_no_key)

    # ── JSON 업데이트 ──────────────────────────────────
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump([asdict(q) for q in all_qs], f, ensure_ascii=False, indent=2)

    print(f'\n✅ 완료: 총 {len(all_qs)}문제')
    print(f'   (기존 {len(existing_qs)} + 신규 {len(added)})')


if __name__ == '__main__':
    main()
