'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function EvaluatePage() {
  const router = useRouter()
  const [occupationCode, setOccupationCode] = useState('15-1252.00')
  const [occupationTitle, setOccupationTitle] = useState('Software Developer')
  const [skills, setSkills] = useState('python,sql,communication')
  const [prefs, setPrefs] = useState('creative,client communication')
  const [loading, setLoading] = useState(false)

  const run = async () => {
    setLoading(true)
    const sessionId = crypto.randomUUID()
    const res = await fetch('/api/py/risk/evaluate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        occupation_code: occupationCode,
        occupation_title: occupationTitle,
        session_id: sessionId,
        user_inputs: {
          skills: skills.split(',').map((s) => s.trim()),
          tasks_preference: prefs.split(',').map((s) => s.trim())
        }
      })
    })
    const data = await res.json()
    localStorage.setItem('assessment', JSON.stringify(data))
    router.push('/dashboard')
  }

  return <div className="card"><h2>对话式引导（MVP）</h2><div className='row'><div><label>职业代码</label><input value={occupationCode} onChange={e=>setOccupationCode(e.target.value)} /></div><div><label>职业名称</label><input value={occupationTitle} onChange={e=>setOccupationTitle(e.target.value)} /></div></div><label>技能（逗号分隔）</label><input value={skills} onChange={e=>setSkills(e.target.value)} /><label>任务偏好</label><input value={prefs} onChange={e=>setPrefs(e.target.value)} /><button onClick={run} disabled={loading}>{loading?'评估中...':'生成风险评估'}</button></div>
}
