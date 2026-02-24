export async function adminFetch(path: string, init: RequestInit = {}) {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
  const key = process.env.ADMIN_API_KEY
  if (!key) throw new Error('Missing ADMIN_API_KEY')
  const headers = new Headers(init.headers)
  headers.set('X-Admin-Key', key)
  if (!headers.get('Content-Type') && init.body) headers.set('Content-Type', 'application/json')
  const res = await fetch(`${base}${path}`, { ...init, headers, cache: 'no-store' })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `Admin API failed: ${res.status}`)
  }
  return res
}
