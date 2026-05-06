#!/usr/bin/env python3
"""풀이 PDF에서 각 문제별 이미지를 추출해 static/images/ 에 저장"""
import fitz
import os
import re
from pathlib import Path

BASE    = Path('/Users/ddoli1545/Desktop/test')
SOL_DIR = BASE / '역대 야마풀이'
IMG_DIR = BASE / 'static' / 'images'
IMG_DIR.mkdir(parents=True, exist_ok=True)

# year → solution PDF filename
YEAR_PDFS = {
    2015: '2015 호흡기학 1차 풀이.pdf',
    2016: '2016 호흡기학 1차 풀이.pdf',
    2017: '2017 호흡기학 1차 풀이.pdf',
    2019: '2019 호흡기학 1차 풀이.pdf',
    2021: '2021 호흡기 1차 풀이.pdf',
    2022: '2022 호흡기 1차 풀이.pdf',
    2023: '2023 호흡기 1차 풀이.pdf',
    2025: '2025 호흡기 1차 풀이.pdf',
}

MIN_W     = 80
MIN_H     = 80
MIN_BYTES = 5_000


def extract_year(year: int, pdf_path: Path) -> int:
    doc = fitz.open(str(pdf_path))

    # 페이지별 문제번호 파악
    page_to_q: dict[int, int] = {}
    cur_q = None
    for i, page in enumerate(doc):
        text = page.get_text()
        m = re.search(r'문제번호\s*(\d+)', text)
        if m:
            cur_q = int(m.group(1))
        if cur_q is not None:
            page_to_q[i] = cur_q

    # 문제번호 → 해당 페이지 목록
    q_pages: dict[int, list[int]] = {}
    for pg, q in page_to_q.items():
        q_pages.setdefault(q, []).append(pg)

    saved = 0
    for q_num, pages in sorted(q_pages.items()):
        img_idx   = 0
        seen_xref = set()
        for pg_i in pages:
            for img in doc[pg_i].get_images(full=True):
                xref = img[0]
                if xref in seen_xref:
                    continue
                seen_xref.add(xref)
                try:
                    bi   = doc.extract_image(xref)
                    w, h = bi['width'], bi['height']
                    data = bi['image']
                    ext  = bi['ext']
                    if w < MIN_W or h < MIN_H or len(data) < MIN_BYTES:
                        continue
                    out = IMG_DIR / f'{year}_Q{q_num}_{img_idx}.{ext}'
                    out.write_bytes(data)
                    img_idx += 1
                    saved   += 1
                except Exception as e:
                    print(f'  [warn] xref={xref}: {e}')
    doc.close()
    return saved


def main():
    total = 0
    for year, fn in sorted(YEAR_PDFS.items()):
        path = SOL_DIR / fn
        if not path.exists():
            print(f'{year}: 파일 없음 ({fn})')
            continue
        n = extract_year(year, path)
        print(f'{year}: {n}개 이미지 저장')
        total += n
    print(f'\n총 {total}개 이미지 → {IMG_DIR}')


if __name__ == '__main__':
    main()
