export const isNum = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v)

export const f3 = (v: number | null | undefined) => (isNum(v) ? v.toFixed(3) : '-')

export const pct = (v: number | null | undefined) => (isNum(v) ? `${Math.round(v * 100)}%` : '-')

/** "17:38:23" from an ISO timestamp. */
export const clock = (ts?: string | null) => (ts ? ts.slice(11, 19) : '')

/** "2026-09-20 17:45" from an ISO timestamp. */
export const stamp = (ts?: string | null) => (ts ? ts.slice(0, 16).replace('T', ' ') : '')

export function duration(ms: number): string {
  if (!Number.isFinite(ms) || ms < 0) return '00:00'
  const s = Math.floor(ms / 1000)
  const p = (n: number) => String(n).padStart(2, '0')
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  return h ? `${h}:${p(m)}:${p(s % 60)}` : `${p(m)}:${p(s % 60)}`
}

/** "c01" from "gen003_c01". */
export const short = (id: string) => id.replace(/^gen\d{3}_/, '')
