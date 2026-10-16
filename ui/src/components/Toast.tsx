import { useEffect, useState } from 'react'
import type { Notice } from '../api'

/** One message at a time; a newer notice replaces the current one. Click or Esc dismisses. */
export function Toast({ notice }: { notice: Notice | null }) {
  const [shown, setShown] = useState<Notice | null>(null)

  useEffect(() => {
    if (!notice) return
    setShown(notice)
    const t = setTimeout(() => setShown((s) => (s?.id === notice.id ? null : s)), 3000)
    return () => clearTimeout(t)
  }, [notice])

  useEffect(() => {
    if (!shown) return
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setShown(null) }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [shown])

  if (!shown) return null
  return (
    <div key={shown.id} className={`toast ${shown.tone}`} role="status" onClick={() => setShown(null)}>
      <i className={`dot ${shown.tone === 'ok' ? 'live' : 'fail'}`} />
      {shown.text}
    </div>
  )
}
