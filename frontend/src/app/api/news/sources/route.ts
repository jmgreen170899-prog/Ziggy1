import { proxyJson } from "../../_lib/proxy";

export async function GET(req: Request) {
  return proxyJson(req, "/news/sources", { timeoutMs: 5000 });
}
