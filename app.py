#!/usr/bin/env python3
"""
호흡기 2차 기출문제 뷰어 — Flask 단일 파일 앱
데이터 생성 전 먼저 python output/gen_lecture_plan.py 실행 필요
"""

import io
import json
import os
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from flask import Flask, abort, jsonify, send_file, send_from_directory

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
JSON_PATH = OUTPUT_DIR / "questions_mapping.json"
IMAGE_DIR = OUTPUT_DIR / "images"
SOLUTION_DIR = IMAGE_DIR / "solutions"
SOLUTION_MAPPING_PATH = OUTPUT_DIR / "solution_mapping.json"
LECTURE_PLAN_PATH = OUTPUT_DIR / "lecture_plan.json"
STUDY_GUIDE_PATH = OUTPUT_DIR / "study_guide.json"
THREESTEP_DEEP_PATH = OUTPUT_DIR / "3step_deep.json"
THREESTEP_MINOR_PATH = OUTPUT_DIR / "3step_minor.json"
MINOR_TOPICS_PATH = OUTPUT_DIR / "minor_topics.json"
LECTURE_DIR = BASE_DIR / "호흡기(2) 강의록"

app = Flask(__name__, static_folder=str(IMAGE_DIR), static_url_path="/static/images")

LECTURE_FILES = {
    "차시1": ["1229 1,2교시 소아 호흡기질환 (김가은).pdf"],
    "차시2": ["1229 3교시 광범위사이질폐질환 (황일선).pdf"],
    "차시3": ["1229 5교시 학생강의_간질성폐질환 총론 (윤성환).pdf"],
    "차시4": ["1229 6교시 간질성폐질환 각론 (윤성환).pdf"],
    "차시5": ["1229 7교시 과민성폐렴과 호산구성폐질환 (윤성환).pdf"],
    "차시6": ["1229 8교시 흉곽,늑막 삼출 (박순효).pdf"],
    "차시7": ["1230 1교시 폐종양의 원인,증상 및 진단 (박순효).pdf"],
    "차시8": ["1230 2교시 폐종양의 병기 및 치료 (박순효).pdf"],
    "차시9": [
        "1230 3교시 소아 호흡기질환 학생강의 (김가은).pdf",
        "1230 4교시 소아 호흡기질환 (김가은).pdf",
    ],
    "차시10": ["1231 1교시 비종양성 폐질환의 외과적 치료(금동윤).pdf"],
    "차시11": ["1231 2교시 폐종양의 외과적 치료 (금동윤).pdf"],
    "차시12": ["1231 3교시 중환자의학 (박재석).pdf"],
    "차시13": ["1231 4교시 급성호흡곤란증 (박재석).pdf"],
    "차시14": ["1231 5교시 폐암 조기진단 (김태훈).pdf"],
    "차시15": ["0102 1교시 호흡기TBL4_폐종양의 병리 (황일선).pdf"],
    "차시16": ["0102 2교시 흉부절개 및 폐절제술 늑막질환 (채민철).pdf"],
    "차시17": ["0102 3교시 호흡기학 종격동질환(채민철).pdf"],
    "차시18": ["0102 4교시 늑막과 종격동 종양의 영상의학(홍정희).pdf"],
    "차시19": ["0102 5교시 호흡기핵의학(송봉일).pdf"],
    "차시20": ["0102 6교시 폐종양 및 흉선종의 방사선 치료(김진희).pdf"],
    "차시21": ["0105 1교시 호흡재활 (김경태).pdf"],
    "차시22": [],
    "차시23": ["0105 3교시 기계환기(박재석).pdf"],
}

DATE_LABELS = {
    "1229": "12/29",
    "1230": "12/30",
    "1231": "12/31",
    "0102": "01/02",
    "0105": "01/05",
}

DATE_ORDER = {"12/29": 0, "12/30": 1, "12/31": 2, "01/02": 3, "01/05": 4, "기타": 99}


def nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def clean_text(value: str) -> str:
    return re.sub(r"[ \t]+", " ", (value or "").replace("\r\n", "\n").replace("\r", "\n")).strip()


def normalize_topic(topic: str) -> str:
    topic = clean_text(topic)
    return re.sub(r"\s+", " ", topic) or "기타"


def parse_answer_num(answer_str: str) -> str:
    match = re.match(r"^\s*(\d+)", str(answer_str or ""))
    return match.group(1) if match else str(answer_str or "").strip()


INLINE_STEM_END = re.compile(
    r"(.{8,260}?(?:것은\s*\?|항목은\s*\?|고르시오\.?|적절한 치료는\s*\?|"
    r"치료는\s*\?|상황은\s*\?|수술법은\s*\?|바르지 않은 것은\s*\?|옳은 것은\s*\?|"
    r"틀린 것은\s*\?|아닌 것은\s*\?|맞는 것은\s*\?))\s*(.+)$",
    re.S,
)
INLINE_CIRCLED = re.compile(r"([①②③④⑤])")
INLINE_NUMBER_MARKER = re.compile(r"(?<!\w)([1-5])(?:[)）]|\.)\s+")


def _clean_inline_choice(text: str) -> str:
    text = clean_text(text)
    text = re.sub(r"^[XO0o]\s*", "", text).strip()
    text = re.sub(r"^[아어이가나]\s+", "", text).strip()
    text = text.strip(" ,.;:|")
    return text


def _split_balanced_choices(text: str, count: int = 5):
    words = [word for word in re.split(r"\s+", text.strip()) if word]
    if len(words) < count:
        return []
    avg = max(1, round(len(words) / count))
    choices = []
    start = 0
    for idx in range(count):
        if idx == count - 1:
            end = len(words)
        else:
            end = min(len(words), start + avg)
            window_end = min(len(words), end + 5)
            for pos in range(end, window_end):
                if re.search(r"(다|요|음|함|됨|한다|시행|치료|투여|계획|관찰)$", words[pos - 1]):
                    end = pos
                    break
        piece = _clean_inline_choice(" ".join(words[start:end]))
        if len(piece) < 2:
            return []
        choices.append(piece)
        start = end
    return choices if len(choices) == count else []


