'use client'

import { useState } from 'react'

export default function AgentPage(){
  const [events,setEvents] = useState<string[]>([])
  const [agent,setAgent] = useState<any>(null)

  const generate = async () => {
    setEvents([]); setAgent(null)
    const assessmentRaw = localStorage.getItem('assessment')
    const assessment = assessmentRaw ? JSON.parse(assessmentRaw) : null
    const res = await fetch('/api/py/agent/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_goal:'提升未来12个月就业韧性',risk_score:assessment?.score,assessment_id:assessment?.assessment_id})})
    const reader = res.body?.getReader()
    if(!reader) return
    const decoder = new TextDecoder()
    let buffer = ''
    while(true){
      const {done,value} = await reader.read()
      if(done) break
      buffer += decoder.decode(value, {stream:true})
      const chunks = buffer.split('\n\n')
      buffer = chunks.pop() || ''
      for(const chunk of chunks){
        const evt = chunk.match(/event: (.*)/)?.[1]
        const dataLine = chunk.match(/data: (.*)/)?.[1]
        if(!evt || !dataLine) continue
        const data = JSON.parse(dataLine)
        setEvents(prev=>[...prev,`${evt}: ${JSON.stringify(data)}`])
        if(evt==='result') setAgent(data.agent_config)
      }
    }
  }

  return <div className='card'><h2>Agent 控制台</h2><button onClick={generate}>流式生成 Agent</button><h3>步骤/进度</h3><pre>{events.join('\n')}</pre><h3>Agent Config</h3><pre>{agent?JSON.stringify(agent,null,2):'暂无'}</pre></div>
}
