import { useState, useEffect, useMemo } from 'react'
import QuestionCard from './QuestionCard'

const TABS = ['강의록', '기출', '학습 가이드', '3step', '지엽']
const STEP_TYPES = ['야마형', '심화형', '지엽형']

function rotateChoices(questions) {
  return questions.map(q => {
    const choices = q._real_choices || []
    if (choices.length < 2) return q
    const ansNum = parseInt(q._answer_num, 10) || 1
    const ansText = (choices[ansNum - 1] || '').replace(/^\d+[)．]\s*/, '')
    const rotated = [choices[choices.length - 1], ...choices.slice(0, -1)]
    const renumbered = rotated.map((ch, i) => `${i + 1}) ${ch.replace(/^\d+[)．]\s*/, '')}`)
    let newAns = ansNum
    renumbered.forEach((ch, i) => { if (ch.replace(/^\d+[)．]\s*/, '') === ansText) newAns = i + 1 })
    return { ...q, _real_choices: renumbered, _answer_num: String(newAns) }
  })
}

export default function LectureViewer({ lecture }) {
  const [activeTab, setActiveTab] = useState('기출')
  const [stepType, setStepType]   = useState('야마형')
  const [questions, setQuestions] = useState([])
  const [loading, setLoading]     = useState(true)

  useEffect(() => {
    setLoading(true)
    setQuestions([])
    setActiveTab('기출')
    setStepType('야마형')
    fetch(`/api/questions/${encodeURIComponent(lecture.key)}`)
      .then(r => r.json())
      .then(d => { setQuestions(d); setLoading(false) })
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
          >{tab}</button>
        ))}
      </nav>

      {activeTab === '강의록'     && <LectureTabContent lecture={lecture} />}
      {activeTab === '기출'       && <QuestionList lecture={lecture} questions={questions} loading={loading} />}
      {activeTab === '학습 가이드' && <GuideTab lecture={lecture} questions={questions} />}
      {activeTab === '3step'      && <StepTab lecture={lecture} questions={questions} stepType={stepType} setStepType={setStepType} />}
      {activeTab === '지엽'       && <MinorTab lecture={lecture} />}
    </div>
  )
}

function LectureTabContent({ lecture }) {
  if (!lecture.has_lecture) return (
    <div className="viewer-placeholder">
      <div style={{ fontSize: '2.5rem' }}>📭</div>
      <div className="placeholder-title">강의록 없음</div>
      <div className="placeholder-sub">이 강의는 강의록 파일이 없습니다.</div>
    </div>
  )
  const url = `/pdf/lecture/${encodeURIComponent(lecture.key + '.pdf')}`
  return (
    <>
      <div className="viewer-bar">
        <span className="vb-title">{lecture.title}</span>
        <span className="mode-pill lec">📖 강의록</span>
        <span className="info-pill"><i className="bi bi-person-fill me-1" />{lecture.professor}</span>
        <span className="info-pill">{lecture.lecture_pages}p</span>
        <a href={url} download={`강의록_${lecture.key}.pdf`} className="btn btn-primary btn-sm" style={{ fontSize: '.78rem' }}>
          <i className="bi bi-download me-1" />다운로드
        </a>
      </div>
      <div className="viewer-frame">
        <iframe src={`${url}#toolbar=1&navpanes=0`} title="강의록 뷰어" />
      </div>
    </>
  )
}

function QuestionList({ lecture, questions, loading }) {
  return (
    <div className="question-scroll">
      <div className="page-title">{lecture.title}</div>
      <div className="page-sub">총 {questions.length}문제 · 최신 연도 먼저 · 선지를 클릭하면 정오답이 표시됩니다</div>
      {loading && <div className="text-center text-secondary py-5"><div className="spinner-border spinner-border-sm me-2" />불러오는 중…</div>}
      {!loading && questions.length === 0 && <div className="text-center text-secondary py-5">문제가 없습니다.</div>}
      {!loading && questions.map((q, idx) => (
        <QuestionCard key={`${q.year}-${q.num}`} q={q} index={idx + 1} />
      ))}
    </div>
  )
}

