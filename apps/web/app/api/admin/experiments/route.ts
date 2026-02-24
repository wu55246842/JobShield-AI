import { adminFetch } from '@/lib/admin-api'

export async function GET() {
  const res = await adminFetch('/admin/experiments')
  return Response.json(await res.json())
}

export async function POST(req: Request) {
  const body = await req.text()
  const res = await adminFetch('/admin/experiments', { method: 'POST', body })
  return Response.json(await res.json())
}
