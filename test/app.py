#!/usr/bin/env python3
"""
호흡기 강의록별 기출문제 뷰어 — Flask 로컬 서버
- 강의록 버튼: 강의록별_기출문제/ (강의록+2025 문제)
- 기출 버튼: 인터랙티브 HTML 뷰어 (선지 클릭·정답 토글)
"""

import io, os, json, re, unicodedata
from flask import Flask, render_template_string, send_file, abort, jsonify

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
PDF_DIR_LEC = os.path.join(BASE_DIR, "강의록별_기출문제")
PDF_DIR_INT = os.path.join(BASE_DIR, "강의록별_기출문제_통합")
LECTURE_DIR = os.path.join(BASE_DIR, "호흡기 (1)", "호흡기 (1) 강의록")
JSON_PATH   = os.path.join(PDF_DIR_INT, "_all_questions.json")
IMG_DIR     = os.path.join(BASE_DIR, "static", "images")

app = Flask(__name__, static_folder=os.path.join(BASE_DIR, "static"))

# lecture_key → (date_label, professor, [lecture_pdf_files])
LECTURE_INFO = {
    "1216_가슴벽의구조":          ("12/16", "채민철",  ["1216 3교시 폐의 구조 (채민철).pdf"]),
    "1216_뒷가슴벽구조_종격동":   ("12/16", "금동윤",  ["1216 7교시 해부학부분(종격동) (금동윤).pdf"]),
    "1216_폐의구조":               ("12/16", "채민철",  ["1216 4교시 폐의 구조 (채민철).pdf"]),
    "1216_호흡기해부학적구조":     ("12/16", "황일선",  ["1216 5교시 호흡기의 구조와 기능 1 (황일선).pdf"]),
    "1216_호흡상피조직학적구조와기능": ("12/16", "황일선", [
        "1216 5교시 호흡기의 구조와 기능 1 (황일선).pdf",
        "1216 6교시 구조와 기능2 (황일선).pdf",
    ]),
    "1217_호흡생리학":             ("12/17", "배재훈",  ["1217 1,2교시 호흡기(호흡생리학) (배재훈).pdf"]),
    "1217_동맥혈가스분석_저산소혈증": ("12/17", "박재석", ["1217 3교시 동맥혈가스분석 저산소혈증(박재석).pdf"]),
    "1217_폐기능검사":             ("12/17", "김현정",  ["1217 4교시 폐기능검사 (김현정).pdf"]),
    "1218_호흡기질환주요증상_진찰및진단방법": ("12/18", "김현정", [
        "1218 1교시 호흡기 질환의 주요 증상 (김현정).pdf",
        "1218 2교시 호흡기 진찰 및 진단 방법 (김현정).pdf",
    ]),
    "1218_정상흉부영상의학":       ("12/18", "홍정희",  ["1218 4교시 호흡기_흉부질환의 영상의학 소견 유형분석(홍정희).pdf"]),
    "1218_흉부질환영상의학소견유형분석": ("12/18", "홍정희", ["1218 4교시 호흡기_흉부질환의 영상의학 소견 유형분석(홍정희).pdf"]),
    "1218_상기도질환_급성기관지염": ("12/18", "김태훈", ["1218 5교시 상기도 질환과 급성기관지염 (김태훈).pdf"]),
    "1218_지역사회획득폐렴":       ("12/18", "김미애",  ["1218 6교시 지역사회획득폐렴 (김미애).pdf"]),
    "1218_병원획득폐렴_흡인성폐렴": ("12/18", "김미애", ["1218 7교시 병원 획득 폐렴, 흡인성 폐렴(김미애).pdf"]),
    "1218_1224_호흡기치료약제1":   ("12/18", "이성용",  [
        "1218 3교시 호흡기질환의 치료약제 (1) (이성용).pdf",
        "1224 3교시 호흡기질환의 치료약제 (1) (이성용).pdf",
    ]),
    "1222_폐농양_기타폐감염":      ("12/22", "김미애",  ["1222 1교시 폐농양, 기타 폐감염 (김미애).pdf"]),
    "1222_폐결핵진단":             ("12/22", "김미애",  ["1222 2교시 결핵의 진단(김미애).pdf"]),
    "1222_폐결핵치료":             ("12/22", "김미애",  ["1222 3교시 결핵의 치료(김미애).pdf"]),
    "1222_기관지확장증":           ("12/22", "박순효",  ["1222 4교시 기관지확장증(박순효).pdf"]),
    "1223_폐색전증":               ("12/23", "김태훈",  [
        "1223 1교시 폐색전증의 임상소견과 진단 치료(김태훈).pdf",
        "1223 2교시 폐색전증case (김태훈).pdf",
    ]),
    "1223_천식_진단및치료":        ("12/23", "김현정",  [
        "1223 3교시 천식 진단 (김현정).pdf",
        "1223 4교시 천식의 치료 (김현정).pdf",
    ]),
    "1223_COPD":                   ("12/23", "김미애",  [
        "1223 5교시 COPD 진단 (김미애).pdf",
        "1223 6교시 COPD치료 (김미애).pdf",
    ]),
    "1224_폐병리학개요":           ("12/24", "황일선",  ["1224 1교시 호흡기_TBL1_폐 병리학 개요 (황일선).pdf"]),
    "1224_감염성폐질환":           ("12/24", "황일선",  ["1224 2교시 감염성폐질환(황일선).pdf"]),
    "1224_기도간질성폐질환_폐부종_폐색전증영상의학": ("12/24", "홍정희", [
        "1224 7교시 폐렴의 영상의학(홍정희).pdf",
        "1224 8교시 기도질환과 폐부종과 폐색전증의 영상의학(홍정희).pdf",
    ]),
    "1224_환기장애_수면무호흡":    ("12/24", "김태훈",  ["1224 5교시 환기장애와 수면 무호흡 (김태훈).pdf"]),
    "1224_직업성환경성폐질환":     ("12/24", "김태훈",  ["1224 6교시 직업성 및 환경성 폐질환(김태훈).pdf"]),
    "1224_호흡기치료약제2":        ("12/24", "장정희",  ["1224 4교시 호흡기질환의 치료약제(2) (장정희).pdf"]),
    "미분류":                       ("기타",  "-",       []),
}


# ── 유틸 ─────────────────────────────────────────────────────────────────

def nfc(s):
    return unicodedata.normalize("NFC", s)


def lecture_file_path(fname):
    target = nfc(fname)
    for f in os.listdir(LECTURE_DIR):
        if nfc(f) == target:
            return os.path.join(LECTURE_DIR, f)
    return None


def compute_lecture_pages(lecture_filenames):
    from pypdf import PdfReader
    total = 0
    for lf in lecture_filenames:
        p = lecture_file_path(lf)
        if p:
            try:
                total += len(PdfReader(p).pages)
            except Exception:
                pass
    return total


