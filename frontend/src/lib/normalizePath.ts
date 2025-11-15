export function normalizePath(
  pathTemplate: string,
  params?: Record<string, string | number>,
): string {
  let out = pathTemplate.trim();
  if (!out.startsWith("/")) out = "/" + out;
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      out = out.replace(
        new RegExp(`:${k}|\\{${k}\\}`, "g"),
        encodeURIComponent(String(v)),
      );
    }
  }
  // remove duplicate slashes
  out = out.replace(/\/+/, "/");
  return out;
}
