import { useState, useEffect } from 'react'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import LectureViewer from './components/LectureViewer'
import Placeholder from './components/Placeholder'

export default function App() {
  const [lectures, setLectures] = useState([])
  const [selected, setSelected] = useState(null)
  const [termsAgreed, setTermsAgreed] = useState(false)

  useEffect(() => {
    fetch('/api/lectures')
      .then(r => r.json())
      .then(setLectures)
      .catch(() => setLectures([]))
  }, [])

  const totalQ = lectures.reduce((s, l) => s + l.q_count, 0)

  return (
    <div className="ll-root d-flex flex-column" style={{ height: '100dvh', overflow: 'hidden' }}>
      <Header totalLectures={lectures.length} totalQ={totalQ} />

      <div className="d-flex flex-grow-1 overflow-hidden">
        <Sidebar
          lectures={lectures}
          selectedKey={selected?.key}
          onSelect={setSelected}
          termsAgreed={termsAgreed}
          onTermsChange={setTermsAgreed}
        />

        <main className="viewer-area">
          {!selected && <Placeholder />}
          {selected && <LectureViewer lecture={selected} />}
        </main>
      </div>
    </div>
  )
}
