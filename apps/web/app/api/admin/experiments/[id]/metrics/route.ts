import { adminFetch } from '@/lib/admin-api'

export async function GET(_: Request, { params }: { params: { id: string } }) {
  const res = await adminFetch(`/admin/experiments/${params.id}/metrics`)
  return Response.json(await res.json())
}
