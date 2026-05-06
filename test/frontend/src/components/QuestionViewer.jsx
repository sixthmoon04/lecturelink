import { useState, useEffect } from 'react'
import QuestionCard from './QuestionCard'

const TABS = ['강의록', '기출', '학습 가이드', '3step', '지엽']

export default function QuestionViewer({ lecture }) {
  const [questions, setQuestions] = useState([])
  const [loading, setLoading]     = useState(true)
  const [activeTab, setActiveTab] = useState('기출')

  useEffect(() => {
    setLoading(true)
    fetch(`/api/questions/${encodeURIComponent(lecture.key)}`)
      .then(r => r.json())
      .then(data => { setQuestions(data); setLoading(false) })
      .catch(() => { setQuestions([]); setLoading(false) })
  }, [lecture.key])

  return (
    <div className="viewer-area">
      <nav className="top-tab-bar">
        {TABS.map(tab => (
          <button
            key={tab}
            className={`tab-btn ${activeTab === tab ? 'active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </nav>

      <div className="question-scroll">
        <div className="page-title">{lecture.title}</div>
        <div className="page-sub">
          총 {questions.length}문제 · 최신 연도 먼저 · 선지를 클릭하면 정오답이 표시됩니다
        </div>

        {loading && (
          <div className="text-center text-secondary py-5">
            <div className="spinner-border spinner-border-sm me-2" />
            불러오는 중…
          </div>
        )}

        {!loading && questions.length === 0 && (
          <div className="text-center text-secondary py-5">문제가 없습니다.</div>
        )}

        {!loading && questions.map((q, idx) => (
          <QuestionCard key={`${q.year}-${q.num}`} q={q} index={idx + 1} />
        ))}
      </div>
    </div>
  )
}
