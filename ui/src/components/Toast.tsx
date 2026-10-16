import type { Notice } from '../api'

export function Toast({ notice }: { notice: Notice | null }) {
  if (!notice) return null
  return (
    <div key={notice.id} className={`toast ${notice.tone}`} role="status">
      <i className={`dot ${notice.tone === 'ok' ? 'live' : 'fail'}`} />
      {notice.text}
    </div>
  )
}
