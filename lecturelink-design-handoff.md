# LectureLink UI/UX 디자인 핸드오프 명세서

> 이 문서는 LectureLink(의대생 AI 학습 플랫폼) 랜딩 페이지의 디자인 시스템과 UX 구조를 정리한 것입니다.
> 다른 Claude 세션에서 기능을 구현할 때, 이 문서의 디자인 토큰·컴포넌트·인터랙션 패턴을 그대로 적용해 주세요.
> **기능 로직은 상대 세션의 베이스를 따르되, 시각적 표현과 인터랙션 패턴은 본 명세서를 기준으로 합니다.**

---

## 1. 프로젝트 개요

- **서비스명**: LectureLink (렉처링크)
- **타겟**: 의대생 + 메디컬 종사자
- **핵심 가치**: 학교 야마(족보) + 교수님 강의록 + KMLE 기출을 AI로 단일화
- **현재 단계**: 베타 테스트
- **핵심 카피**:
  - 메인: `야마와 KMLE를 AI로 단일화`
  - 서브: `교수님별 강의록 기반 맞춤형 AI 튜터`
- **컨셉**: "수술복(Scrub)의 편안함 + 정밀 의료기기의 깨끗함" / Clean & Professional Medical

---

## 2. 디자인 토큰

### 2.1 컬러 팔레트

| 토큰 | HEX | 용도 |
|---|---|---|
| `--primary` | `#8CBDB3` | Light Teal — 브랜드 핵심, 아이콘 배경, 보조 강조 |
| `--accent` | `#E67E22` | Soft Orange — CTA, 핵심 키워드 강조, 액티브 상태 |
| `--text-primary` | `#2F4F4F` | Dark Slate Gray — 본문, 헤딩 |
| `--text-muted` | `#2F4F4F at opacity 0.55–0.7` | 서브 카피, 부가 설명 |
| `--bg` | `#FFFFFF` | 메인 배경 (반드시 흰색 유지) |
| `--bg-soft` | `#FAFBFB` | 섹션 분할 배경 |
| `--bg-tinted` | `#F5F9F8` | 뱃지·아이콘 컨테이너 배경 |
| `--bg-gray` | `#F7F8F7` | 약관 박스 등 비활성 정보 배경 |
| `--border-soft` | `#E5EAE8`, `#D3D9D4` | 연한 보더 |
| `--warning-bg` | `#FFF4E6` | 경고 알림 박스 배경 |
| `--warning-border` | `#F5D1A9` | 경고 알림 박스 보더 |

### 2.2 타이포그래피

```css
font-family: 'LINESeedKR', 'IBM Plex Sans KR', 'Apple SD Gothic Neo',
             -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
```

- **본문 자간**: `letter-spacing: -0.03em`
- **헤딩 자간**: `letter-spacing: -0.05em` (h1, h2, h3 모두 동일하게 타이트)
- **굵기 시스템**: 400 (regular) / 500 (medium) / 700 (bold) / 800 (extra-bold)
- **수치 강조**: `font-feature-settings: "tnum"` + `font-weight: 800` (carded numbers)

#### 폰트 로드
```css
@font-face {
  font-family: 'LINESeedKR';
  font-weight: 400;
  src: url('https://cdn.jsdelivr.net/gh/webfontworld/lineseed/LINESeedKR-Rg.woff2') format('woff2');
  font-display: swap;
}
@font-face {
  font-family: 'LINESeedKR';
  font-weight: 700;
  src: url('https://cdn.jsdelivr.net/gh/webfontworld/lineseed/LINESeedKR-Bd.woff2') format('woff2');
  font-display: swap;
}
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@100;200;300;400;500;600;700&display=swap');
```

### 2.3 라운드/모서리 시스템

전체 톤은 "둥글둥글한 부드러움". 모든 카드·버튼은 24px 이상 라운드 권장.

| 용도 | Tailwind | px |
|---|---|---|
| 작은 뱃지 / pill | `rounded-full` | ∞ |
| 입력창, 검색바 | `rounded-full` | ∞ |
| 작은 아이콘 컨테이너 | `rounded-2xl` | 16 |
| 일반 카드 (지표, 기능, 업로드) | `rounded-3xl` | 24 |
| 대형 섹션 박스, CTA 컨테이너 | `rounded-[2.5rem]` | 40 |

