#!/usr/bin/env python3
"""
기출문제 강의록별 분류 스크립트
- 풀이.pdf에서 각 문제의 페이지 범위와 주제를 추출
- 주제를 강의록 파일과 매핑
- 강의록별 문제+풀이 PDF 생성
"""

import os
import re
import pdfplumber
from pypdf import PdfWriter, PdfReader

BASE_DIR = "/Users/ddoli1545/Desktop/test"
SOLUTIONS_PDF = os.path.join(BASE_DIR, "2025 호흡기 1차 풀이.pdf")
LECTURE_DIR = os.path.join(BASE_DIR, "호흡기 (1)", "호흡기 (1) 강의록")
OUTPUT_DIR = os.path.join(BASE_DIR, "강의록별_기출문제")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 주제 → 강의록 파일 매핑
# 키: solutions PDF의 '주제' 필드 (부분 일치로 검색)
# 값: 강의록 파일명 (prefix 일치)
TOPIC_TO_LECTURE = [
    # (주제 키워드, 출력 파일명 prefix, 강의록 파일 prefix 목록)
    (
        ["호흡기 질환의 주요증상", "호흡기 진찰"],
        "1218_호흡기질환주요증상_진찰및진단방법",
        ["1218 1교시", "1218 2교시"],
    ),
    (
        ["기관지천식", "천식"],
        "1223_천식_진단및치료",
        ["1223 3교시", "1223 4교시"],
    ),
    (
        ["뒷가슴벽의 구조"],
        "1216_뒷가슴벽구조_종격동",
        ["1216 7교시"],
    ),
    (
        ["가슴벽의 구조"],
        "1216_가슴벽의구조",
        ["1216 3교시"],
    ),
    (
        ["폐의 구조"],
        "1216_폐의구조",
        ["1216 4교시"],
    ),
    (
        ["호흡기의 해부학적 구조"],
        "1216_호흡기해부학적구조",
        ["1216 5교시"],
    ),
    (
        ["호흡상피의 조직학적"],
        "1216_호흡상피조직학적구조와기능",
        ["1216 5교시", "1216 6교시"],
    ),
    (
        ["폐 병리학 용어", "급성 폐 손상", "폐쇄폐질환"],
        "1224_폐병리학개요",
        ["1224 1교시"],
    ),
    (
        ["감염성 폐질환"],
        "1224_감염성폐질환",
        ["1224 2교시"],
    ),
    (
        ["호흡생리학"],
        "1217_호흡생리학",
        ["1217 1,2교시"],
    ),
    (
        ["동맥혈가스분석", "저산소혈증"],
        "1217_동맥혈가스분석_저산소혈증",
        ["1217 3교시"],
    ),
    (
        ["정상 흉부"],
        "1218_정상흉부영상의학",
        ["1218 4교시"],
    ),
    (
        ["흉부질환의 영상의학 소견 유형", "흉부질환 영상의학 소견 유형"],
        "1218_흉부질환영상의학소견유형분석",
        ["1218 4교시"],
    ),
    (
        ["기도 및 간질성 폐질환", "폐부종과 폐색전증의 영상의학"],
        "1224_기도간질성폐질환_폐부종_폐색전증영상의학",
        ["1224 7교시", "1224 8교시"],
    ),
    (
        ["상기도 질환", "급성기관지염"],
        "1218_상기도질환_급성기관지염",
        ["1218 5교시"],
    ),
    (
        ["폐색전증의 임상소견", "폐색전증의 치료", "지방색전증"],
        "1223_폐색전증",
        ["1223 1교시", "1223 2교시"],
    ),
    (
        ["환기장애", "수면무호흡"],
        "1224_환기장애_수면무호흡",
        ["1224 5교시"],
    ),
    (
        ["직업성", "환경성 폐질환"],
        "1224_직업성환경성폐질환",
        ["1224 6교시"],
    ),
    (
        ["지역사회획득폐렴"],
        "1218_지역사회획득폐렴",
        ["1218 6교시"],
    ),
    (
        ["병원획득폐렴", "흡인성 폐렴"],
        "1218_병원획득폐렴_흡인성폐렴",
        ["1218 7교시"],
    ),
    (
        ["폐농양"],
        "1222_폐농양_기타폐감염",
        ["1222 1교시"],
    ),
    (
        ["폐결핵의 진단"],
        "1222_폐결핵진단",
        ["1222 2교시"],
    ),
    (
        ["폐결핵의 치료"],
        "1222_폐결핵치료",
        ["1222 3교시"],
    ),
    (
        ["만성폐쇄성폐질환", "만선폐쇄성폐질환"],
        "1223_COPD",
        ["1223 5교시", "1223 6교시"],
    ),
    (
        ["기관지확장증"],
        "1222_기관지확장증",
        ["1222 4교시"],
    ),
    (
        ["호흡기질환의 치료약제 (1)", "호흡기질환의 치료약제(1)"],
        "1218_1224_호흡기치료약제1",
        ["1218 3교시", "1224 3교시"],
    ),
    (
        ["호흡기질환의 치료약제 (2)", "호흡기질환의 치료약제(2)"],
        "1224_호흡기치료약제2",
        ["1224 4교시"],
    ),
    # 폐기능 검사 (문제가 없을 수도 있음)
    (
        ["폐기능 검사"],
        "1217_폐기능검사",
        ["1217 4교시"],
    ),
    # 과정 소개 (문제가 없을 수도 있음)
    (
        ["호흡기 과정소개", "과정소개"],
        "1216_호흡기과정소개",
        ["1216 2교시"],
    ),
]


