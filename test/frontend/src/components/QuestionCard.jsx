import { useState, useEffect } from 'react'

export default function QuestionCard({ q, index }) {
  const [chosen, setChosen]     = useState(null) // null | 'correct' | number
  const [revealed, setRevealed] = useState(false)
  const [lightbox, setLightbox] = useState(null)

  useEffect(() => {
    const handler = e => { if (e.key === 'Escape') setLightbox(null) }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  function handleChoice(num) {
    if (chosen !== null) return
    setChosen(num)
  }

  function choiceClass(num) {
    if (chosen === null) return ''
    const answerNum = parseInt(q._answer_num, 10)
    if (num === answerNum)  return 'correct'
    if (num === chosen)     return 'wrong'
    return 'dimmed'
  }

  return (
    <>
      <div className="q-card" id={`qcard-${index}`}>
        <div className="q-header">
          <span className="q-year-badge">{q.year}년 Q{q.num}</span>
          <span className="q-topic">[{q.professor}] {q.topic}</span>
        </div>

        <div className="q-body">
          <div className="q-text">{q.question_text}</div>

          <div className="choices">
            {q._real_choices.map((ch, i) => {
              const num = i + 1
              return (
                <button
                  key={num}
                  className={`choice-btn ${choiceClass(num)}`}
                  onClick={() => handleChoice(num)}
                >
                  {ch}
                </button>
              )
            })}
          </div>

          <div className="reveal-wrap">
            <button
              className={`reveal-btn ${revealed ? 'revealed' : ''}`}
              onClick={() => setRevealed(r => !r)}
            >
              {revealed ? '답과 해설 닫기' : '답과 해설 보기'}
            </button>
          </div>

          {revealed && (
            <div className="answer-panel">
              <div className="answer-line">정답: {q.answer}</div>

              {q._images?.length > 0 && (
                <div className="q-images">
                  {q._images.map(img => (
                    <img
                      key={img}
                      src={`/static/images/${img}`}
                      alt="풀이 이미지"
                      onClick={() => setLightbox(`/static/images/${img}`)}
                    />
                  ))}
                </div>
              )}

              {q.explanation && (
                <div className="explanation">{q.explanation}</div>
              )}
            </div>
          )}
        </div>
      </div>

      {lightbox && (
        <div className="lightbox show" onClick={() => setLightbox(null)}>
          <button className="lightbox-close" onClick={() => setLightbox(null)}>✕</button>
          <img src={lightbox} alt="확대 이미지" onClick={e => e.stopPropagation()} />
        </div>
      )}
    </>
  )
}
