'use client'

import { useEffect, useState } from 'react'

type Assessment = { score:number; summary:string; breakdown:{factor:string;weight:number;value:number;explanation:string}[]; suggested_focus:string[]; assessment_id?:number }

export default function DashboardPage(){
  const [assessment,setAssessment] = useState<Assessment | null>(null)
  const [tools,setTools] = useState<any[]>([])

  useEffect(()=>{
    const raw = localStorage.getItem('assessment')
    if(raw){
      const parsed = JSON.parse(raw)
      setAssessment(parsed)
      fetch('/api/py/rag/tools/search',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:'ai productivity for software developer',top_k:6})})
        .then(r=>r.json()).then(d=>setTools(d.results||[])).catch(()=>setTools([]))
    }
  },[])

  if(!assessment) return <div className='card'>暂无评估，请先去 Evaluate 页面。</div>
  return <div>
    <div className='card'><h2>风险仪表盘</h2><p>总分：<b>{assessment.score}</b>/100</p><p>{assessment.summary}</p></div>
    <div className='card'><h3>Breakdown</h3>{assessment.breakdown.map(b=><p key={b.factor}>{b.factor}: {(b.value*100).toFixed(0)}% - {b.explanation}</p>)}</div>
    <div className='card'><h3>推荐工具</h3>{tools.length===0?<p>暂无（请先导入Apify数据或配置OPENAI_API_KEY）</p>:tools.map(t=><p key={t.tool_id}><a href={t.url} target='_blank'>{t.name}</a> ({(t.score*100).toFixed(1)})</p>)}</div>
  </div>
}
