import { mixed, mixedStatusFromBatch, proxyJson } from '../../_lib/proxy'

export async function GET(req: Request) {
  // If caller didn't request batch, still proxy normally; but we encourage batch=true for resilience.
  const url = new URL(req.url)
  const wantsBatch = url.searchParams.get('batch') === 'true'
  if (!wantsBatch) {
    return proxyJson(req, '/trade/ohlc', { timeoutMs: 8000 })
  }

  // Force batch=true with a sane timeout per ticker
  url.searchParams.set('batch', 'true')
  if (!url.searchParams.get('timeout_s')) url.searchParams.set('timeout_s', '3')
  const backendReq = new Request(url.toString(), { headers: req.headers, method: 'GET' })
  const res = await fetch(backendReq)
  try {
    const data = await res.json()
    const status = mixedStatusFromBatch(data)
    if (status === 'mixed') return mixed(data)
    return new Response(JSON.stringify({ ok: true, status: 'ok', data }), { headers: { 'content-type': 'application/json' } })
  } catch {
    return new Response(JSON.stringify({ ok: false, status: 'degraded', reason: 'proxy_parse_error' }), { headers: { 'content-type': 'application/json' } })
  }
}