### 2.4 그림자

- **기본 카드**: `shadow-sm` 또는 보더만
- **호버 카드**: `hover:shadow-xl hover:-translate-y-1`
- **포커스 검색바**: `focus-within:shadow-lg`
- **강조 알약/박스**: `shadow-2xl`

### 2.5 트랜지션 / 인터랙션

- 기본: `transition` (Tailwind 기본 ~150ms)
- 카드 호버: `hover:-translate-y-1`
- 버튼 호버: `hover:shadow-lg hover:-translate-y-0.5`
- 라이브 포인트: `animate-pulse`
- 카운트업 애니메이션: `requestAnimationFrame` + easeOutCubic, 1.8s

---

## 3. 페이지 구조 (섹션 순서)

1. **Header (Sticky)** — 로고 + 네비게이션 + 시작하기 버튼
2. **Hero** — 베타 뱃지 + 메인 카피 + 서브 카피 + 검색/업로드/약관 동의 블록
3. **Why LectureLink** — "기술 신뢰도와 학습 데이터로 보는 LectureLink만의 장점" + 4개 지표 카드(Live count + 3 metrics)
4. **Core Features** — "본과생의 시간을 설계하는 3가지 엔진" + 3개 기능 카드
5. **How it Works** — "복잡한 과정, 단 3단계" + 3단계 스텝
6. **Trust / Tech** — AI 토큰 최적화(다크) + 안전한 데이터 관리(화이트) 듀얼 카드
7. **CTA** — "오늘 밤, 더 효율적으로 공부하세요" + 베타 무료 안내
8. **Footer** — 로고 + 링크 + 카피라이트

---

## 4. 핵심 컴포넌트 명세

### 4.1 로고 (SVG)

```jsx
const Logo = ({ size = 36 }) => (
  <svg width={size} height={size} viewBox="0 0 40 40" fill="none">
    <rect x="2" y="2" width="36" height="36" rx="10" fill="#8CBDB3"/>
    <path d="M13 14 Q13 11 16 11 L19 11 Q22 11 22 14 L22 17"
          stroke="white" strokeWidth="2.2" strokeLinecap="round" fill="none"/>
    <path d="M27 26 Q27 29 24 29 L21 29 Q18 29 18 26 L18 23"
          stroke="white" strokeWidth="2.2" strokeLinecap="round" fill="none"/>
    <circle cx="20" cy="20" r="2.2" fill="#E67E22"/>
  </svg>
);
```

- 두 개의 'L' 모양이 맞물려 "Link(연결)"를 시각화
- 중앙 오렌지 닷이 "연결의 핵심" 포인트

### 4.2 Hero 메인 카피

```jsx
<h1 className="text-4xl md:text-6xl leading-[1.25] text-center" style={{ color: '#2F4F4F' }}>
  <span style={{ color: '#E67E22' }}>야마</span>와{' '}
  <span style={{ color: '#E67E22' }}>KMLE</span>를
  <br />
  <span style={{ color: '#8CBDB3', fontWeight: 800, fontSize: '1.05em' }}>AI</span>로 단일화
</h1>
```

- **야마 / KMLE**: 오렌지 `#E67E22`
- **AI**: 라이트 틸 `#8CBDB3` + ExtraBold 800 + 1.05em
- **나머지**: 다크 슬레이트 `#2F4F4F`
- 배경 박스 없음 (clean typography)

### 4.3 Hero 배경 (Floating Logos)

```jsx
const bgLogos = [
  { top: '6%',  left: '5%',   size: 42, opacity: 0.08, rotate: -15 },
  { top: '14%', right: '8%',  size: 64, opacity: 0.06, rotate: 14 },
  { top: '28%', left: '3%',   size: 32, opacity: 0.08, rotate: 22 },
  // ... 총 12개 로고를 비대칭으로 산포
];
```

- 12개 로고 아이콘을 히어로 영역에 산포
- 크기: 28~76px / 투명도: 5~8% / 회전: ±30°
- `pointer-events-none` 필수 (인터랙션 방해 금지)
- AI 플랫폼의 정제된 분위기 연출

### 4.4 베타 뱃지

