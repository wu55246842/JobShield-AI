'use client'

import { useState } from 'react'

export default function LabelPage({ params }: { params: { assessment_id: string } }) {
  const [risk, setRisk] = useState('')
  const [confidence, setConfidence] = useState('0.8')
  const [rater, setRater] = useState('admin')
  const [notes, setNotes] = useState('')
  const [saved, setSaved] = useState(false)

  async function save() {
    await fetch('/api/admin/labels', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        assessment_id: Number(params.assessment_id),
        rater,
        risk_score_label: Number(risk),
        confidence_label: Number(confidence),
        notes,
      })
    })
    setSaved(true)
  }

  if (process.env.NEXT_PUBLIC_DISABLE_ADMIN === 'true') return <div className='card'>Admin disabled.</div>

  return <div className='card'>
    <h2>Label assessment #{params.assessment_id}</h2>
    <input placeholder='rater' value={rater} onChange={e => setRater(e.target.value)} />
    <input placeholder='risk 0-100' value={risk} onChange={e => setRisk(e.target.value)} />
    <input placeholder='confidence 0-1' value={confidence} onChange={e => setConfidence(e.target.value)} />
    <textarea placeholder='notes' value={notes} onChange={e => setNotes(e.target.value)} />
    <button onClick={save}>Save</button>
    {saved && <p>Saved.</p>}
  </div>
}