def parse_inline_numbered_choices(raw: str):
    text = clean_text(raw)
    markers = list(INLINE_NUMBER_MARKER.finditer(text))
    nums = [int(match.group(1)) for match in markers]
    if len(nums) < 3:
        return None
    expected = list(range(1, min(len(nums), 5) + 1))
    if nums[: len(expected)] != expected:
        return None
    if len(markers) > 5 and int(markers[5].group(1)) <= 5:
        markers = markers[:5]
    else:
        markers = markers[: len(expected)]
    stem = text[:markers[0].start()].strip()
    choices = []
    for idx, marker in enumerate(markers):
        start = marker.end()
        end = markers[idx + 1].start() if idx + 1 < len(markers) else len(text)
        body = _clean_inline_choice(text[start:end])
        if not body:
            return None
        choices.append(f"{idx + 1}) {body}")
    return stem, choices


def parse_inline_choices(raw: str):
    text = clean_text(raw)
    if not text:
        return "", []
    numbered = parse_inline_numbered_choices(text)
    if numbered:
        return numbered
    circled = INLINE_CIRCLED.split(text)
    if len(circled) >= 11 and circled[1] == "①":
        stem = circled[0].strip()
        choices = []
        for idx in range(1, len(circled), 2):
            marker = circled[idx]
            body = circled[idx + 1] if idx + 1 < len(circled) else ""
            num = "①②③④⑤".find(marker) + 1
            if 1 <= num <= 5:
                choices.append(f"{num}) {_clean_inline_choice(body)}")
        if len(choices) >= 2:
            return stem, choices[:5]

    match = INLINE_STEM_END.match(text)
    if match:
        stem, tail = match.group(1).strip(), match.group(2).strip()
    elif "?" in text:
        stem, tail = text.split("?", 1)
        stem = stem.strip() + "?"
        tail = tail.strip()
    else:
        return text, []
    tail = re.sub(r"\s*[;:]\s*", " | ", tail)
    tail = re.sub(r"\s+[XO0o]\s*(?=$|[가-힣A-Z([])", " | ", tail)
    tail = re.sub(r"(?<=[다요음함됨])\s*[0o]\s*(?=$|[가-힣A-Z([])", " | ", tail)
    parts = [_clean_inline_choice(part) for part in tail.split("|")]
    parts = [part for part in parts if len(part) >= 2]

    expanded = []
    for part in parts:
        if len(part) > 130:
            sentences = re.split(r"(?<=[.!?。])\s+|(?<=[다요음함됨])\s+(?=[가-힣A-Z([])", part)
            expanded.extend(_clean_inline_choice(sentence) for sentence in sentences if len(sentence.strip()) >= 3)
        else:
            expanded.append(part)
    parts = [part for part in expanded if part]
    if len(parts) < 5 and len(tail) >= 20:
        parts = _split_balanced_choices(tail)
    if len(parts) >= 5:
        return stem, [f"{idx}) {body}" for idx, body in enumerate(parts[:5], start=1)]
    return stem, []