```jsx
<div className="flex items-center gap-2 px-4 py-1.5 rounded-full border"
     style={{ backgroundColor: '#F5F9F8', borderColor: '#8CBDB3' }}>
  <Sparkles size={14} style={{ color: '#8CBDB3' }} />
  <span className="text-xs" style={{ color: '#2F4F4F', fontWeight: 700 }}>
    베타 테스트 진행 중
  </span>
</div>
```

### 4.5 검색바 (약관 동의 연동 — 핵심 인터랙션)

```jsx
const [termsAgreed, setTermsAgreed] = useState(false);

<div className="relative bg-white rounded-full shadow-md border border-gray-100
                flex items-center pl-7 pr-5 py-1.5 transition">
  <input
    type="text"
    placeholder={termsAgreed ? '교수명 · 강의록 주제 검색' : '이용약관 동의 후 검색 가능합니다'}
    disabled={!termsAgreed}
    className="flex-1 py-3 outline-none bg-transparent text-sm"
  />
  <button
    disabled={!termsAgreed}
    style={{
      backgroundColor: termsAgreed ? '#E67E22' : '#D3D9D4',
      color: '#FFFFFF',
    }}
    className={`w-10 h-10 rounded-full flex items-center justify-center
                ${termsAgreed ? 'cursor-pointer hover:scale-110' : 'cursor-not-allowed'}`}
  >
    <Search size={18} strokeWidth={2.5} />
  </button>
</div>
```

**동작 규칙 (반드시 준수)**:
- 약관 미동의 → 돋보기 버튼 회색 `#D3D9D4`, disabled, placeholder 변경
- 약관 동의 시 → 돋보기 버튼 **오렌지 `#E67E22`**, 클릭 가능, 호버 시 1.1배 확대

### 4.6 업로드 카드 (점선 보더)

```jsx
<button className="w-full bg-white border-2 border-dashed rounded-3xl p-5
                   flex items-center gap-4
                   hover:border-[#8CBDB3] hover:bg-[#F5F9F8] transition group"
        style={{ borderColor: '#D3D9D4' }}>
  <div className="w-14 h-14 rounded-2xl flex items-center justify-center"
       style={{ backgroundColor: '#F5F9F8' }}>
    <UploadIcon size={36} />  {/* 파일+상단 화살표 SVG */}
  </div>
  <div className="flex-1">
    <div style={{ fontWeight: 700 }}>내 강의록 업로드하고 분석하기</div>
    <div className="text-xs" style={{ color: '#9CA3AF' }}>[베타테스트 이후 추가 예정]</div>
  </div>
  <ArrowRight size={18} className="group-hover:translate-x-1" style={{ color: '#8CBDB3' }} />
</button>
```

#### 업로드 아이콘 SVG
```jsx
const UploadIcon = ({ size = 56 }) => (
  <svg width={size} height={size} viewBox="0 0 64 64" fill="none">
    <path d="M32 10 V34" stroke="#8CBDB3" strokeWidth="3" strokeLinecap="round"/>
    <path d="M22 20 L32 10 L42 20" stroke="#8CBDB3" strokeWidth="3"
          strokeLinecap="round" strokeLinejoin="round" fill="none"/>
    <path d="M12 40 V50 C12 52.7614 14.2386 55 17 55 H47 C49.7614 55 52 52.7614 52 50 V40"
          stroke="#2F4F4F" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
    <circle cx="48" cy="18" r="3" fill="#E67E22"/>
  </svg>
);
```

### 4.7 이용약관 박스

- **위치**: 업로드 카드 바로 아래, 직접 업로드 링크 아래
- **사이즈**: `h-56` 고정, `overflow-y-auto` 내부 스크롤
- **배경**: `#F7F8F7`, 보더 `#E5EAE8`
- **헤더**: `[LectureLink] 베타 서비스 이용약관` (Bold 13px) + 시행일
- **구조**: 7개 조항 (제1조 ~ 제7조)
- **법적 경고 박스**: 제4조 하단, 오렌지 톤 `#FFF4E6` 배경 + `AlertTriangle` 아이콘 + "5년 이하 징역 또는 5천만 원 이하 벌금" 강조
- **커스텀 스크롤바**:
  ```css
  .terms-scroll::-webkit-scrollbar { width: 6px; }
  .terms-scroll::-webkit-scrollbar-thumb { background: #D3D9D4; border-radius: 3px; }
  .terms-scroll::-webkit-scrollbar-thumb:hover { background: #8CBDB3; }
  ```

