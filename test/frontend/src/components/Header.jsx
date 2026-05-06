export default function Header({ totalLectures, totalQ }) {
  return (
    <header className="app-header flex-shrink-0">
      <div className="ll-logo" aria-hidden="true">
        <svg width="36" height="36" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="2" y="2" width="36" height="36" rx="10" fill="#8CBDB3" />
          <path d="M13 14 Q13 11 16 11 L19 11 Q22 11 22 14 L22 17" stroke="white" strokeWidth="2.2" strokeLinecap="round" fill="none" />
          <path d="M27 26 Q27 29 24 29 L21 29 Q18 29 18 26 L18 23" stroke="white" strokeWidth="2.2" strokeLinecap="round" fill="none" />
          <circle cx="20" cy="20" r="2.2" fill="#E67E22" />
        </svg>
      </div>
      <div className="flex-grow-1">
        <div className="brand">LectureLink <span>호흡기</span></div>
        <div className="subtitle">교수님별 강의록 기반 맞춤형 AI 튜터</div>
      </div>
      <div className="d-flex gap-2 flex-shrink-0">
        <span className="stat-pill">
          <i className="bi bi-book me-1" />{totalLectures}강의
        </span>
        <span className="stat-pill">
          <i className="bi bi-question-circle me-1" />{totalQ}문제
        </span>
      </div>
    </header>
  )
}