def build_meta():
    from pypdf import PdfReader
    lec_stats = {}
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, encoding='utf-8') as f:
            qs = json.load(f)
        for q in qs:
            lk = q.get('lecture_key', '')
            if not lk:
                continue
            if lk not in lec_stats:
                lec_stats[lk] = {'years': set(), 'count': 0, 'title': q.get('lecture_title', lk)}
            lec_stats[lk]['years'].add(q.get('year', 0))
            lec_stats[lk]['count'] += 1

    result = []
    for lk, (date, prof, lec_files) in LECTURE_INFO.items():
        int_path = os.path.join(PDF_DIR_INT, lk + '.pdf')
        if not os.path.exists(int_path):
            continue
        stats     = lec_stats.get(lk, {'years': set(), 'count': 0, 'title': lk})
        years     = sorted(stats['years'], reverse=True)
        old_path  = os.path.join(PDF_DIR_LEC, lk + '.pdf')
        has_old   = os.path.exists(old_path)
        lec_pages = 0
        old_total = 0
        if has_old:
            try:
                old_total = len(PdfReader(old_path).pages)
                lec_pages = compute_lecture_pages(lec_files)
            except Exception:
                pass
        result.append({
            'key':           lk,
            'file':          lk + '.pdf',
            'date':          date,
            'title':         stats['title'],
            'professor':     prof,
            'years':         years,
            'q_count':       stats['count'],
            'has_lecture':   has_old and lec_pages > 0,
            'lecture_pages': lec_pages,
            'old_total':     old_total,
        })

    DATE_ORDER = {'12/16': 0, '12/17': 1, '12/18': 2, '12/22': 3,
                  '12/23': 4, '12/24': 5, '기타': 99}
    result.sort(key=lambda m: (DATE_ORDER.get(m['date'], 50), m['key']))
    return result


def build_question_index():
    """lecture_key → sorted question list, with image paths pre-computed"""
    if not os.path.exists(JSON_PATH):
        return {}
    with open(JSON_PATH, encoding='utf-8') as f:
        raw = json.load(f)

    # 존재하는 이미지 파일 목록 미리 캐시
    img_files = set(os.listdir(IMG_DIR)) if os.path.isdir(IMG_DIR) else set()

    index = {}
    for q in raw:
        lk = q.get('lecture_key', '')
        if not lk:
            continue
        year, num = q.get('year', 0), q.get('num', 0)
        # 해당 문제의 이미지 파일 목록
        imgs = sorted(
            f for f in img_files
            if f.startswith(f'{year}_Q{num}_')
        )
        q['_images'] = imgs
        q['_real_choices'] = parse_real_choices(q.get('choices', []))
        q['_answer_num']   = parse_answer_num(q.get('answer', ''))
        index.setdefault(lk, []).append(q)

    # 최신 연도 먼저, 같은 연도면 문제번호 순
    for lk in index:
        index[lk].sort(key=lambda x: (-x['year'], x['num']))
    return index


def parse_real_choices(choices_raw: list) -> list:
    """choices 배열에서 실제 보기(1~5)만 추출 (최초 등장 기준)"""
    real = {}
    for item in choices_raw:
        s = item.strip()
        m = re.match(r'^(\d+)[)．]', s)
        if m:
            n = int(m.group(1))
            if 1 <= n <= 5 and n not in real:
                real[n] = s
    return [real[i] for i in sorted(real.keys())]


def parse_answer_num(answer_str: str) -> str:
    """'4)' → '4', '4번' → '4', 이미 '4'이면 그대로"""
    m = re.match(r'^(\d+)', str(answer_str).strip())
    return m.group(1) if m else answer_str.strip()


print("메타데이터 계산 중...", flush=True)
META          = build_meta()
META_BY_KEY   = {m['key']: m for m in META}
QUESTION_IDX  = build_question_index()
print(f"완료 ({len(META)}개 강의, {sum(len(v) for v in QUESTION_IDX.values())}문제)", flush=True)