### 4.8 약관 동의 체크박스 (커스텀)

```jsx
<label className="flex items-start gap-3 cursor-pointer group select-none
                  p-3 rounded-2xl transition hover:bg-gray-50">
  <input type="checkbox" checked={termsAgreed}
         onChange={(e) => setTermsAgreed(e.target.checked)}
         className="sr-only" />
  <div className="w-5 h-5 rounded-md border-2 flex items-center justify-center transition"
       style={{
         backgroundColor: termsAgreed ? '#E67E22' : '#FFFFFF',
         borderColor: termsAgreed ? '#E67E22' : '#C9D1CD',
       }}>
    {termsAgreed && <Check size={14} strokeWidth={3.5} className="text-white" />}
  </div>
  <span className="text-xs">
    <span style={{ color: '#E67E22', fontWeight: 700 }}>[필수]</span>{' '}
    위 약관을 모두 읽었으며, 자료 유출 금지 및 이용 조건에 동의합니다
  </span>
</label>
```

### 4.9 라이브 카운트 카드 (강의록 카운트업)

```jsx
const [uploadCount, setUploadCount] = useState(0);

useEffect(() => {
  const target = 542;  // 실제 운영 시 API에서 받아오기
  const duration = 1800;
  const start = performance.now();
  const tick = (now) => {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);  // easeOutCubic
    setUploadCount(Math.floor(eased * target));
    if (progress < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}, []);
```

- 0 → 542 (또는 실제 값) 까지 1.8초 카운트업
- easeOutCubic 곡선으로 자연스러운 감속
- `toLocaleString()` 으로 천 단위 콤마 자동 처리
- 카드 보더: 2px 오렌지 `#E67E22`
- 좌상단 LIVE 인디케이터: `animate-pulse` 오렌지 닷 + "LIVE" 라벨
- 숫자 폰트: ExtraBold 800, `font-feature-settings: "tnum"`

### 4.10 지표 카드 (3종)

| 메트릭 | 값 | 라벨 | 설명 |
|---|---|---|---|
| 매칭 정확도 | 98.7% | Target 아이콘 | 족보–KMLE 연결 정밀도 |
| 요약 일관성 | 93% | FileText 아이콘 | 강의록 요약 일관성 수치 |
| 유사도 검증 | 95.1% | Brain 아이콘 | 오답 기반 AI 유사 문제 매핑 |

- 패턴: `rounded-3xl border border-gray-100 p-7`
- 아이콘 컨테이너: `w-10 h-10 rounded-2xl bg-[#F5F9F8]`
- 수치: `text-5xl md:text-6xl`, ExtraBold, `%`는 한 단계 작게 (`text-3xl`)

### 4.11 Core Features 섹션 헤딩

```jsx
<h2>
  본과생의 시간을 설계하는<br />
  <span style={{ color: '#E67E22' }}>3가지</span> 엔진
</h2>
<p>
  흩어진 학습 자료를 정밀하게 꿰어 내신과 KMLE를{' '}
  <span style={{ color: '#E67E22', fontWeight: 700 }}>동시에</span> 잡습니다.
</p>
```

- "3가지", "동시에" 키워드만 오렌지 강조

### 4.12 기능 카드 3종

| # | 아이콘 | 컬러 | 제목 |
|---|---|---|---|
| 1 | Link2 | `#8CBDB3` (Teal) | 강의록 · 기출 · KMLE 자동 매핑 |
| 2 | Brain | `#E67E22` (Orange) | AI 오답 기반 유사 문제 생성 |
| 3 | Target | `#2F4F4F` (Dark Slate) | 실전 대비 최종 모의고사 |

→ 컬러 순서를 통해 시각적 리듬: 틸 → 오렌지 → 다크

### 4.13 CTA 섹션

- 배경: 솔리드 `#8CBDB3` (그라디언트 X)
- `rounded-[2.5rem]`, `p-12 md:p-16`
- 백그라운드 블러 원형 2개 (`bg-white/20 blur-2xl`)
- Stethoscope 아이콘 (40px)
- 메인 버튼: **"지금 바로 시작하기"** (white bg / dark text)
- 보조 버튼: "서비스 둘러보기" (transparent / white border)
- 하단: **"결제 정보 불필요 · 베타 기간 전면 무료"** (Bold 700)