def parse_rawtext(raw: str):
    inline_numbered = parse_inline_numbered_choices(raw or "")
    if inline_numbered:
        return inline_numbered
    lines = (raw or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    choice_start = None
    circled_map = {"①": 1, "②": 2, "③": 3, "④": 4, "⑤": 5}
    hangul_map = {"가": 1, "나": 2, "다": 3, "라": 4, "마": 5}
    first_choice_patterns = [
        re.compile(r"^\s*1[)）]\s*(.*)$"),
        re.compile(r"^\s*①\s*(.*)$"),
        re.compile(r"^\s*1\.\s*(.*)$"),
        re.compile(r"^\s*가\.\s*(.*)$"),
    ]
    choice_patterns = [
        re.compile(r"^\s*(\d+)[)）]\s*(.*)$"),
        re.compile(r"^\s*([①②③④⑤])\s*(.*)$"),
        re.compile(r"^\s*(\d+)\.\s*(.*)$"),
        re.compile(r"^\s*([가나다라마])\.\s*(.*)$"),
    ]

    def parse_choice_line(line: str):
        for pattern in choice_patterns:
            matched = pattern.match(line)
            if not matched:
                continue
            marker, body = matched.group(1), matched.group(2).strip()
            if marker in circled_map:
                num = circled_map[marker]
            elif marker in hangul_map:
                num = hangul_map[marker]
            else:
                num = int(marker)
            return num, body
        return None

    for idx, line in enumerate(lines):
        if any(pattern.match(line) for pattern in first_choice_patterns):
            parsed = parse_choice_line(line)
            if parsed and parsed[0] == 1:
                choice_start = idx
                break

    if choice_start is None:
        return parse_inline_choices("\n".join(lines))

    question_lines = lines[:choice_start]
    choice_lines = lines[choice_start:]
    choices = []
    current_num = None
    current_parts = []

    for line in choice_lines:
        parsed = parse_choice_line(line)
        if parsed:
            num, body = parsed
            if 1 <= num <= 5:
                if current_num is not None and num <= current_num:
                    break
                if current_num is not None:
                    choices.append(f"{current_num}) {' '.join(current_parts).strip()}")
                current_num = num
                current_parts = [body] if body else []
                continue
        if current_num is not None and line.strip():
            current_parts.append(line.strip())

    if current_num is not None:
        choices.append(f"{current_num}) {' '.join(current_parts).strip()}")

    return clean_text("\n".join(question_lines)), choices


def lecture_file_path(filename: str):
    target = nfc(filename)
    for existing in LECTURE_DIR.iterdir():
        if nfc(existing.name) == target:
            return existing
    return None


def find_question_images(year, num):
    prefix = f"{year}_{num}_"
    if not IMAGE_DIR.exists():
        return []
    return sorted(
        path.name for path in IMAGE_DIR.iterdir()
        if path.is_file()
        and path.name.startswith(prefix)
        and path.name not in SOLUTION_FILENAMES
    )


def load_json_file(path, default):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def build_solution_index():
    mapping = load_json_file(SOLUTION_MAPPING_PATH, [])
    indexed = defaultdict(list)
    for item in mapping:
        question_id = item.get("question_id")
        filename = item.get("filename")
        if question_id and filename:
            indexed[question_id].append(filename)
    return indexed


def build_minor_key_points(questions):
    points = []
    seen = set()
    for q in questions:
        for source in [q.get("explanation", ""), q.get("question_text", "")]:
            text = clean_text(source)
            if not text:
                continue
            snippet = text[:160]
            if snippet not in seen:
                seen.add(snippet)
                points.append(snippet)
            if len(points) >= 3:
                return points
    return points


def build_mnemonic(topic: str, questions):
    keywords = [token for token in re.split(r"[\s,·()/]+", topic) if len(token) >= 2][:3]
    base = f"핵심 키워드: {' · '.join(keywords)}" if keywords else ""
    answers = [parse_answer_num(q.get("answer", "")) for q in questions]
    answers = [ans for ans in answers if ans]
    if answers:
        top_answer = Counter(answers).most_common(1)[0][0]
        return f"{base} / 대표 정답: {top_answer}" if base else f"대표 정답: {top_answer}"
    return base or None


PHOTO_KEYWORDS = ["사진", "그림", "영상", "CT", "PET", "X-ray", "X선", "X-선", "소견이다", "소견은", "촬영"]


def has_photo_text(question):
    text = f"{question.get('question_text', '')} {question.get('rawText', '')}".lower()
    return any(keyword.lower() in text for keyword in PHOTO_KEYWORDS)


OCR_NOISE_PATTERN = re.compile(
    r"떼양|폐앉|생암종|비혼연자|대장임|치즈과사|64새|IIYNOMQ|"
    r"흩연|총괴|엿다|앉다|하없다|외있|있없|관찰되다|페질환"
)


def is_ocr_quality_bad(raw_q, rawtext):
    if int(raw_q.get("year") or 0) != 2020:
        return False
    if not rawtext:
        return False
    # 2020 OCR corpus still contains widespread medical-term corruption, so
    # hide it until a reliable re-extraction replaces the rawText.
    return True


def serialize_question(question, include_images=True):
    images = question.get("_images", []) if include_images else []
    photo_text = has_photo_text(question)
    data_quality_issue = question.get("data_quality_issue", "")
    return {
        "id": question.get("id"),
        "year": question.get("year"),
        "num": question.get("num"),
        "session": question.get("session"),
        "professor": question.get("professor", ""),
        "topic": question.get("topic", ""),
        "question_text": question.get("question_text", ""),
        "answer": question.get("answer", ""),
        "explanation": question.get("explanation", ""),
        "no_rawtext": question.get("no_rawtext", False),
        "_answer_num": question.get("_answer_num", ""),
        "_real_choices": question.get("_real_choices", []),
        "_images": images,
        "has_photo_text": photo_text,
        "photo_image_missing": bool(photo_text and not images and not data_quality_issue),
        "data_quality_issue": data_quality_issue,
        "solution_images": question.get("solution_images", []),
    }


def serialize_generated_question(question):
    answer = str(question.get("answer", ""))
    choices = question.get("choices", [])
    return {
        "id": question.get("id"),
        "year": "3step",
        "num": question.get("id", "").split("-")[-1],
        "session": question.get("session", ""),
        "professor": "",
        "topic": question.get("type", ""),
        "question_text": question.get("question", ""),
        "answer": answer,
        "explanation": question.get("explanation", ""),
        "_answer_num": parse_answer_num(answer),
        "_real_choices": [f"{idx + 1}) {choice}" for idx, choice in enumerate(choices)],
        "_images": [],
        "solution_images": [],
    }


def load_data():
    with JSON_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    session_map = data["session_map"]
    raw_questions = data["questions"]
    questions_by_session = defaultdict(list)

    for raw_q in raw_questions:
        rawtext = raw_q.get("rawText", "").strip()
        data_quality_issue = ""
        if is_ocr_quality_bad(raw_q, rawtext):
            question_text = "(OCR 품질 미달 - 데이터 없음)"
            choices = []
            data_quality_issue = "OCR 품질 미달"
        elif rawtext:
            question_text, choices = parse_rawtext(rawtext)
        else:
            question_text = "(문제 원문 없음 - 답·해설만 제공)"
            choices = []
        session_key = raw_q.get("session", "")
        topic = normalize_topic(raw_q.get("topic", ""))
        parsed = {
            **raw_q,
            "topic": topic,
            "question_text": question_text,
            "no_rawtext": not bool(rawtext),
            "data_quality_issue": data_quality_issue,
            "_real_choices": choices,
            "_answer_num": parse_answer_num(raw_q.get("answer", "")),
            "_images": find_question_images(raw_q.get("year"), raw_q.get("num")),
            "solution_images": SOLUTION_IDX.get(raw_q.get("id"), []),
        }
        questions_by_session[session_key].append(parsed)

    meta = []
    for session_key, session_info in session_map.items():
        session_questions = questions_by_session.get(session_key, [])
        years = sorted({q.get("year") for q in session_questions if q.get("year")}, reverse=True)
        date_label = DATE_LABELS.get(session_info.get("date"), "기타")
        period = clean_text(session_info.get("period", ""))
        session_display = period
        meta.append(
            {
                "key": session_key,
                "date": date_label,
                "session_display": session_display,
                "period": period,
                "professor": clean_text(session_info.get("professor", "")),
                "topic": normalize_topic(session_info.get("topic", "")),
                "years": years,
                "q_count": len(session_questions),
                "has_lecture": bool(LECTURE_FILES.get(session_key)),
                "lecture_plan": {
                    "prediction": LECTURE_PLAN.get(session_key, {}).get("prediction", ""),
                    "trend": LECTURE_PLAN.get(session_key, {}).get("trend", ""),
                    "questions_by_year": LECTURE_PLAN.get(session_key, {}).get("questions_by_year", {}),
                },
                "study_units": STUDY_GUIDE.get(session_key, []),
            }
        )

    meta.sort(key=lambda item: (DATE_ORDER.get(item["date"], 99), int(re.sub(r"\D", "", item["key"]) or 0)))

    for session_key in questions_by_session:
        questions_by_session[session_key].sort(key=lambda q: (-int(q.get("year", 0)), int(q.get("num", 0))))

    return meta, {item["key"]: item for item in meta}, questions_by_session


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>호흡기 2차 기출문제 뷰어</title>
  <link rel="stylesheet" href="/vendor/bootstrap.min.css">
  <link rel="stylesheet" href="/vendor/bootstrap-icons.min.css">
  <style>
    :root { --sidebar-w:360px; --header-h:56px; }
    body { background:#f1f5f9; overflow:hidden; height:100dvh; margin:0; font-family:'Noto Sans KR',sans-serif; }

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

    .sidebar-panel {
      width:var(--sidebar-w); height:calc(100dvh - var(--header-h));
      display:flex; flex-direction:column; background:#fff;
      border-right:1px solid #e2e8f0; flex-shrink:0; overflow:hidden;
    }
    .sidebar-top { padding:14px 14px 0; background:#f8fafc; border-bottom:1px solid #e2e8f0; flex-shrink:0; }
    .sidebar-top .title-row { display:flex; align-items:center; justify-content:space-between; padding-bottom:10px; }
    .sidebar-top .title-row h6 { font-size:.75rem; font-weight:700; text-transform:uppercase; letter-spacing:.06em; color:#64748b; margin:0; }
    .sidebar-scroll { overflow-y:auto; flex:1; }

    .search-box { background:#fff; border:1px solid #e2e8f0; border-radius:8px; padding:7px 12px; display:flex; align-items:center; gap:8px; margin-bottom:10px; }
    .search-box i { color:#94a3b8; font-size:.9rem; flex-shrink:0; }
    .search-box input { border:none; outline:none; font-size:.82rem; background:transparent; color:#1e293b; width:100%; }
    .search-box input::placeholder { color:#b0bec5; }

    .sort-bar { display:flex; gap:6px; padding-bottom:12px; }
    .sort-btn { flex:1; padding:5px 0; font-size:.75rem; font-weight:700; border-radius:8px; border:1.5px solid #e2e8f0; background:#f8fafc; color:#475569; cursor:pointer; transition:all .15s; }
    .sort-btn.active { background:#1e293b; color:#fff; border-color:#1e293b; }
    .sort-btn:not(.active):hover { background:#f1f5f9; }

    .date-header {
      padding:6px 14px 4px; font-size:.67rem; font-weight:800; text-transform:uppercase;
      letter-spacing:.08em; color:#94a3b8; background:#f8fafc; border-bottom:1px solid #f1f5f9;
      position:sticky; top:0; z-index:2; display:flex; align-items:center; gap:6px;
    }
    .date-header::before { content:''; display:block; width:6px; height:6px; border-radius:50%; background:#cbd5e1; }

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

    .top-tab-bar { display:flex; gap:4px; padding:10px 16px; background:#fff; border-bottom:1px solid #e2e8f0; flex-shrink:0; }
    .tab-btn { padding:6px 16px; border-radius:8px; font-size:.82rem; font-weight:700; border:1.5px solid #e2e8f0; background:#f8fafc; color:#475569; cursor:pointer; transition:all .15s; white-space:nowrap; }
    .tab-btn:hover:not(.active) { background:#f1f5f9; color:#334155; }
    .tab-btn.active { background:#1e293b; color:#fff; border-color:#1e293b; }

    .question-scroll { flex:1; overflow-y:auto; padding:20px 16px 60px; }
    .page-title { font-size:1.1rem; font-weight:800; color:#1e293b; margin-bottom:4px; }
    .page-sub   { font-size:.82rem; color:#64748b; margin-bottom:24px; }

    .q-card { background:#fff; border-radius:12px; box-shadow:0 1px 4px rgba(0,0,0,.08); margin-bottom:20px; overflow:hidden; width:100%; max-width:100%; word-break:break-word; white-space:normal; overflow-wrap:anywhere; }
    .q-card.no-rawtext { border-left:3px solid #94a3b8; opacity:.85; }
    .q-header { padding:10px 16px; background:linear-gradient(135deg,#1e40af,#3b82f6); display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
    .q-year-badge { font-size:.75rem; font-weight:800; color:#fff; background:rgba(255,255,255,.18); padding:2px 10px; border-radius:20px; }
    .q-topic { font-size:.72rem; color:#bfdbfe; }
    .q-body  { padding:16px; width:100%; max-width:100%; word-break:break-word; white-space:pre-wrap; overflow-wrap:anywhere; }
    .q-text  { font-size:.92rem; line-height:1.75; color:#1e293b; white-space:pre-wrap; margin-bottom:14px; width:100%; max-width:100%; word-break:break-word; overflow-wrap:anywhere; }
    .choices { display:flex; flex-direction:column; gap:7px; margin-bottom:16px; }
    .choice-btn { width:100%; max-width:100%; text-align:left; padding:9px 14px; border-radius:8px; border:1.5px solid #e2e8f0; background:#f8fafc; font-size:.88rem; color:#334155; cursor:pointer; transition:all .15s; white-space:pre-wrap; line-height:1.55; word-break:break-word; overflow-wrap:anywhere; }
    .choice-btn:hover:not(.correct):not(.wrong):not(.dimmed) { background:#f1f5f9; border-color:#94a3b8; }
    .choice-btn.correct { background:#dcfce7; border-color:#22c55e; color:#15803d; font-weight:700; }
    .choice-btn.wrong   { background:#fee2e2; border-color:#ef4444; color:#b91c1c; }
    .choice-btn.dimmed  { opacity:.45; }
    .reveal-wrap { display:flex; justify-content:flex-end; }
    .reveal-btn { font-size:.82rem; font-weight:700; padding:7px 18px; border-radius:8px; border:1.5px solid #a5b4fc; background:#eef2ff; color:#4338ca; cursor:pointer; transition:all .15s; }
    .reveal-btn:hover { background:#e0e7ff; }
    .reveal-btn.revealed { background:#4338ca; color:#fff; border-color:#4338ca; }
    .answer-panel { margin-top:14px; padding:14px; background:#f0fdf4; border-radius:10px; border:1.5px solid #86efac; width:100%; max-width:100%; word-break:break-word; white-space:pre-wrap; overflow-wrap:anywhere; }
    .answer-line { font-size:.9rem; font-weight:800; color:#15803d; margin-bottom:8px; }
    .explanation { font-size:.85rem; line-height:1.75; color:#1e293b; white-space:pre-wrap; width:100%; max-width:100%; word-break:break-word; overflow-wrap:anywhere; }
    .q-images { display:flex; flex-wrap:wrap; gap:10px; margin-bottom:12px; }
    .q-images img { max-width:100%; height:auto; max-height:280px; border-radius:8px; border:1px solid #e2e8f0; object-fit:contain; cursor:pointer; }
    .image-pending-banner { margin:0 0 12px; padding:10px 12px; border-radius:10px; border:1.5px solid #fbbf24; background:#fffbeb; color:#92400e; font-size:.84rem; font-weight:700; line-height:1.55; }
    .image-pending-banner small { display:block; font-weight:500; color:#a16207; margin-top:2px; }

    .lightbox { display:none; position:fixed; inset:0; background:rgba(0,0,0,.85); z-index:9999; align-items:center; justify-content:center; }
    .lightbox.show { display:flex; }
    .lightbox img { max-width:92vw; height:auto; max-height:90vh; border-radius:8px; }
    .lightbox-close { position:fixed; top:16px; right:20px; color:#fff; font-size:2rem; cursor:pointer; background:none; border:none; line-height:1; }

    .step-type-bar { display:flex; gap:6px; padding:10px 16px; background:#f8fafc; border-bottom:1px solid #e2e8f0; flex-shrink:0; align-items:center; }
    .step-type-btn { padding:5px 14px; border-radius:20px; font-size:.78rem; font-weight:700; border:1.5px solid #e2e8f0; background:#fff; color:#475569; cursor:pointer; transition:all .15s; white-space:nowrap; }
    .step-type-btn.active { background:#7c3aed; color:#fff; border-color:#7c3aed; }
    .step-type-btn:hover:not(.active) { background:#f1f5f9; }

    .guide-section { margin-bottom:24px; }
    .guide-section-title { font-size:.82rem; font-weight:800; padding:8px 14px; background:linear-gradient(135deg,#1e40af,#3b82f6); color:#fff; border-radius:8px; margin-bottom:10px; }
    .guide-concept-list { display:flex; flex-direction:column; gap:6px; }
    .guide-concept-item { padding:8px 14px; background:#fff; border-radius:8px; border:1.5px solid #e2e8f0; font-size:.84rem; color:#334155; display:flex; align-items:center; gap:8px; }
    .rank-badge { font-size:.7rem; font-weight:800; background:#dbeafe; color:#1d4ed8; padding:2px 8px; border-radius:20px; white-space:nowrap; }
    .guide-freq-item { padding:10px 14px; background:#fff; border-radius:8px; border:1.5px solid #e2e8f0; font-size:.84rem; color:#334155; margin-bottom:8px; }
    .flow-card { background:#fff; border:1.5px solid #e2e8f0; border-radius:12px; padding:16px; margin-bottom:18px; }
    .mermaid-box { width:100%; max-width:100%; overflow-x:auto; background:#f8fafc; border-radius:10px; padding:12px; border:1px solid #e2e8f0; }
    .flow-desc { font-size:.82rem; line-height:1.7; color:#475569; padding:8px 0; border-bottom:1px solid #f1f5f9; }
    .emphasis-card { background:#fff; border:1.5px solid #e2e8f0; border-radius:12px; padding:14px 16px; margin-bottom:12px; }
    .emphasis-title { font-weight:800; color:#1e293b; margin-bottom:10px; }
    .emphasis-row { display:grid; grid-template-columns:96px 1fr; gap:10px; padding:7px 0; border-top:1px solid #f1f5f9; font-size:.84rem; line-height:1.65; }
    .emphasis-label { font-weight:800; color:#2563eb; }
    .login-screen { min-height:100dvh; display:flex; align-items:center; justify-content:center; background:radial-gradient(circle at 50% 40%,#eff6ff,#f8fafc 62%); padding:24px; }
    .login-card { width:min(420px,100%); background:#fff; border:1px solid #e2e8f0; border-radius:18px; box-shadow:0 18px 60px rgba(15,23,42,.12); padding:28px; }
    .login-logo { font-size:2.4rem; margin-bottom:8px; }
    .login-title { font-size:1.35rem; font-weight:900; color:#0f172a; margin-bottom:4px; }
    .login-sub { font-size:.86rem; color:#64748b; margin-bottom:18px; }
    .login-input { width:100%; border:1.5px solid #cbd5e1; border-radius:10px; padding:11px 12px; font-size:.95rem; margin-bottom:10px; }
    .login-btn { width:100%; border:none; border-radius:10px; background:#1e293b; color:#fff; font-weight:800; padding:11px 12px; }
    .login-error { color:#dc2626; font-size:.82rem; min-height:20px; margin-top:8px; }

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

  <script src="/vendor/react.production.min.js"></script>
  <script src="/vendor/react-dom.production.min.js"></script>
  <script async src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
  <script src="/vendor/babel.min.js"></script>
  <script type="text/babel">
    const { useState, useEffect, useMemo } = React;
    const DATE_ORDER = {'12/29':0,'12/30':1,'12/31':2,'01/02':3,'01/05':4,'기타':99};
    const TABS = ['강의록','기출','학습 가이드','3step','지엽'];
    const STEP_TYPES = ['야마형','심화형','지엽형'];
    if (window.mermaid) {
      window.mermaid.initialize({ startOnLoad: false, securityLevel: 'loose' });
    }

    function simpleHash(value) {
      let hash = 0;
      for (let i = 0; i < value.length; i++) hash = ((hash << 5) - hash) + value.charCodeAt(i);
      return String(hash >>> 0);
    }

    function LoginScreen({onLogin}) {
      const [password, setPassword] = useState('');
      const [error, setError] = useState('');
      useEffect(() => {
        if (!localStorage.getItem('viewerPasswordHash')) {
          localStorage.setItem('viewerPasswordHash', simpleHash('resp2025'));
        }
      }, []);
      function submit(event) {
        event.preventDefault();
        const expected = localStorage.getItem('viewerPasswordHash') || simpleHash('resp2025');
        if (simpleHash(password) === expected) {
          localStorage.setItem('loggedIn', 'true');
          onLogin();
        } else {
          setError('비밀번호가 맞지 않습니다.');
        }
      }
      return (
        <div className="login-screen">
          <form className="login-card" onSubmit={submit}>
            <div className="login-logo">🫁</div>
            <div className="login-title">호흡기 2차 기출 뷰어</div>
            <div className="login-sub">강의 직후 복습과 시험 전 압축 회독을 위한 학습 공간입니다.</div>
            <input className="login-input" type="password" placeholder="비밀번호" value={password} onChange={e => setPassword(e.target.value)} autoFocus />
            <button className="login-btn" type="submit">시작하기</button>
            <div className="login-error">{error}</div>
          </form>
        </div>
      );
    }

    function MermaidChart({code, chartKey}) {
      const ref = React.useRef(null);
      useEffect(() => {
        if (!ref.current || !code) return;
        let cancelled = false;
        let attempts = 0;
        function renderWhenReady() {
          if (cancelled || !ref.current) return;
          if (!window.mermaid) {
            ref.current.textContent = code;
            attempts += 1;
            if (attempts < 20) setTimeout(renderWhenReady, 250);
            return;
          }
          window.mermaid.initialize({ startOnLoad: false, securityLevel: 'loose' });
          const id = 'mermaid-' + chartKey.replace(/[^a-zA-Z0-9_-]/g, '-');
          window.mermaid.render(id, code)
            .then(({svg}) => { if (ref.current) ref.current.innerHTML = svg; })
            .catch(() => { if (ref.current) ref.current.textContent = code; });
        }
        renderWhenReady();
        return () => { cancelled = true; };
      }, [code, chartKey]);
      return <div className="mermaid-box" ref={ref} />;
    }

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

    function App() {
      const [isLoggedIn, setIsLoggedIn] = useState(() => localStorage.getItem('loggedIn') === 'true');
      const [lectures, setLectures] = useState([]);
      const [selected, setSelected] = useState(null);
      useEffect(() => {
        fetch('/api/lectures').then(r => r.json()).then(setLectures).catch(() => {});
      }, []);
      const totalQ = lectures.reduce((s, l) => s + l.q_count, 0);
      if (!isLoggedIn) return <LoginScreen onLogin={() => setIsLoggedIn(true)} />;
      return (
        <div style={{display:'flex',flexDirection:'column',height:'100dvh',overflow:'hidden'}}>
          <header className="app-header">
            <div style={{flex:1}}>
              <div className="brand">🫁 <span>호흡기 2차</span> 기출문제 뷰어</div>
              <div className="subtitle">2015–2025 역대 기출 · 차시별 분류</div>
            </div>
            <div style={{display:'flex',gap:8}}>
              <span className="stat-pill"><i className="bi bi-book me-1"/>{lectures.length}차시</span>
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

    function Sidebar({lectures, selectedKey, onSelect}) {
      const [query, setQuery] = useState('');
      const [sortMode, setSortMode] = useState('date');
      const filtered = useMemo(() => {
        const q = query.trim().toLowerCase();
        return lectures.filter(l =>
          !q ||
          l.session_display.toLowerCase().includes(q) ||
          l.professor.toLowerCase().includes(q) ||
          l.topic.toLowerCase().includes(q)
        );
      }, [lectures, query]);
      const grouped = useMemo(() => {
        if (sortMode === 'date') {
          const map = {};
          filtered.forEach(l => { const k = l.date || '기타'; if(!map[k]) map[k] = []; map[k].push(l); });
          return Object.entries(map).sort(([a],[b]) => (DATE_ORDER[a] || 50) - (DATE_ORDER[b] || 50));
        } else {
          const sorted = [...filtered].sort((a,b) => a.professor.localeCompare(b.professor,'ko'));
          const map = {};
          sorted.forEach(l => { const k = l.professor || '-'; if(!map[k]) map[k] = []; map[k].push(l); });
          return Object.entries(map);
        }
      }, [filtered, sortMode]);
      return (
        <aside className="sidebar-panel">
          <div className="sidebar-top">
            <div className="title-row">
              <h6>차시 목록</h6>
              <span className="badge bg-primary-subtle text-primary rounded-pill">{lectures.length}</span>
            </div>
            <div className="search-box">
              <i className="bi bi-search"/>
              <input type="text" placeholder="차시, 교수명, 토픽 검색…" value={query} onChange={e => setQuery(e.target.value)} />
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
            <div className="item-title" title={lecture.session_display}>{lecture.topic || lecture.session_display}</div>
            <div className="item-meta">
              <span className="prof-badge"><i className="bi bi-person-fill me-1"/>{lecture.professor}</span>
              {lecture.session_display && <span className="year-chip">{lecture.session_display}</span>}
              {yearsLabel && <span className="year-chip">{yearsLabel}</span>}
              <span className="count-chip">{lecture.q_count}문제</span>
            </div>
          </div>
        </div>
      );
    }

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

    function LectureTabContent({lecture}) {
      if (!lecture.has_lecture) return (
        <div className="viewer-placeholder">
          <div style={{fontSize:'2.5rem'}}>📭</div>
          <div className="placeholder-title">강의록 없음</div>
          <div className="placeholder-sub">이 차시는 강의록 파일이 없습니다.</div>
        </div>
      );
      const url = '/pdf/lecture/'+encodeURIComponent(lecture.key)+'.pdf';
      return (
        <React.Fragment>
          <div className="viewer-bar">
            <span className="vb-title">{lecture.session_display} · {lecture.topic}</span>
            <span className="mode-pill lec">📖 강의록</span>
            <span className="info-pill"><i className="bi bi-person-fill me-1"/>{lecture.professor}</span>
          </div>
          <div className="viewer-frame">
            <embed src={url} type="application/pdf" width="100%" height="100%" />
          </div>
        </React.Fragment>
      );
    }

    function QuestionList({lecture, questions, loading}) {
      return (
        <div className="question-scroll">
          <div className="page-title">{lecture.session_display} · {lecture.topic}</div>
          <div className="page-sub">총 {questions.length}문제 · 최신 연도 먼저 · 선지를 클릭하면 정오답이 표시됩니다</div>
          {loading && <div style={{textAlign:'center',padding:'40px 0',color:'#94a3b8'}}><span className="spinner-border spinner-border-sm me-2"/>불러오는 중…</div>}
          {!loading && questions.length === 0 && <div style={{textAlign:'center',padding:'40px 0',color:'#94a3b8'}}>문제가 없습니다.</div>}
          {!loading && questions.map((q, idx) => (
            <QuestionCard key={q.year+'-'+q.num+'-'+idx} q={q} index={idx+1} />
          ))}
        </div>
      );
    }

    function GuideTab({lecture, questions}) {
      const plan = lecture.lecture_plan || {};
      const units = lecture.study_units || [];
      const years = Object.entries(plan.questions_by_year || {}).map(([year, count]) => `${year}(${count})`).join(', ');
      const trendLabel = plan.trend === '증가' ? '▲ 증가' : plan.trend === '감소' ? '▼ 감소' : '→ 유지';
      const fieldLabels = [
        ['definition', '정의'],
        ['pathogenesis', '병인'],
        ['diagnostic_criteria', '진단기준'],
        ['features', '특징'],
        ['treatment', '치료'],
        ['key_emphasis', '핵심강조내용'],
      ];
      const cleanLabel = text => String(text || '').replace(/^\\d+\\.\\s*/, '').replace(/["\\\\]/g, '').slice(0, 28);
      const flowCode = useMemo(() => {
        if (!units.length) return '';
        const nodes = units.map((unit, i) => `U${i+1}["${cleanLabel(unit.unit_title || 'Unit '+(i+1))}"]`);
        const links = units.slice(1).map((_, i) => `U${i+1} --> U${i+2}`);
        return ['flowchart LR', ...nodes, ...links].join('\\n');
      }, [units]);
      return (
        <div className="question-scroll">
          <div className="page-title">{lecture.session_display} · 학습 가이드</div>
          <div className="page-sub">수업 직후 복습과 시험 전 회독을 모두 고려한 압축 학습 흐름</div>
          <div className="card mb-3">
            <div className="card-header fw-bold">📊 출제경향 분석</div>
            <div className="card-body">
              <div className="mb-2"><span className="badge bg-primary me-2">{lecture.professor}</span><span>{lecture.topic}</span></div>
              {years && <div className="small text-secondary mb-2">연도별 출제 수: {years}</div>}
              <div className="mb-2">추세: <span className="badge bg-info-subtle text-info-emphasis">{trendLabel}</span></div>
              <div>2026 예측: {plan.prediction || '생성된 예측 데이터가 없습니다.'}</div>
            </div>
          </div>
          {units.length > 0 && (
            <div className="guide-section">
              <div className="guide-section-title">📚 학습 흐름</div>
              <div className="flow-card">
                <MermaidChart code={flowCode} chartKey={lecture.key + '-flow'} />
                <div style={{marginTop:12}}>
                  {units.map((unit, i) => (
                    <div className="flow-desc" key={i}>
                      <strong>{unit.unit_title}</strong> — {(unit.definition || unit.key_emphasis || unit.summary || '').split(/[.!?。]/).slice(0, 2).join('. ').slice(0, 180)}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
          <div className="guide-section">
            <div className="guide-section-title">📌 핵심 강조 개념</div>
            {units.length === 0 && <div style={{color:'#94a3b8',padding:'16px'}}>생성된 개념 단위가 없습니다.</div>}
            {units.map((unit, i) => {
              const visibleRows = fieldLabels.filter(([field]) => unit[field]);
              if (!visibleRows.length) return null;
              return (
                <div className="emphasis-card" key={i}>
                  <div className="emphasis-title">{unit.unit_title}</div>
                  {(unit.keywords || []).map(keyword => <span key={keyword} className="badge bg-secondary-subtle text-secondary-emphasis me-1 mb-2">{keyword}</span>)}
                  {visibleRows.map(([field, label]) => (
                    <div className="emphasis-row" key={field}>
                      <div className="emphasis-label">{label}</div>
                      <div>{unit[field]}</div>
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
        </div>
      );
    }

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

      const yamaQs = useMemo(() => rotateChoices(questions).slice(0, 40), [questions]);
      const displayQs = stepType === '야마형' ? yamaQs : stepType === '심화형' ? deepQs : minorQs;
      const isLoading = stepType === '심화형' ? deepLoading : stepType === '지엽형' ? minorLoading : false;

      return (
        <React.Fragment>
          <div className="step-type-bar">
            {STEP_TYPES.map(t => (
              <button key={t} className={'step-type-btn'+(stepType===t?' active':'')} onClick={() => setStepType(t)}>{t}</button>
            ))}
            {!isLoading && <span className="badge bg-primary-subtle text-primary ms-auto">[{stepType} {displayQs.length}/40]</span>}
          </div>
          <div className="question-scroll">
            <div className="page-title">{lecture.session_display} — {stepType}</div>
            <div className="page-sub">
              {stepType === '야마형' && '핵심 빈출 문제 · 선지 순서 변형 적용'}
              {stepType === '심화형' && '핵심 개념 심화 문제 · 텍스트 전용'}
              {stepType === '지엽형' && '지엽 세부 지식 문제'}
            </div>
            {isLoading && <div style={{textAlign:'center',padding:'40px 0',color:'#94a3b8'}}><span className="spinner-border spinner-border-sm me-2"/>불러오는 중…</div>}
            {!isLoading && displayQs.length === 0 && <div style={{textAlign:'center',padding:'40px 0',color:'#94a3b8'}}>문제가 없습니다.</div>}
            {!isLoading && displayQs.map((q, idx) => (
              <QuestionCard key={stepType+'-'+(q.id || q.year+'-'+q.num)+'-'+idx} q={q} index={idx+1} />
            ))}
          </div>
        </React.Fragment>
      );
    }

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
          <div className="page-title">{lecture.session_display} — 지엽 정리</div>
          <div className="page-sub">강의록 내 비강조 요소 중 기출에 출제된 항목만 표시됩니다.</div>
          {loading && <div style={{textAlign:'center',padding:'40px 0',color:'#94a3b8'}}><span className="spinner-border spinner-border-sm me-2"/>불러오는 중…</div>}
          {!loading && minorData && minorData.length === 0 && <div style={{textAlign:'center',padding:'40px 0',color:'#94a3b8'}}>지엽 항목이 없습니다.</div>}
          {!loading && minorData && minorData.map((item, i) => (
            <div key={i} className="minor-card">
              <div className="minor-card-header">
                <span className="minor-card-title">키워드</span>
                <span className="minor-card-badge">{item.keyword}</span>
              </div>
              <div className="minor-card-body">
                <div className="minor-key-point"><strong>기출 맥락:</strong> {item.context}</div>
                <div className="minor-mnemonic"><strong>강의 맥락:</strong> {item.lecture_context}</div>
              </div>
            </div>
          ))}
        </div>
      );
    }

    function QuestionCard({q, index}) {
      const [chosen, setChosen] = useState(null);
      const [revealed, setRevealed] = useState(false);
      const [lightbox, setLightbox] = useState(null);
      const questionLabel = q.year === '3step' ? `3step Q${q.num}` : `${q.year}년 Q${q.num}`;
      const PHOTO_KEYWORDS = ['사진', '그림', '영상', 'CT', 'PET', 'X-ray', 'X선', 'X-선', '소견이다', '소견은', '촬영'];
      const hasPhotoText = PHOTO_KEYWORDS.some(k => String(q.question_text || '').toLowerCase().includes(k.toLowerCase()));
      const hasQuestionImages = (q._images || []).length > 0;
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
          <div className={'q-card'+(q.no_rawtext ? ' no-rawtext' : '')}>
            <div className="q-header">
              <span className="q-year-badge">{questionLabel}</span>
              {q.no_rawtext && <span className="badge bg-secondary ms-1">원문없음</span>}
              <span className="q-topic">[{q.professor}] {q.topic}</span>
            </div>
            <div className="q-body">
              <div className="q-text">{q.question_text}</div>
              {q.data_quality_issue && (
                <div className="image-pending-banner">
                  데이터 없음
                  <small>{q.data_quality_issue}로 원문 노출을 중단했습니다. 이미지나 해설이 있는 경우에만 보조 자료로 확인하세요.</small>
                </div>
              )}
              {hasPhotoText && !hasQuestionImages && (
                <div className="image-pending-banner">
                  이미지 준비 중
                  <small>사진/영상 기반 발문입니다. 원본 이미지가 복구되기 전까지 발문만으로 판단하지 마세요.</small>
                </div>
              )}
              {hasQuestionImages && (
                <div className="q-images">
                  {q._images.map(img => (
                    <img key={img} src={'/static/images/'+img} alt="문제 이미지" onClick={() => setLightbox('/static/images/'+img)} />
                  ))}
                </div>
              )}
              <div className="choices">
                {(q._real_choices || []).length === 0 && hasQuestionImages && (
                  <div style={{color:'#64748b',fontSize:'.86rem'}}>이미지 문제 (선지 이미지 확인)</div>
                )}
                {(q._real_choices || []).length === 0 && !hasQuestionImages && !hasPhotoText && (
                  <div style={{color:'#94a3b8',fontSize:'.86rem'}}>데이터 없음</div>
                )}
                {(q._real_choices || []).map((ch, i) => {
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
                  <div className="answer-line">정답: {q.answer || '정답 데이터 없음'}</div>
                  {q.solution_images && q.solution_images.length > 0 && (
                    <div className="q-images">
                      {q.solution_images.map(img => (
                        <img key={img} src={'/static/solutions/'+img} alt="풀이 이미지" onClick={() => setLightbox('/static/solutions/'+img)} />
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

    function Placeholder() {
      return (
        <div className="viewer-placeholder">
          <div className="placeholder-icon">📄</div>
          <div className="placeholder-title">차시를 선택하세요</div>
          <div className="placeholder-sub">왼쪽 목록에서 차시를 클릭하면 학습을 시작할 수 있습니다</div>
        </div>
      );
    }

    ReactDOM.createRoot(document.getElementById('root')).render(<App />);
  </script>
</body>
</html>
"""


SOLUTION_IDX = build_solution_index()
SOLUTION_FILENAMES = {filename for filenames in SOLUTION_IDX.values() for filename in filenames}
LECTURE_PLAN = load_json_file(LECTURE_PLAN_PATH, {})
STUDY_GUIDE = load_json_file(STUDY_GUIDE_PATH, {})
THREESTEP_DEEP = load_json_file(THREESTEP_DEEP_PATH, {})
THREESTEP_MINOR = load_json_file(THREESTEP_MINOR_PATH, {})
MINOR_TOPICS = load_json_file(MINOR_TOPICS_PATH, {})
META, META_BY_KEY, QUESTION_IDX = load_data()


@app.route("/")
def index():
    return HTML_TEMPLATE


@app.route("/vendor/<path:filename>")
def vendor_file(filename):
    return send_from_directory(OUTPUT_DIR / "vendor", filename)


@app.route("/static/solutions/<path:filename>")
def solution_image(filename):
    return send_from_directory(SOLUTION_DIR, filename)


@app.route("/api/lectures")
def api_lectures():
    return jsonify(META)


@app.route("/api/questions/<session_key>")
def api_questions(session_key):
    if session_key not in META_BY_KEY:
        abort(404)
    return jsonify([serialize_question(question) for question in QUESTION_IDX.get(session_key, [])])


@app.route("/api/3step/deep/<session_key>")
def api_3step_deep(session_key):
    if session_key not in META_BY_KEY:
        abort(404)
    return jsonify([serialize_generated_question(q) for q in THREESTEP_DEEP.get(session_key, [])[:40]])


@app.route("/api/3step/minor/<session_key>")
def api_3step_minor(session_key):
    if session_key not in META_BY_KEY:
        abort(404)
    return jsonify([serialize_generated_question(q) for q in THREESTEP_MINOR.get(session_key, [])[:40]])


@app.route("/api/minor/<session_key>")
def api_minor(session_key):
    if session_key not in META_BY_KEY:
        abort(404)
    return jsonify(MINOR_TOPICS.get(session_key, []))


@app.route("/pdf/lecture/<session_key>.pdf")
def pdf_lecture(session_key):
    if session_key not in META_BY_KEY:
        abort(404)

    pdf_files = LECTURE_FILES.get(session_key, [])
    if not pdf_files:
        abort(404)

    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError as exc:
        raise RuntimeError("pypdf is required to merge lecture PDFs.") from exc

    writer = PdfWriter()
    merged_any = False
    for pdf_name in pdf_files:
        path = lecture_file_path(pdf_name)
        if path is None:
            continue
        reader = PdfReader(str(path))
        for page in reader.pages:
            writer.add_page(page)
        merged_any = True

    if not merged_any:
        abort(404)

    buffer = io.BytesIO()
    writer.write(buffer)
    buffer.seek(0)
    return send_file(buffer, mimetype="application/pdf", download_name=f"{session_key}.pdf")


if __name__ == "__main__":
    print("=" * 56)
    print("호흡기 2차 past exam question viewer ready")
    print("localhost:8080 에서 확인하세요")
    print("=" * 56)
    app.run(host="0.0.0.0", port=8080, debug=False)