# ── 메인 페이지 HTML (React CDN) ────────────────────────────────────────
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>호흡기 기출문제 뷰어</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
  <style>
    :root { --sidebar-w:360px; --header-h:56px; }
    body { background:#f1f5f9; overflow:hidden; height:100dvh; margin:0; font-family:'Noto Sans KR',sans-serif; }

    /* Header */
    .app-header {
      height:var(--header-h); display:flex; align-items:center; padding:0 1.5rem; gap:1rem; flex-shrink:0;
      background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 100%);
      border-bottom:1px solid rgba(255,255,255,.08); box-shadow:0 2px 12px rgba(0,0,0,.35); z-index:1040;
    }
    .app-header .brand { font-size:.95rem; font-weight:700; color:#fff; }
    .app-header .brand span { color:#60a5fa; }
    .app-header .subtitle { font-size:.72rem; color:#94a3b8; margin-top:1px; }
    .stat-pill {
      font-size:.7rem; font-weight:600; background:rgba(255,255,255,.1);
      border:1px solid rgba(255,255,255,.15); color:#e2e8f0; padding:3px 10px; border-radius:20px;
    }

    /* Sidebar */
    .sidebar-panel {
      width:var(--sidebar-w); height:calc(100dvh - var(--header-h));
      display:flex; flex-direction:column; background:#fff;
      border-right:1px solid #e2e8f0; flex-shrink:0; overflow:hidden;
    }
    .sidebar-top { padding:14px 14px 0; background:#f8fafc; border-bottom:1px solid #e2e8f0; flex-shrink:0; }
    .sidebar-top .title-row { display:flex; align-items:center; justify-content:space-between; padding-bottom:10px; }
    .sidebar-top .title-row h6 { font-size:.75rem; font-weight:700; text-transform:uppercase; letter-spacing:.06em; color:#64748b; margin:0; }
    .sidebar-scroll { overflow-y:auto; flex:1; }

    /* Search */
    .search-box { background:#fff; border:1px solid #e2e8f0; border-radius:8px; padding:7px 12px; display:flex; align-items:center; gap:8px; margin-bottom:10px; }
    .search-box i { color:#94a3b8; font-size:.9rem; flex-shrink:0; }
    .search-box input { border:none; outline:none; font-size:.82rem; background:transparent; color:#1e293b; width:100%; }
    .search-box input::placeholder { color:#b0bec5; }

    /* Sort bar */
    .sort-bar { display:flex; gap:6px; padding-bottom:12px; }
    .sort-btn { flex:1; padding:5px 0; font-size:.75rem; font-weight:700; border-radius:8px; border:1.5px solid #e2e8f0; background:#f8fafc; color:#475569; cursor:pointer; transition:all .15s; }
    .sort-btn.active { background:#1e293b; color:#fff; border-color:#1e293b; }
    .sort-btn:not(.active):hover { background:#f1f5f9; }

    /* Date header */
    .date-header {
      padding:6px 14px 4px; font-size:.67rem; font-weight:800; text-transform:uppercase;
      letter-spacing:.08em; color:#94a3b8; background:#f8fafc; border-bottom:1px solid #f1f5f9;
      position:sticky; top:0; z-index:2; display:flex; align-items:center; gap:6px;
    }
    .date-header::before { content:''; display:block; width:6px; height:6px; border-radius:50%; background:#cbd5e1; }

    /* Lecture item */
    .lecture-item { display:flex; align-items:stretch; border-bottom:1px solid #f1f5f9; transition:background .12s; position:relative; }
    .lecture-item::before { content:''; position:absolute; left:0; top:0; bottom:0; width:3px; background:transparent; transition:background .15s; }
    .lecture-item:hover { background:#f8fafc; }
    .lecture-item.active-lecture::before  { background:#3b82f6; }
    .lecture-item.active-lecture          { background:#eff6ff; }
    .lecture-item.active-questions::before{ background:#22c55e; }
    .lecture-item.active-questions        { background:#f0fdf4; }
    .item-info { flex:1; padding:10px 8px 10px 15px; min-width:0; }
    .item-title { font-size:.82rem; font-weight:600; color:#1e293b; line-height:1.35; margin-bottom:5px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .item-meta { display:flex; align-items:center; gap:5px; flex-wrap:wrap; }
    .prof-badge { font-size:.67rem; font-weight:600; background:#f1f5f9; color:#475569; padding:1px 7px; border-radius:20px; border:1px solid #e2e8f0; white-space:nowrap; }
    .year-chip { font-size:.62rem; font-weight:700; background:#dbeafe; color:#1d4ed8; padding:1px 6px; border-radius:20px; white-space:nowrap; }
    .count-chip { font-size:.62rem; font-weight:700; background:#dcfce7; color:#15803d; padding:1px 6px; border-radius:20px; white-space:nowrap; }
    .item-actions { display:flex; flex-direction:column; border-left:1px solid #f1f5f9; flex-shrink:0; width:58px; }
    .action-btn { flex:1; border:none; background:transparent; cursor:pointer; font-size:.65rem; font-weight:700; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:3px; transition:background .12s,color .12s; padding:0; }
    .action-btn i { font-size:.95rem; }
    .action-btn.lec-btn { color:#3b82f6; border-bottom:1px solid #f1f5f9; }
    .action-btn.que-btn { color:#16a34a; }
    .action-btn.lec-btn:hover { background:#eff6ff; }
    .action-btn.que-btn:hover { background:#f0fdf4; }
    .action-btn.lec-btn.active { background:#3b82f6; color:#fff; }
    .action-btn.que-btn.active { background:#22c55e; color:#fff; }

    /* Viewer */
    .viewer-area { flex:1; display:flex; flex-direction:column; overflow:hidden; min-width:0; }
    .viewer-bar { padding:9px 18px; background:#fff; border-bottom:1px solid #e2e8f0; display:flex; align-items:center; gap:10px; flex-shrink:0; box-shadow:0 1px 4px rgba(0,0,0,.06); }
    .vb-title { font-size:.88rem; font-weight:700; color:#1e293b; flex:1; min-width:0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .mode-pill { font-size:.7rem; font-weight:700; padding:3px 10px; border-radius:20px; white-space:nowrap; }
    .mode-pill.lec { background:#dbeafe; color:#1d4ed8; }
    .mode-pill.que { background:#dcfce7; color:#15803d; }
    .info-pill { font-size:.7rem; color:#64748b; background:#f1f5f9; padding:3px 9px; border-radius:20px; white-space:nowrap; border:1px solid #e2e8f0; }
    .viewer-frame { flex:1; overflow:hidden; }
    .viewer-frame iframe { width:100%; height:100%; border:none; display:block; }
    .viewer-placeholder { flex:1; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:16px; color:#94a3b8; background:radial-gradient(ellipse at 50% 60%,#f0f9ff 0%,#f1f5f9 70%); }
    .placeholder-icon { width:80px; height:80px; border-radius:20px; background:linear-gradient(135deg,#3b82f6,#6366f1); display:flex; align-items:center; justify-content:center; font-size:2.2rem; box-shadow:0 8px 24px rgba(99,102,241,.25); }
    .placeholder-title { font-size:1rem; font-weight:700; color:#475569; }
    .placeholder-sub { font-size:.82rem; color:#94a3b8; text-align:center; }

    /* Top tab nav */
    .top-tab-bar { display:flex; gap:4px; padding:10px 16px; background:#fff; border-bottom:1px solid #e2e8f0; flex-shrink:0; }
    .tab-btn { padding:6px 16px; border-radius:8px; font-size:.82rem; font-weight:700; border:1.5px solid #e2e8f0; background:#f8fafc; color:#475569; cursor:pointer; transition:all .15s; white-space:nowrap; }
    .tab-btn:hover:not(.active) { background:#f1f5f9; color:#334155; }
    .tab-btn.active { background:#1e293b; color:#fff; border-color:#1e293b; }

    /* Question scroll */
    .question-scroll { flex:1; overflow-y:auto; padding:20px 16px 60px; }
    .page-title { font-size:1.1rem; font-weight:800; color:#1e293b; margin-bottom:4px; }
    .page-sub   { font-size:.82rem; color:#64748b; margin-bottom:24px; }

    /* Question card */
    .q-card { background:#fff; border-radius:12px; box-shadow:0 1px 4px rgba(0,0,0,.08); margin-bottom:20px; overflow:hidden; }
    .q-header { padding:10px 16px; background:linear-gradient(135deg,#1e40af,#3b82f6); display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
    .q-year-badge { font-size:.75rem; font-weight:800; color:#fff; background:rgba(255,255,255,.18); padding:2px 10px; border-radius:20px; }
    .q-topic { font-size:.72rem; color:#bfdbfe; }
    .q-body  { padding:16px; }
    .q-text  { font-size:.92rem; line-height:1.75; color:#1e293b; white-space:pre-wrap; margin-bottom:14px; }
    .choices { display:flex; flex-direction:column; gap:7px; margin-bottom:16px; }
    .choice-btn { width:100%; text-align:left; padding:9px 14px; border-radius:8px; border:1.5px solid #e2e8f0; background:#f8fafc; font-size:.88rem; color:#334155; cursor:pointer; transition:all .15s; white-space:pre-wrap; line-height:1.55; }
    .choice-btn:hover:not(.correct):not(.wrong):not(.dimmed) { background:#f1f5f9; border-color:#94a3b8; }
    .choice-btn.correct { background:#dcfce7; border-color:#22c55e; color:#15803d; font-weight:700; }
    .choice-btn.wrong   { background:#fee2e2; border-color:#ef4444; color:#b91c1c; }
    .choice-btn.dimmed  { opacity:.45; }
    .reveal-wrap { display:flex; justify-content:flex-end; }
    .reveal-btn { font-size:.82rem; font-weight:700; padding:7px 18px; border-radius:8px; border:1.5px solid #a5b4fc; background:#eef2ff; color:#4338ca; cursor:pointer; transition:all .15s; }
    .reveal-btn:hover { background:#e0e7ff; }
    .reveal-btn.revealed { background:#4338ca; color:#fff; border-color:#4338ca; }
    .answer-panel { margin-top:14px; padding:14px; background:#f0fdf4; border-radius:10px; border:1.5px solid #86efac; }
    .answer-line { font-size:.9rem; font-weight:800; color:#15803d; margin-bottom:8px; }
    .explanation { font-size:.85rem; line-height:1.75; color:#1e293b; white-space:pre-wrap; }
    .q-images { display:flex; flex-wrap:wrap; gap:10px; margin-bottom:12px; }
    .q-images img { max-width:100%; max-height:280px; border-radius:8px; border:1px solid #e2e8f0; object-fit:contain; cursor:pointer; }

    /* Lightbox */
    .lightbox { display:none; position:fixed; inset:0; background:rgba(0,0,0,.85); z-index:9999; align-items:center; justify-content:center; }
    .lightbox.show { display:flex; }
    .lightbox img { max-width:92vw; max-height:90vh; border-radius:8px; }
    .lightbox-close { position:fixed; top:16px; right:20px; color:#fff; font-size:2rem; cursor:pointer; background:none; border:none; line-height:1; }

    /* Step type sub-bar */
    .step-type-bar { display:flex; gap:6px; padding:10px 16px; background:#f8fafc; border-bottom:1px solid #e2e8f0; flex-shrink:0; align-items:center; }
    .step-type-btn { padding:5px 14px; border-radius:20px; font-size:.78rem; font-weight:700; border:1.5px solid #e2e8f0; background:#fff; color:#475569; cursor:pointer; transition:all .15s; white-space:nowrap; }
    .step-type-btn.active { background:#7c3aed; color:#fff; border-color:#7c3aed; }
    .step-type-btn:hover:not(.active) { background:#f1f5f9; }

    /* Guide */
    .guide-section { margin-bottom:24px; }
    .guide-section-title { font-size:.82rem; font-weight:800; padding:8px 14px; background:linear-gradient(135deg,#1e40af,#3b82f6); color:#fff; border-radius:8px; margin-bottom:10px; }
    .guide-concept-list { display:flex; flex-direction:column; gap:6px; }
    .guide-concept-item { padding:8px 14px; background:#fff; border-radius:8px; border:1.5px solid #e2e8f0; font-size:.84rem; color:#334155; display:flex; align-items:center; gap:8px; }
    .rank-badge { font-size:.7rem; font-weight:800; background:#dbeafe; color:#1d4ed8; padding:2px 8px; border-radius:20px; white-space:nowrap; }
    .guide-freq-item { padding:10px 14px; background:#fff; border-radius:8px; border:1.5px solid #e2e8f0; font-size:.84rem; color:#334155; margin-bottom:8px; }

    /* Minor cards */
    .minor-card { background:#fff; border-radius:12px; box-shadow:0 1px 4px rgba(0,0,0,.08); margin-bottom:16px; overflow:hidden; }
    .minor-card-header { padding:10px 16px; background:linear-gradient(135deg,#065f46,#10b981); display:flex; align-items:center; justify-content:space-between; gap:10px; }
    .minor-card-title { font-size:.85rem; font-weight:800; color:#fff; flex:1; min-width:0; }
    .minor-card-badge { font-size:.7rem; font-weight:700; background:rgba(255,255,255,.2); color:#fff; padding:2px 8px; border-radius:20px; white-space:nowrap; }
    .minor-card-body { padding:14px 16px; }
    .minor-key-point { font-size:.83rem; line-height:1.7; color:#1e293b; padding:6px 10px; background:#f0fdf4; border-radius:6px; border-left:3px solid #22c55e; margin-bottom:6px; }
    .minor-mnemonic { font-size:.8rem; line-height:1.65; color:#6d28d9; background:#f5f3ff; padding:8px 12px; border-radius:6px; border-left:3px solid #8b5cf6; margin-top:8px; }
  </style>
</head>
<body>
  <div id="root"></div>

  <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
  <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  <script type="text/babel">
    const { useState, useEffect, useMemo } = React;
    const DATE_ORDER = {'12/16':0,'12/17':1,'12/18':2,'12/22':3,'12/23':4,'12/24':5,'기타':99};
    const TABS = ['강의록','기출','학습 가이드','3step','지엽'];
    const STEP_TYPES = ['야마형','심화형','지엽형'];

    /* ── Util: rotate choices by 1 position to vary answer positions ── */
    function rotateChoices(questions) {
      return questions.map(q => {
        const choices = q._real_choices || [];
        if (choices.length < 2) return q;
        const ansNum = parseInt(q._answer_num, 10) || 1;
        const ansText = (choices[ansNum - 1] || '').replace(/^\d+[)．]\s*/, '');
        const rotated = [choices[choices.length - 1], ...choices.slice(0, -1)];
        const renumbered = rotated.map((ch, i) => `${i+1}) ${ch.replace(/^\d+[)．]\s*/, '')}`);
        let newAns = ansNum;
        renumbered.forEach((ch, i) => { if (ch.replace(/^\d+[)．]\s*/, '') === ansText) newAns = i + 1; });
        return {...q, _real_choices: renumbered, _answer_num: String(newAns)};
      });
    }

    /* ── App ── */
    function App() {
      const [lectures, setLectures] = useState([]);
      const [selected, setSelected] = useState(null);
      useEffect(() => {
        fetch('/api/lectures').then(r => r.json()).then(setLectures).catch(() => {});
      }, []);
      const totalQ = lectures.reduce((s, l) => s + l.q_count, 0);
      return (
        <div style={{display:'flex',flexDirection:'column',height:'100dvh',overflow:'hidden'}}>
          <header className="app-header">
            <div style={{flex:1}}>
              <div className="brand">🫁 <span>호흡기</span> 기출문제 뷰어</div>
              <div className="subtitle">2015 – 2025 역대 기출 · 강의록별 분류</div>
            </div>
            <div style={{display:'flex',gap:8}}>
              <span className="stat-pill"><i className="bi bi-book me-1"/>{lectures.length}강의</span>
              <span className="stat-pill"><i className="bi bi-question-circle me-1"/>{totalQ}문제</span>
            </div>
          </header>
          <div style={{display:'flex',flex:1,overflow:'hidden'}}>
            <Sidebar lectures={lectures} selectedKey={selected && selected.key} onSelect={setSelected} />
            <main className="viewer-area">
              {!selected && <Placeholder />}
              {selected && <LectureViewer lecture={selected} />}
            </main>
          </div>
        </div>
      );
    }

    /* ── Sidebar ── */
    function Sidebar({lectures, selectedKey, onSelect}) {
      const [query, setQuery] = useState('');
      const [sortMode, setSortMode] = useState('date');
      const filtered = useMemo(() => {
        const q = query.trim().toLowerCase();
        return lectures.filter(l => !q || l.title.toLowerCase().includes(q) || l.professor.toLowerCase().includes(q));
      }, [lectures, query]);
      const grouped = useMemo(() => {
        if (sortMode === 'date') {
          const map = {};
          filtered.forEach(l => { const k = l.date||'기타'; if(!map[k])map[k]=[]; map[k].push(l); });
          return Object.entries(map).sort(([a],[b]) => (DATE_ORDER[a]||50) - (DATE_ORDER[b]||50));
        } else {
          const sorted = [...filtered].sort((a,b) => a.professor.localeCompare(b.professor,'ko'));
          const map = {};
          sorted.forEach(l => { const k = l.professor||'-'; if(!map[k])map[k]=[]; map[k].push(l); });
          return Object.entries(map);
        }
      }, [filtered, sortMode]);
      return (
        <aside className="sidebar-panel">
          <div className="sidebar-top">
            <div className="title-row">
              <h6>강의 목록</h6>
              <span className="badge bg-primary-subtle text-primary rounded-pill">{lectures.length}</span>
            </div>
            <div className="search-box">
              <i className="bi bi-search"/>
              <input type="text" placeholder="제목 또는 교수명 검색…" value={query} onChange={e => setQuery(e.target.value)} />
            </div>
            <div className="sort-bar">
              <button className={'sort-btn'+(sortMode==='date'?' active':'')} onClick={() => setSortMode('date')}>날짜별</button>
              <button className={'sort-btn'+(sortMode==='prof'?' active':'')} onClick={() => setSortMode('prof')}>교수별</button>
            </div>
          </div>
          <div className="sidebar-scroll">
            {grouped.map(([groupKey, items]) => (
              <div key={groupKey}>
                <div className="date-header">{groupKey}</div>
                {items.map(lecture => (
                  <LectureItem key={lecture.key} lecture={lecture} isActive={selectedKey === lecture.key} onSelect={onSelect} />
                ))}
              </div>
            ))}
          </div>
        </aside>
      );
    }

    function LectureItem({lecture, isActive, onSelect}) {
      const yrs = lecture.years;
      const yearsLabel = yrs && yrs.length
        ? yrs.length === 1 ? yrs[0]+'년' : yrs[yrs.length-1]+'–'+yrs[0]+'년'
        : null;
      return (
        <div className={'lecture-item'+(isActive?' active-questions':'')} style={{cursor:'pointer'}} onClick={() => onSelect(lecture)}>
          <div className="item-info" style={{padding:'10px 15px'}}>
            <div className="item-title" title={lecture.title}>{lecture.title}</div>
            <div className="item-meta">
              <span className="prof-badge"><i className="bi bi-person-fill me-1"/>{lecture.professor}</span>
              {yearsLabel && <span className="year-chip">{yearsLabel}</span>}
              <span className="count-chip">{lecture.q_count}문제</span>
            </div>
          </div>
        </div>
      );
    }

    /* ── LectureViewer: unified tab container ── */
    function LectureViewer({lecture}) {
      const [activeTab, setActiveTab] = useState('기출');
      const [stepType, setStepType] = useState('야마형');
      const [questions, setQuestions] = useState([]);
      const [loading, setLoading] = useState(true);
      useEffect(() => {
        setLoading(true);
        setQuestions([]);
        setActiveTab('기출');
        setStepType('야마형');
        fetch('/api/questions/'+encodeURIComponent(lecture.key))
          .then(r => r.json())
          .then(d => { setQuestions(d); setLoading(false); })
          .catch(() => { setQuestions([]); setLoading(false); });
      }, [lecture.key]);
      return (
        <div className="viewer-area">
          <nav className="top-tab-bar">
            {TABS.map(tab => (
              <button key={tab} className={'tab-btn'+(activeTab===tab?' active':'')} onClick={() => setActiveTab(tab)}>{tab}</button>
            ))}
          </nav>
          {activeTab === '강의록'    && <LectureTabContent lecture={lecture} />}
          {activeTab === '기출'      && <QuestionList lecture={lecture} questions={questions} loading={loading} />}
          {activeTab === '학습 가이드' && <GuideTab lecture={lecture} questions={questions} />}
          {activeTab === '3step'     && <StepTab lecture={lecture} questions={questions} stepType={stepType} setStepType={setStepType} />}
          {activeTab === '지엽'      && <MinorTab lecture={lecture} />}
        </div>
      );
    }

    /* ── Tab: 강의록 ── */
    function LectureTabContent({lecture}) {
      if (!lecture.has_lecture) return (
        <div className="viewer-placeholder">
          <div style={{fontSize:'2.5rem'}}>📭</div>
          <div className="placeholder-title">강의록 없음</div>
          <div className="placeholder-sub">이 강의는 강의록 파일이 없습니다.</div>
        </div>
      );
      const url = '/pdf/lecture/'+encodeURIComponent(lecture.key+'.pdf');
      return (
        <React.Fragment>
          <div className="viewer-bar">
            <span className="vb-title">{lecture.title}</span>
            <span className="mode-pill lec">📖 강의록</span>
            <span className="info-pill"><i className="bi bi-person-fill me-1"/>{lecture.professor}</span>
            <span className="info-pill">{lecture.lecture_pages}p</span>
            <a href={url} download={'강의록_'+lecture.key+'.pdf'} className="btn btn-primary btn-sm" style={{fontSize:'.78rem'}}>
              <i className="bi bi-download me-1"/>다운로드
            </a>
          </div>
          <div className="viewer-frame">
            <iframe src={url+'#toolbar=1&navpanes=0'} title="강의록 뷰어"/>
          </div>
        </React.Fragment>
      );
    }

    /* ── Tab: 기출 ── */
    function QuestionList({lecture, questions, loading}) {
      return (
        <div className="question-scroll">
          <div className="page-title">{lecture.title}</div>
          <div className="page-sub">총 {questions.length}문제 · 최신 연도 먼저 · 선지를 클릭하면 정오답이 표시됩니다</div>
          {loading && <div style={{textAlign:'center',padding:'40px 0',color:'#94a3b8'}}><span className="spinner-border spinner-border-sm me-2"/>불러오는 중…</div>}
          {!loading && questions.length === 0 && <div style={{textAlign:'center',padding:'40px 0',color:'#94a3b8'}}>문제가 없습니다.</div>}
          {!loading && questions.map((q, idx) => (
            <QuestionCard key={q.year+'-'+q.num} q={q} index={idx+1} />
          ))}
        </div>
      );
    }

    /* ── Tab: 학습 가이드 ── */
    function GuideTab({lecture, questions}) {
      const guide = useMemo(() => {
        if (!questions.length) return null;
        const tm = {};
        questions.forEach(q => {
          const t = q.topic || '기타';
          if (!tm[t]) tm[t] = {count:0, years:new Set()};
          tm[t].count++;
          tm[t].years.add(q.year);
        });
        const sorted = Object.entries(tm).sort(([,a],[,b]) => b.count - a.count);
        return {
          keyConcepts: sorted.slice(0,8).map(([t,s]) => ({topic:t, count:s.count})),
          freqTopics:  sorted.slice(0,10).map(([t,s]) => ({topic:t, count:s.count, years:[...s.years].sort((a,b)=>b-a)})),
          studyFlow:   sorted.map(([t]) => t),
        };
      }, [questions]);
      if (!guide) return <div style={{flex:1,display:'flex',alignItems:'center',justifyContent:'center',color:'#94a3b8'}}>문제 데이터가 없습니다.</div>;
      return (
        <div className="question-scroll">
          <div className="page-title">{lecture.title} — 학습 가이드</div>
          <div className="page-sub">기출문제 {questions.length}개 분석 기반 · 빈출 토픽 자동 추출</div>
          <div className="guide-section">
            <div className="guide-section-title">📌 핵심 강조 개념</div>
            <div className="guide-concept-list">
              {guide.keyConcepts.map((item, i) => (
                <div key={i} className="guide-concept-item">
                  <span className="rank-badge">#{i+1}</span>
                  <span style={{flex:1}}>{item.topic}</span>
                  <span style={{fontSize:'.72rem',color:'#64748b'}}>{item.count}문제</span>
                </div>
              ))}
            </div>
          </div>
          <div className="guide-section">
            <div className="guide-section-title">🎯 자주 출제 개념</div>
            {guide.freqTopics.map((item, i) => (
              <div key={i} className="guide-freq-item">
                <div style={{fontWeight:700,marginBottom:3}}>{item.topic}</div>
                <div style={{fontSize:'.75rem',color:'#64748b'}}>출제 {item.count}회 · {item.years.join(', ')}년</div>
              </div>
            ))}
          </div>
          <div className="guide-section">
            <div className="guide-section-title">📚 효율적 학습 흐름</div>
            {guide.studyFlow.map((topic, i) => (
              <div key={i} style={{display:'flex',alignItems:'center',gap:8,padding:'6px 0',borderBottom:'1px solid #f1f5f9'}}>
                <span style={{fontSize:'.7rem',fontWeight:800,color:'#3b82f6',minWidth:28}}>{i+1}.</span>
                <span style={{fontSize:'.84rem',color:'#334155'}}>{topic}</span>
              </div>
            ))}
          </div>
        </div>
      );
    }

    /* ── Tab: 3step ── */
    function StepTab({lecture, questions, stepType, setStepType}) {
      const [deepQs, setDeepQs] = useState([]);
      const [deepLoading, setDeepLoading] = useState(false);
      const [minorQs, setMinorQs] = useState([]);
      const [minorLoading, setMinorLoading] = useState(false);

      useEffect(() => {
        if (stepType !== '심화형') return;
        let cancelled = false;
        setDeepLoading(true);
        setDeepQs([]);
        fetch('/api/3step/deep/'+encodeURIComponent(lecture.key))
          .then(r => r.json())
          .then(d => { if (!cancelled) { setDeepQs(d); setDeepLoading(false); } })
          .catch(() => { if (!cancelled) { setDeepQs([]); setDeepLoading(false); } });
        return () => { cancelled = true; };
      }, [stepType, lecture.key]);

      useEffect(() => {
        if (stepType !== '지엽형') return;
        let cancelled = false;
        setMinorLoading(true);
        setMinorQs([]);
        fetch('/api/3step/minor/'+encodeURIComponent(lecture.key))
          .then(r => r.json())
          .then(d => { if (!cancelled) { setMinorQs(d); setMinorLoading(false); } })
          .catch(() => { if (!cancelled) { setMinorQs([]); setMinorLoading(false); } });
        return () => { cancelled = true; };
      }, [stepType, lecture.key]);

      const yamaQs = useMemo(() => rotateChoices(questions), [questions]);
      const displayQs = stepType === '야마형' ? yamaQs : stepType === '심화형' ? deepQs : minorQs;
      const isLoading = stepType === '심화형' ? deepLoading : stepType === '지엽형' ? minorLoading : false;

      return (
        <React.Fragment>
          <div className="step-type-bar">
            {STEP_TYPES.map(t => (
              <button key={t} className={'step-type-btn'+(stepType===t?' active':'')} onClick={() => setStepType(t)}>{t}</button>
            ))}
            {!isLoading && <span style={{marginLeft:'auto',fontSize:'.75rem',color:'#64748b'}}>{displayQs.length}문제</span>}
          </div>
          <div className="question-scroll">
            <div className="page-title">{lecture.title} — {stepType}</div>
            <div className="page-sub">
              {stepType === '야마형' && '핵심 빈출 문제 · 선지 순서 변형 적용'}
              {stepType === '심화형' && '핵심 개념 심화 문제 · 텍스트 전용'}
              {stepType === '지엽형' && '지엽 세부 지식 문제'}
            </div>
            {isLoading && <div style={{textAlign:'center',padding:'40px 0',color:'#94a3b8'}}><span className="spinner-border spinner-border-sm me-2"/>불러오는 중…</div>}
            {!isLoading && displayQs.length === 0 && <div style={{textAlign:'center',padding:'40px 0',color:'#94a3b8'}}>문제가 없습니다.</div>}
            {!isLoading && displayQs.map((q, idx) => (
              <QuestionCard key={stepType+'-'+q.year+'-'+q.num} q={q} index={idx+1} />
            ))}
          </div>
        </React.Fragment>
      );
    }

    /* ── Tab: 지엽 ── */
    function MinorTab({lecture}) {
      const [minorData, setMinorData] = useState(null);
      const [loading, setLoading] = useState(false);
      useEffect(() => {
        setMinorData(null);
        setLoading(true);
        fetch('/api/minor/'+encodeURIComponent(lecture.key))
          .then(r => r.json())
          .then(d => { setMinorData(d); setLoading(false); })
          .catch(() => { setMinorData([]); setLoading(false); });
      }, [lecture.key]);
      return (
        <div className="question-scroll">
          <div className="page-title">{lecture.title} — 지엽 정리</div>
          <div className="page-sub">빈출도 낮은 세부 내용 · 암기 포인트 중심</div>
          {loading && <div style={{textAlign:'center',padding:'40px 0',color:'#94a3b8'}}><span className="spinner-border spinner-border-sm me-2"/>불러오는 중…</div>}
          {!loading && minorData && minorData.length === 0 && <div style={{textAlign:'center',padding:'40px 0',color:'#94a3b8'}}>지엽 항목이 없습니다.</div>}
          {!loading && minorData && minorData.map((item, i) => (
            <div key={i} className="minor-card">
              <div className="minor-card-header">
                <span className="minor-card-title">{item.topic}</span>
                <span className="minor-card-badge">{item.q_count}회 · {item.years.join(', ')}년</span>
              </div>
              <div className="minor-card-body">
                {item.key_points.map((pt, j) => (
                  <div key={j} className="minor-key-point">{pt}</div>
                ))}
                {item.mnemonic && <div className="minor-mnemonic">💡 {item.mnemonic}</div>}
              </div>
            </div>
          ))}
        </div>
      );
    }

    /* ── QuestionCard (shared by 기출, 3step) ── */
    function QuestionCard({q, index}) {
      const [chosen, setChosen] = useState(null);
      const [revealed, setRevealed] = useState(false);
      const [lightbox, setLightbox] = useState(null);
      useEffect(() => {
        const handler = e => { if (e.key === 'Escape') setLightbox(null); };
        window.addEventListener('keydown', handler);
        return () => window.removeEventListener('keydown', handler);
      }, []);
      function choiceClass(num) {
        if (chosen === null) return 'choice-btn';
        const ans = parseInt(q._answer_num, 10);
        if (num === ans) return 'choice-btn correct';
        if (num === chosen) return 'choice-btn wrong';
        return 'choice-btn dimmed';
      }
      return (
        <React.Fragment>
          <div className="q-card">
            <div className="q-header">
              <span className="q-year-badge">{q.year}년 Q{q.num}</span>
              <span className="q-topic">[{q.professor}] {q.topic}</span>
            </div>
            <div className="q-body">
              <div className="q-text">{q.question_text}</div>
              <div className="choices">
                {q._real_choices.map((ch, i) => {
                  const num = i + 1;
                  return <button key={num} className={choiceClass(num)} onClick={() => { if (chosen === null) setChosen(num); }}>{ch}</button>;
                })}
              </div>
              <div className="reveal-wrap">
                <button className={'reveal-btn'+(revealed?' revealed':'')} onClick={() => setRevealed(r => !r)}>
                  {revealed ? '답과 해설 닫기' : '답과 해설 보기'}
                </button>
              </div>
              {revealed && (
                <div className="answer-panel">
                  <div className="answer-line">정답: {q.answer}</div>
                  {q._images && q._images.length > 0 && (
                    <div className="q-images">
                      {q._images.map(img => (
                        <img key={img} src={'/static/images/'+img} alt="풀이 이미지" onClick={() => setLightbox('/static/images/'+img)} />
                      ))}
                    </div>
                  )}
                  {q.explanation && <div className="explanation">{q.explanation}</div>}
                </div>
              )}
            </div>
          </div>
          {lightbox && (
            <div className="lightbox show" onClick={() => setLightbox(null)}>
              <button className="lightbox-close" onClick={() => setLightbox(null)}>✕</button>
              <img src={lightbox} alt="확대" onClick={e => e.stopPropagation()} />
            </div>
          )}
        </React.Fragment>
      );
    }

    /* ── Placeholder ── */
    function Placeholder() {
      return (
        <div className="viewer-placeholder">
          <div className="placeholder-icon">📄</div>
          <div className="placeholder-title">강의를 선택하세요</div>
          <div className="placeholder-sub">왼쪽 목록에서 강의를 클릭하면 학습을 시작할 수 있습니다</div>
        </div>
      );
    }

    ReactDOM.createRoot(document.getElementById('root')).render(<App />);
  </script>
</body>
</html>
"""


# ── 인터랙티브 문제 뷰어 HTML ────────────────────────────────────────────
QUESTIONS_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ title }}</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">
  <style>
    body { background:#f8fafc; font-family:'Noto Sans KR',sans-serif; padding:20px 16px 60px; }
    .page-title { font-size:1.1rem; font-weight:800; color:#1e293b; margin-bottom:4px; }
    .page-sub   { font-size:.82rem; color:#64748b; margin-bottom:24px; }

    .q-card {
      background:#fff; border-radius:12px;
      box-shadow:0 1px 4px rgba(0,0,0,.08);
      margin-bottom:20px; overflow:hidden;
    }
    .q-header {
      padding:10px 16px;
      background:linear-gradient(135deg,#1e40af,#3b82f6);
      display:flex; align-items:center; gap:8px; flex-wrap:wrap;
    }
    .q-year-badge {
      font-size:.75rem; font-weight:800; color:#fff;
      background:rgba(255,255,255,.18); padding:2px 10px; border-radius:20px;
    }
    .q-topic { font-size:.72rem; color:#bfdbfe; }
    .q-body  { padding:16px; }

    .q-text {
      font-size:.92rem; line-height:1.75; color:#1e293b;
      white-space:pre-wrap; margin-bottom:14px;
    }
    .q-images { display:flex; flex-wrap:wrap; gap:10px; margin-bottom:14px; }
    .q-images img {
      max-width:100%; max-height:280px; border-radius:8px;
      border:1px solid #e2e8f0; object-fit:contain;
      cursor:pointer;
    }

    /* 선지 버튼 */
    .choices { display:flex; flex-direction:column; gap:7px; margin-bottom:16px; }
    .choice-btn {
      width:100%; text-align:left;
      padding:9px 14px; border-radius:8px; border:1.5px solid #e2e8f0;
      background:#f8fafc; font-size:.88rem; color:#334155;
      cursor:pointer; transition:all .15s;
      white-space:pre-wrap; line-height:1.55;
    }
    .choice-btn:hover:not(.correct):not(.wrong) { background:#f1f5f9; border-color:#94a3b8; }
    .choice-btn.correct { background:#dcfce7; border-color:#22c55e; color:#15803d; font-weight:700; }
    .choice-btn.wrong   { background:#fee2e2; border-color:#ef4444; color:#b91c1c; }
    .choice-btn.dimmed  { opacity:.45; }

    /* 답/해설 토글 */
    .reveal-wrap { display:flex; justify-content:flex-end; }
    .reveal-btn {
      font-size:.82rem; font-weight:700; padding:7px 18px; border-radius:8px;
      border:1.5px solid #a5b4fc; background:#eef2ff; color:#4338ca; cursor:pointer;
      transition:all .15s;
    }
    .reveal-btn:hover { background:#e0e7ff; }
    .reveal-btn.revealed { background:#4338ca; color:#fff; border-color:#4338ca; }

    .answer-panel {
      display:none; margin-top:14px;
      padding:14px; background:#f0fdf4;
      border-radius:10px; border:1.5px solid #86efac;
    }
    .answer-line {
      font-size:.9rem; font-weight:800; color:#15803d; margin-bottom:8px;
    }
    .explanation {
      font-size:.85rem; line-height:1.75; color:#1e293b;
      white-space:pre-wrap;
    }

    /* 이미지 라이트박스 */
    .lightbox {
      display:none; position:fixed; inset:0; background:rgba(0,0,0,.85);
      z-index:9999; align-items:center; justify-content:center;
    }
    .lightbox.show { display:flex; }
    .lightbox img { max-width:92vw; max-height:90vh; border-radius:8px; }
    .lightbox-close {
      position:fixed; top:16px; right:20px; color:#fff; font-size:2rem;
      cursor:pointer; background:none; border:none; line-height:1;
    }
  </style>
</head>
<body>
  <div class="page-title">{{ title }}</div>
  <div class="page-sub">총 {{ questions|length }}문제 · 최신 연도 먼저 · 선지를 클릭하면 정오답이 표시됩니다</div>

  {% for q in questions %}
  <div class="q-card" id="qcard-{{ loop.index }}">
    <div class="q-header">
      <span class="q-year-badge">{{ q.year }}년 Q{{ q.num }}</span>
      <span class="q-topic">[{{ q.professor }}]  {{ q.topic }}</span>
    </div>
    <div class="q-body">
      <div class="q-text">{{ q.question_text }}</div>

      {% if q._images %}
      <div class="q-images">
        {% for img in q._images %}
        <img src="/static/images/{{ img }}" alt="문제 이미지" onclick="openLightbox(this.src)">
        {% endfor %}
      </div>
      {% endif %}

      <div class="choices" id="choices-{{ loop.index }}">
        {% for ch in q._real_choices %}
        <button class="choice-btn"
                data-num="{{ loop.index0 + 1 }}"
                data-answer="{{ q._answer_num }}"
                onclick="checkChoice(this)">{{ ch }}</button>
        {% endfor %}
      </div>

      <div class="reveal-wrap">
        <button class="reveal-btn" onclick="toggleAnswer(this)">답과 해설 보기</button>
      </div>
      <div class="answer-panel">
        <div class="answer-line">정답: {{ q.answer }}</div>
        {% if q.explanation %}
        <div class="explanation">{{ q.explanation }}</div>
        {% endif %}
      </div>
    </div>
  </div>
  {% endfor %}

  <!-- 라이트박스 -->
  <div class="lightbox" id="lightbox" onclick="closeLightbox()">
    <button class="lightbox-close" onclick="closeLightbox()">✕</button>
    <img id="lightboxImg" src="" alt="">
  </div>

  <script>
    function checkChoice(btn) {
      const wrap    = btn.closest('.choices');
      const already = wrap.querySelector('.correct, .wrong');
      if (already) return; // 이미 답 확인됨

      const chosen = btn.dataset.num;
      const answer = btn.dataset.answer;

      wrap.querySelectorAll('.choice-btn').forEach(b => {
        if (b.dataset.num === answer) {
          b.classList.add('correct');
        } else if (b.dataset.num === chosen) {
          b.classList.add('wrong');
        } else {
          b.classList.add('dimmed');
        }
      });
    }

    function toggleAnswer(btn) {
      const panel = btn.closest('.q-body').querySelector('.answer-panel');
      const open  = panel.style.display === 'block';
      panel.style.display = open ? 'none' : 'block';
      btn.textContent = open ? '답과 해설 보기' : '답과 해설 닫기';
      btn.classList.toggle('revealed', !open);
    }

    function openLightbox(src) {
      document.getElementById('lightboxImg').src = src;
      document.getElementById('lightbox').classList.add('show');
    }
    function closeLightbox() {
      document.getElementById('lightbox').classList.remove('show');
    }
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeLightbox(); });
  </script>
</body>
</html>
"""


# ── Flask 라우트 ──────────────────────────────────────────────────────

def group_by_date(meta_list):
    groups = {}
    for m in meta_list:
        groups.setdefault(m['date'], []).append(m)
    return groups


def _slice_pdf(pdf_dir, filename, start, end):
    from pypdf import PdfWriter, PdfReader
    safe = os.path.basename(filename)
    path = os.path.join(pdf_dir, safe)
    if not os.path.exists(path):
        abort(404)
    reader = PdfReader(path)
    writer = PdfWriter()
    for i in range(start, min(end, len(reader.pages))):
        writer.add_page(reader.pages[i])
    buf = io.BytesIO()
    writer.write(buf)
    buf.seek(0)
    return buf


@app.route("/")
def index():
    return HTML_TEMPLATE


@app.route("/pdf/lecture/<filename>")
def serve_lecture(filename):
    safe = os.path.basename(filename)
    key  = safe.replace('.pdf', '')
    m    = META_BY_KEY.get(key)
    if not m or not m['has_lecture']:
        abort(404)
    buf = _slice_pdf(PDF_DIR_LEC, safe, 0, m['lecture_pages'])
    return send_file(buf, mimetype="application/pdf", download_name="강의록_" + safe)


@app.route("/view/<lecture_key>")
def view_questions(lecture_key):
    """인터랙티브 문제 뷰어"""
    questions = QUESTION_IDX.get(lecture_key, [])
    if lecture_key not in META_BY_KEY:
        abort(404)
    m = META_BY_KEY.get(lecture_key, {})
    title = m.get('title', lecture_key)
    return render_template_string(
        QUESTIONS_TEMPLATE,
        title=title,
        questions=questions,
    )


@app.route("/api/lectures")
def api_lectures():
    return jsonify(META)


@app.route("/api/questions/<lecture_key>")
def api_questions(lecture_key):
    if lecture_key not in META_BY_KEY:
        abort(404)
    qs = QUESTION_IDX.get(lecture_key, [])
    serializable = []
    for q in qs:
        serializable.append({
            'year':          q.get('year'),
            'num':           q.get('num'),
            'professor':     q.get('professor', ''),
            'topic':         q.get('topic', ''),
            'question_text': q.get('question_text', ''),
            'answer':        q.get('answer', ''),
            'explanation':   q.get('explanation', ''),
            '_answer_num':   q.get('_answer_num', ''),
            '_real_choices': q.get('_real_choices', []),
            '_images':       q.get('_images', []),
        })
    return jsonify(serializable)


@app.route("/api/3step/<step_type>/<lecture_key>")
def api_3step(step_type, lecture_key):
    if lecture_key not in META_BY_KEY:
        abort(404)
    qs = QUESTION_IDX.get(lecture_key, [])
    topic_counts = {}
    for q in qs:
        t = q.get('topic', '')
        topic_counts[t] = topic_counts.get(t, 0) + 1

    def serialize(q, images=True):
        return {
            'year':          q.get('year'),
            'num':           q.get('num'),
            'professor':     q.get('professor', ''),
            'topic':         q.get('topic', ''),
            'question_text': q.get('question_text', ''),
            'answer':        q.get('answer', ''),
            'explanation':   q.get('explanation', ''),
            '_answer_num':   q.get('_answer_num', ''),
            '_real_choices': q.get('_real_choices', []),
            '_images':       q.get('_images', []) if images else [],
        }

    if step_type == 'deep':
        # 심화형: high-frequency topics, text-only (no images)
        high = {t for t, c in topic_counts.items() if c >= 2}
        result = [serialize(q, images=False) for q in qs if q.get('topic', '') in high]
    elif step_type == 'minor':
        # 지엽형: low-frequency topics
        low = {t for t, c in topic_counts.items() if c == 1}
        result = [serialize(q) for q in qs if q.get('topic', '') in low]
    else:
        abort(404)
    return jsonify(result)


@app.route("/api/minor/<lecture_key>")
def api_minor(lecture_key):
    if lecture_key not in META_BY_KEY:
        abort(404)
    qs = QUESTION_IDX.get(lecture_key, [])
    topic_data = {}
    for q in qs:
        t = q.get('topic') or '기타'
        if t not in topic_data:
            topic_data[t] = {'questions': [], 'count': 0}
        topic_data[t]['questions'].append(q)
        topic_data[t]['count'] += 1

    minor = []
    for topic, data in topic_data.items():
        if data['count'] <= 2:
            key_points = []
            for q in data['questions']:
                exp = (q.get('explanation') or '').strip()
                if exp:
                    key_points.append(exp[:150])
            words = [w for w in topic.split() if len(w) > 1][:3]
            mnemonic = '핵심 키워드: ' + ' · '.join(words) if words else None
            first_ans = data['questions'][0].get('answer', '') if data['questions'] else ''
            if first_ans and mnemonic:
                mnemonic += f' / 대표 정답: {first_ans}'
            minor.append({
                'topic':      topic,
                'q_count':    data['count'],
                'years':      sorted({q.get('year', 0) for q in data['questions']}, reverse=True),
                'key_points': key_points[:3],
                'mnemonic':   mnemonic,
            })
    minor.sort(key=lambda x: x['topic'])
    return jsonify(minor)


if __name__ == "__main__":
    print("=" * 50)
    print("  호흡기 기출문제 뷰어")
    print("  http://localhost:8080 에서 확인하세요")
    print("=" * 50)
    app.run(debug=False, port=8080)