function GuideTab({ lecture, questions }) {
  const guide = useMemo(() => {
    if (!questions.length) return null
    const tm = {}
    questions.forEach(q => {
      const t = q.topic || '기타'
      if (!tm[t]) tm[t] = { count: 0, years: new Set() }
      tm[t].count++
      tm[t].years.add(q.year)
    })
    const sorted = Object.entries(tm).sort(([, a], [, b]) => b.count - a.count)
    return {
      keyConcepts: sorted.slice(0, 8).map(([t, s]) => ({ topic: t, count: s.count })),
      freqTopics:  sorted.slice(0, 10).map(([t, s]) => ({ topic: t, count: s.count, years: [...s.years].sort((a, b) => b - a) })),
      studyFlow:   sorted.map(([t]) => t),
    }
  }, [questions])

  if (!guide) return <div className="viewer-placeholder"><div className="placeholder-sub">문제 데이터가 없습니다.</div></div>

  return (
    <div className="question-scroll">
      <div className="page-title">{lecture.title} — 학습 가이드</div>
      <div className="page-sub">기출문제 {questions.length}개 분석 기반 · 빈출 토픽 자동 추출</div>

      <div className="guide-section">
        <div className="guide-section-title">📌 핵심 강조 개념</div>
        <div className="guide-concept-list">
          {guide.keyConcepts.map((item, i) => (
            <div key={i} className="guide-concept-item">
              <span className="rank-badge">#{i + 1}</span>
              <span style={{ flex: 1 }}>{item.topic}</span>
              <span style={{ fontSize: '.72rem', color: '#64748b' }}>{item.count}문제</span>
            </div>
          ))}
        </div>
      </div>

      <div className="guide-section">
        <div className="guide-section-title">🎯 자주 출제 개념</div>
        {guide.freqTopics.map((item, i) => (
          <div key={i} className="guide-freq-item">
            <div style={{ fontWeight: 700, marginBottom: 3 }}>{item.topic}</div>
            <div style={{ fontSize: '.75rem', color: '#64748b' }}>출제 {item.count}회 · {item.years.join(', ')}년</div>
          </div>
        ))}
      </div>

      <div className="guide-section">
        <div className="guide-section-title">📚 효율적 학습 흐름</div>
        {guide.studyFlow.map((topic, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 0', borderBottom: '1px solid #f1f5f9' }}>
            <span style={{ fontSize: '.7rem', fontWeight: 800, color: '#3b82f6', minWidth: 28 }}>{i + 1}.</span>
            <span style={{ fontSize: '.84rem', color: '#334155' }}>{topic}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function StepTab({ lecture, questions, stepType, setStepType }) {
  const [deepQs, setDeepQs]         = useState([])
  const [deepLoading, setDeepLoading] = useState(false)
  const [minorQs, setMinorQs]       = useState([])
  const [minorLoading, setMinorLoading] = useState(false)

  useEffect(() => {
    if (stepType !== '심화형') return
    let cancelled = false
    setDeepLoading(true)
    setDeepQs([])
    fetch(`/api/3step/deep/${encodeURIComponent(lecture.key)}`)
      .then(r => r.json())
      .then(d => { if (!cancelled) { setDeepQs(d); setDeepLoading(false) } })
      .catch(() => { if (!cancelled) { setDeepQs([]); setDeepLoading(false) } })
    return () => { cancelled = true }
  }, [stepType, lecture.key])

  useEffect(() => {
    if (stepType !== '지엽형') return
    let cancelled = false
    setMinorLoading(true)
    setMinorQs([])
    fetch(`/api/3step/minor/${encodeURIComponent(lecture.key)}`)
      .then(r => r.json())
      .then(d => { if (!cancelled) { setMinorQs(d); setMinorLoading(false) } })
      .catch(() => { if (!cancelled) { setMinorQs([]); setMinorLoading(false) } })
    return () => { cancelled = true }
  }, [stepType, lecture.key])

  const yamaQs   = useMemo(() => rotateChoices(questions), [questions])
  const displayQs = stepType === '야마형' ? yamaQs : stepType === '심화형' ? deepQs : minorQs
  const isLoading = stepType === '심화형' ? deepLoading : stepType === '지엽형' ? minorLoading : false

  return (
    <>
      <div className="step-type-bar">
        {STEP_TYPES.map(t => (
          <button key={t} className={`step-type-btn ${stepType === t ? 'active' : ''}`} onClick={() => setStepType(t)}>{t}</button>
        ))}
        {!isLoading && <span style={{ marginLeft: 'auto', fontSize: '.75rem', color: '#64748b' }}>{displayQs.length}문제</span>}
      </div>
      <div className="question-scroll">
        <div className="page-title">{lecture.title} — {stepType}</div>
        <div className="page-sub">
          {stepType === '야마형' && '핵심 빈출 문제 · 선지 순서 변형 적용'}
          {stepType === '심화형' && '핵심 개념 심화 문제 · 텍스트 전용'}
          {stepType === '지엽형' && '지엽 세부 지식 문제'}
        </div>
        {isLoading && <div className="text-center text-secondary py-5"><div className="spinner-border spinner-border-sm me-2" />불러오는 중…</div>}
        {!isLoading && displayQs.length === 0 && <div className="text-center text-secondary py-5">문제가 없습니다.</div>}
        {!isLoading && displayQs.map((q, idx) => (
          <QuestionCard key={`${stepType}-${q.year}-${q.num}`} q={q} index={idx + 1} />
        ))}
      </div>
    </>
  )
}

function MinorTab({ lecture }) {
  const [minorData, setMinorData] = useState(null)
  const [loading, setLoading]     = useState(false)

  useEffect(() => {
    setMinorData(null)
    setLoading(true)
    fetch(`/api/minor/${encodeURIComponent(lecture.key)}`)
      .then(r => r.json())
      .then(d => { setMinorData(d); setLoading(false) })
      .catch(() => { setMinorData([]); setLoading(false) })
  }, [lecture.key])

  return (
    <div className="question-scroll">
      <div className="page-title">{lecture.title} — 지엽 정리</div>
      <div className="page-sub">빈출도 낮은 세부 내용 · 암기 포인트 중심</div>
      {loading && <div className="text-center text-secondary py-5"><div className="spinner-border spinner-border-sm me-2" />불러오는 중…</div>}
      {!loading && minorData?.length === 0 && <div className="text-center text-secondary py-5">지엽 항목이 없습니다.</div>}
      {!loading && minorData?.map((item, i) => (
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
  )
}