def match_topic(topic_text):
    """주제 텍스트를 매핑 테이블에서 찾기"""
    for keywords, output_prefix, lecture_prefixes in TOPIC_TO_LECTURE:
        for kw in keywords:
            if kw in topic_text:
                return output_prefix, lecture_prefixes
    return None, None


def parse_solutions_pdf():
    """풀이 PDF에서 각 문제의 페이지 범위와 주제 추출"""
    questions = []
    with pdfplumber.open(SOLUTIONS_PDF) as pdf:
        total_pages = len(pdf.pages)
        current_q = None

        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            if "문제번호" in text and ("교수님" in text or "주제" in text):
                # 새 문제 시작
                if current_q:
                    current_q["end_page"] = i  # 0-indexed, exclusive
                    questions.append(current_q)

                # 문제 번호 추출
                num_match = re.search(r"문제번호\s*(\d+)", text)
                q_num = int(num_match.group(1)) if num_match else 0

                # 주제 추출 (여러 패턴 처리)
                lines = text.split("\n")
                topic = ""
                for j, line in enumerate(lines):
                    if line.startswith("주제"):
                        topic = line.replace("주제", "").strip()
                        # 다음 줄에 이어지는 경우 (해설자/감수자가 없으면 다음 줄도 주제)
                        if j + 1 < len(lines):
                            next_line = lines[j + 1]
                            if not any(
                                x in next_line
                                for x in ["해설자", "감수자", "문제", "교수님"]
                            ):
                                topic += " / " + next_line.strip()
                        break

                current_q = {
                    "num": q_num,
                    "topic": topic,
                    "start_page": i,  # 0-indexed
                    "end_page": total_pages,  # 기본값 (마지막 문제)
                }

        if current_q:
            questions.append(current_q)

    return questions


def find_lecture_files(lecture_prefixes):
    """강의록 파일 찾기 (macOS NFD 정규화 처리)"""
    import unicodedata
    found = []
    for prefix in lecture_prefixes:
        prefix_nfc = unicodedata.normalize("NFC", prefix)
        for fname in sorted(os.listdir(LECTURE_DIR)):
            fname_nfc = unicodedata.normalize("NFC", fname)
            if fname_nfc.startswith(prefix_nfc) and fname_nfc.endswith(".pdf"):
                found.append(os.path.join(LECTURE_DIR, fname))
                break
    return found


def create_output_pdf(output_prefix, question_pages, lecture_files):
    """강의록 + 해당 문제들을 합쳐서 새 PDF 생성"""
    writer = PdfWriter()

    # 강의록 추가
    for lf in lecture_files:
        if os.path.exists(lf):
            reader = PdfReader(lf)
            for page in reader.pages:
                writer.add_page(page)
            print(f"  강의록 추가: {os.path.basename(lf)} ({len(reader.pages)}p)")
        else:
            print(f"  [경고] 강의록 파일 없음: {lf}")

    # 문제 페이지 추가
    solutions_reader = PdfReader(SOLUTIONS_PDF)
    q_page_count = 0
    for start, end in question_pages:
        for page_idx in range(start, end):
            writer.add_page(solutions_reader.pages[page_idx])
            q_page_count += 1

    out_path = os.path.join(OUTPUT_DIR, f"{output_prefix}.pdf")
    with open(out_path, "wb") as f:
        writer.write(f)
    print(f"  → 저장: {out_path} (문제 {q_page_count}p)")
    return out_path


def main():
    print("=== 기출문제 강의록별 분류 시작 ===\n")

    # 1. 풀이 PDF 파싱
    print("[1단계] 풀이 PDF 파싱 중...")
    questions = parse_solutions_pdf()
    print(f"  총 {len(questions)}개 문제 발견\n")

    # 2. 문제별 주제 매핑
    print("[2단계] 주제 → 강의록 매핑 중...")
    lecture_to_questions = {}  # output_prefix → [(start, end), ...]
    unmatched = []

    for q in questions:
        output_prefix, lecture_prefixes = match_topic(q["topic"])
        if output_prefix:
            if output_prefix not in lecture_to_questions:
                lecture_to_questions[output_prefix] = {
                    "lecture_prefixes": lecture_prefixes,
                    "pages": [],
                    "q_nums": [],
                }
            lecture_to_questions[output_prefix]["pages"].append(
                (q["start_page"], q["end_page"])
            )
            lecture_to_questions[output_prefix]["q_nums"].append(q["num"])
            print(f"  Q{q['num']:2d} [{q['topic'][:40]}] → {output_prefix}")
        else:
            unmatched.append(q)
            print(f"  Q{q['num']:2d} [미매핑] 주제: {q['topic']}")

    # 3. 강의록별 PDF 생성
    print(f"\n[3단계] 강의록별 PDF 생성 중... ({len(lecture_to_questions)}개 파일)")
    created = []
    for output_prefix, data in sorted(lecture_to_questions.items()):
        print(f"\n  [{output_prefix}] 문제 {data['q_nums']}")
        lecture_files = find_lecture_files(data["lecture_prefixes"])
        out_path = create_output_pdf(output_prefix, data["pages"], lecture_files)
        created.append(out_path)

    print(f"\n=== 완료 ===")
    print(f"생성된 파일 수: {len(created)}")
    print(f"저장 위치: {OUTPUT_DIR}")
    if unmatched:
        print(f"\n미매핑 문제 ({len(unmatched)}개):")
        for q in unmatched:
            print(f"  Q{q['num']}: {q['topic']}")


if __name__ == "__main__":
    main()
