import { adminFetch } from '@/lib/admin-api'

export async function GET(req: Request, { params }: { params: { id: string } }) {
  const { searchParams } = new URL(req.url)
  const models = searchParams.get('models') || 'v0,v1'
  const experimentId = searchParams.get('experiment_id')
  const suffix = experimentId ? `&experiment_id=${experimentId}` : ''
  const res = await adminFetch(`/admin/assessments/${params.id}/compare?models=${models}${suffix}`)
  return Response.json(await res.json())
}