---

## 5. 인터랙션 / 상태 관리 요약

| 상태 | 기능 |
|---|---|
| `termsAgreed` | 약관 체크박스 ↔ 검색 버튼 활성화 연동 |
| `uploadCount` | 라이브 카운트업 애니메이션 (0 → target) |
| `menuOpen` | 모바일 햄버거 메뉴 토글 |

### 5.1 약관 동의 연동 로직 (필수 구현)
```
[ ] 미동의 → 검색 버튼 회색 + disabled, placeholder = "이용약관 동의 후 검색 가능합니다"
[✓] 동의 → 검색 버튼 오렌지 활성화, placeholder = "교수명 · 강의록 주제 검색"
```

### 5.2 카운트업 애니메이션 (필수 구현)
- `requestAnimationFrame` 기반 (setInterval ❌)
- easeOutCubic 곡선
- 1.8초 (`duration = 1800`)
- 정수 floor 처리 + `toLocaleString()` 포맷

---

## 6. 반응형 가이드

- 기본 컨테이너: `max-w-3xl mx-auto px-6` (Hero 콘텐츠), `max-w-7xl` (전체 섹션)
- 모바일 헤더: 햄버거 메뉴 (`md:hidden`)
- 그리드: 4-col (`lg:grid-cols-4`) → 2-col (`md:grid-cols-2`) → 1-col
- 폰트 크기: 메인 카피 `text-4xl md:text-6xl`
- 패딩: `py-20`, `p-12 md:p-16`

---

## 7. 사용 라이브러리

```jsx
import {
  Menu, X, ArrowRight, Check, Sparkles, Brain, FileText,
  Target, Shield, Zap, ChevronRight, Link2, Stethoscope,
  Search, AlertTriangle
} from 'lucide-react';
```

- **React**: useState, useEffect (필수 hooks)
- **Tailwind CSS**: 유틸리티 클래스 (별도 PostCSS 설정 필요 없음, CDN 호환)
- **lucide-react**: 모든 아이콘
- **외부 폰트**: jsdelivr CDN의 LINE Seed KR + Google Fonts의 IBM Plex Sans KR

---

## 8. 디자인 원칙 체크리스트

상대 세션에서 구현 시 다음을 모두 만족하는지 확인:

- [ ] 메인 배경은 항상 순백 `#FFFFFF`
- [ ] 모든 카드는 `rounded-3xl` (24px) 이상
- [ ] 헤딩 자간 `-0.05em`, 본문 자간 `-0.03em`
- [ ] 키워드 강조는 오렌지 `#E67E22` 단일 컬러로 통일
- [ ] AI 단어는 라이트 틸 `#8CBDB3` + ExtraBold 800
- [ ] 호버 효과: 카드는 `-translate-y-1`, 버튼은 `-translate-y-0.5`
- [ ] 수치 카드는 `font-weight: 800` + `tnum`
- [ ] 약관 미동의 시 검색 버튼 회색·비활성, 동의 시 오렌지 활성화
- [ ] 라이브 카운트는 `requestAnimationFrame` + easeOutCubic
- [ ] 의료 콘텐츠는 친근한 둥근 라운드와 차분한 컬러로 신뢰감 표현

---

## 9. 카피라이팅 원칙

- 조사·수식어 최소화, 단어 위주 구성
- 의대생 슬랭 자연스럽게 활용 (야마, KMLE, 본과생, 내신, 기출)
- 베타 단계임을 솔직하게 명시 ("베타 기간 한정", "추후 추가 예정")
- 법적 책임 관련 안내는 시각적으로 명확하게 (오렌지 경고 박스)

---

## 부록: 다른 세션에 전달할 핵심 한 줄 요약

> "라이트 틸(#8CBDB3) + 소프트 오렌지(#E67E22) + 다크 슬레이트(#2F4F4F) 트라이톤,
> LINE Seed KR / IBM Plex Sans KR 폰트, rounded-3xl 이상의 둥근 카드,
> 자간 -0.05em(헤딩) / -0.03em(본문), 약관 동의 ↔ 검색 활성화 연동,
> requestAnimationFrame 기반 카운트업, 12개 로고를 산포한 floating background.
> 의료기기처럼 깨끗하고 수술복처럼 편안한 Clean & Professional Medical 톤."
