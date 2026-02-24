import { adminFetch } from '@/lib/admin-api'

export async function PATCH(req: Request, { params }: { params: { id: string } }) {
  const body = await req.text()
  const res = await adminFetch(`/admin/experiments/${params.id}`, { method: 'PATCH', body })
  return Response.json(await res.json())
}
