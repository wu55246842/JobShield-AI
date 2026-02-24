import { adminFetch } from '@/lib/admin-api'

export async function GET(req: Request, { params }: { params: { id: string } }) {
  const { searchParams } = new URL(req.url)
  const limit = searchParams.get('limit') || '20'
  const res = await adminFetch(`/admin/experiments/${params.id}/runs?limit=${limit}`)
  return Response.json(await res.json())
}
