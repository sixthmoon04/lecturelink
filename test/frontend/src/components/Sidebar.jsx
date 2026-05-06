import { useState, useMemo } from 'react'

const DATE_ORDER = {
  '12/16': 0, '12/17': 1, '12/18': 2,
  '12/22': 3, '12/23': 4, '12/24': 5, '기타': 99,
}

export default function Sidebar({ lectures, selectedKey, onSelect, termsAgreed, onTermsChange }) {
  const [query, setQuery]       = useState('')
  const [sortMode, setSortMode] = useState('date')

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return lectures.filter(l =>
      !q || l.title.toLowerCase().includes(q) || l.professor.toLowerCase().includes(q)
    )
  }, [lectures, query])

  const grouped = useMemo(() => {
    if (sortMode === 'date') {
      const map = {}
      filtered.forEach(l => {
        const key = l.date || '기타'
        if (!map[key]) map[key] = []
        map[key].push(l)
      })
      return Object.entries(map).sort(
        ([a], [b]) => (DATE_ORDER[a] ?? 50) - (DATE_ORDER[b] ?? 50)
      )
    } else {
      const sorted = [...filtered].sort((a, b) =>
        a.professor.localeCompare(b.professor, 'ko')
      )
      const map = {}
      sorted.forEach(l => {
        const key = l.professor || '-'
        if (!map[key]) map[key] = []
        map[key].push(l)
      })
      return Object.entries(map)
    }
  }, [filtered, sortMode])

  return (
    <aside className="sidebar-panel">
      <div className="sidebar-top">
        <div className="title-row">
          <h6>강의 목록</h6>
          <span className="ll-count-badge">
            {lectures.length}
          </span>
        </div>

        <div className={`search-box ${termsAgreed ? 'is-active' : 'is-disabled'}`}>
          <i className="bi bi-search" />
          <input
            type="text"
            placeholder={termsAgreed ? '제목 또는 교수명 검색' : '이용약관 동의 후 검색 가능합니다'}
            value={query}
            disabled={!termsAgreed}
            onChange={e => setQuery(e.target.value)}
          />
          <button
            className="search-submit"
            disabled={!termsAgreed}
            aria-label={termsAgreed ? '검색' : '이용약관 동의 필요'}
          >
            <i className="bi bi-arrow-right" />
          </button>
        </div>

        <label className="terms-agree">
          <input
            type="checkbox"
            checked={termsAgreed}
            onChange={e => onTermsChange(e.target.checked)}
          />
          <span className="check-box"><i className="bi bi-check-lg" /></span>
          <span>
            <strong>[필수]</strong> 자료 유출 금지 및 이용 조건에 동의합니다
          </span>
        </label>

        {!termsAgreed && (
          <div className="terms-hint">약관 동의 후 강의 검색이 활성화됩니다</div>
        )}

        <div className="sort-bar">
          <button
            className={`sort-btn ${sortMode === 'date' ? 'active' : ''}`}
            onClick={() => setSortMode('date')}
          >날짜별</button>
          <button
            className={`sort-btn ${sortMode === 'prof' ? 'active' : ''}`}
            onClick={() => setSortMode('prof')}
          >교수별</button>
        </div>
      </div>

      <div className="sidebar-scroll">
        {grouped.map(([groupKey, items]) => (
          <div key={groupKey} className="date-group">
            <div className="date-header">{groupKey}</div>
            {items.map(lecture => (
              <LectureItem
                key={lecture.key}
                lecture={lecture}
                isActive={selectedKey === lecture.key}
                onSelect={onSelect}
              />
            ))}
          </div>
        ))}
      </div>
    </aside>
  )
}

function LectureItem({ lecture, isActive, onSelect }) {
  const yrs = lecture.years
  const yearsLabel = yrs?.length
    ? yrs.length === 1 ? `${yrs[0]}년` : `${yrs[yrs.length - 1]}–${yrs[0]}년`
    : null

  return (
    <div
      className={`lecture-item ${isActive ? 'active-questions' : ''}`}
      style={{ cursor: 'pointer' }}
      onClick={() => onSelect(lecture)}
    >
      <div className="item-info" style={{ padding: '10px 15px' }}>
        <div className="item-title" title={lecture.title}>{lecture.title}</div>
        <div className="item-meta">
          <span className="prof-badge">
            <i className="bi bi-person-fill me-1" />{lecture.professor}
          </span>
          {yearsLabel && <span className="year-chip">{yearsLabel}</span>}
          <span className="count-chip">{lecture.q_count}문제</span>
        </div>
      </div>
    </div>
  )
}
