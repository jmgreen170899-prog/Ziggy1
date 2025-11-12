// Dev-only guard to warn if obvious placeholders appear in UI surfaces
export function guardRealData(surfaceName: string, samples: Array<string | number>) {
  if (process.env.NODE_ENV !== 'development') return;
  try {
    const badTokens = [/lorem\s+ipsum/i, /xxxx/i, /john\s+doe/i, /123456/, /^0(\.0+)?$/];
    const flagged = samples.filter((s) => {
      const str = String(s ?? '').trim();
      return badTokens.some((re) => re.test(str));
    });
    if (flagged.length > 0) {
      console.warn(`[guardRealData] ${surfaceName} contains potential placeholder values:`, flagged.slice(0, 3));
    }
  } catch {
    // ignore
  }
}
