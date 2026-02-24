'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'

export default function ExperimentsPage() {
  const [items, setItems] = useState<any[]>([])
  const [form, setForm] = useState({ name: '', description: '', model_version: 'v1', params: '{"v1":{}}', is_active: false })

  async function load() {
    const res = await fetch('/api/admin/experiments')
    setItems(await res.json())
  }

  useEffect(() => { load() }, [])

  async function createExp() {
    await fetch('/api/admin/experiments', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...form, params: JSON.parse(form.params) })
    })
    await load()
  }

  async function toggle(item: any) {
    await fetch(`/api/admin/experiments/${item.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_active: !item.is_active })
    })
    await load()
  }

  if (process.env.NEXT_PUBLIC_DISABLE_ADMIN === 'true') return <div className='card'>Admin disabled.</div>

  return <div className='card'>
    <h2>Experiments</h2>
    {items.map((x) => <p key={x.id}><Link href={`/admin/experiments/${x.id}`}>{x.name}</Link> [{x.model_version}] active={String(x.is_active)} samples={x.sample_count} <button onClick={() => toggle(x)}>toggle</button></p>)}
    <h3>Create</h3>
    <input placeholder='name' value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
    <input placeholder='description' value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
    <textarea rows={8} value={form.params} onChange={(e) => setForm({ ...form, params: e.target.value })} />
    <button onClick={createExp}>Create</button>
  </div>
}
