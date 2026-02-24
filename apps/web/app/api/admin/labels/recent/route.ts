import { adminFetch } from '@/lib/admin-api'

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url)
  const limit = searchParams.get('limit') || '20'
  const res = await adminFetch(`/admin/labels/recent?limit=${limit}`)
  return Response.json(await res.json())
}
