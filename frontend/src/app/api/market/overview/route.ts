import { proxyJson } from "../../_lib/proxy";

export async function GET(req: Request) {
  // Proxies to backend /market/overview with same query params
  return proxyJson(req, "/market/overview", { timeoutMs: 5000 });
}
