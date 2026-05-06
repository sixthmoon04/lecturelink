export default function Placeholder() {
  return (
    <div className="viewer-placeholder">
      <div className="placeholder-icon">
        <svg width="44" height="44" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="2" y="2" width="36" height="36" rx="10" fill="#8CBDB3" />
          <path d="M13 14 Q13 11 16 11 L19 11 Q22 11 22 14 L22 17" stroke="white" strokeWidth="2.2" strokeLinecap="round" fill="none" />
          <path d="M27 26 Q27 29 24 29 L21 29 Q18 29 18 26 L18 23" stroke="white" strokeWidth="2.2" strokeLinecap="round" fill="none" />
          <circle cx="20" cy="20" r="2.2" fill="#E67E22" />
        </svg>
      </div>
      <div className="placeholder-title">강의를 선택하세요</div>
      <div className="placeholder-sub">
        왼쪽 목록에서 강의를 클릭하면 학습을 시작할 수 있습니다
      </div>
    </div>
  )
}
