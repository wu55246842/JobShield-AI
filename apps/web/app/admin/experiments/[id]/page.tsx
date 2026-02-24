'use client'

import { useEffect, useState } from 'react'

function CompareView({ outputs }: { outputs: any }) {
  const left = outputs.v0 || {}
  const right = outputs.v1 || {}
  return <div className='row'>
    <div><h4>v0</h4><pre>{JSON.stringify(left.breakdown, null, 2)}</pre></div>
    <div><h4>v1</h4><pre>{JSON.stringify(right.breakdown, null, 2)}</pre></div>
  </div>
}

export default function ExperimentDetail({ params }: { params: { id: string } }) {
  const [metrics, setMetrics] = useState<any>(null)
  const [runs, setRuns] = useState<any[]>([])
  const [selected, setSelected] = useState<any>(null)
  const [compare, setCompare] = useState<any>(null)

  useEffect(() => {
    fetch(`/api/admin/experiments/${params.id}/metrics`).then(r => r.json()).then(setMetrics)
    fetch(`/api/admin/experiments/${params.id}/runs?limit=20`).then(r => r.json()).then(setRuns)
  }, [params.id])

  async function replay(run: any) {
    setSelected(run)
    const res = await fetch(`/api/admin/assessments/${run.assessment_id}/compare?models=v0,v1&experiment_id=${params.id}`)
    setCompare(await res.json())
  }

  if (process.env.NEXT_PUBLIC_DISABLE_ADMIN === 'true') return <div className='card'>Admin disabled.</div>

  return <div>
    <div className='card'><h2>Metrics</h2><pre>{JSON.stringify(metrics, null, 2)}</pre></div>
    <div className='card'><h3>Recent runs</h3>{runs.map((r) => <p key={r.id}>assessment={r.assessment_id} variant={r.variant} score={r.score} confidence={r.confidence} <button onClick={() => replay(r)}>replay</button></p>)}</div>
    {selected && <div className='card'><h3>Replay</h3><pre>{JSON.stringify(selected.output, null, 2)}</pre>{compare?.outputs && <CompareView outputs={compare.outputs} />}</div>}
  </div>
}
