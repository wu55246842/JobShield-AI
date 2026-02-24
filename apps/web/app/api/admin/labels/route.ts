import { adminFetch } from '@/lib/admin-api'

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url)
  const assessment_id = searchParams.get('assessment_id')
  const res = await adminFetch(`/admin/labels?assessment_id=${assessment_id}`)
  return Response.json(await res.json())
}

export async function POST(req: Request) {
  const body = await req.text()
  const res = await adminFetch('/admin/labels', { method: 'POST', body })
  return Response.json(await res.json())
}
