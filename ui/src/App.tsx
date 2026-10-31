// AI-assisted code: generated and revised with Claude Opus 5.5
// under the author's direction; reviewed and tested by the author
// (see the thesis section "Use of AI tools").
import { useEffect, useState } from 'react'
import { NewRunPage } from './components/NewRunPage'
import { RunPage } from './components/RunPage'
import { RunsPage } from './components/RunsPage'

function useHash() {
  const [hash, setHash] = useState(location.hash)
  useEffect(() => {
    const onChange = () => setHash(location.hash)
    addEventListener('hashchange', onChange)
    return () => removeEventListener('hashchange', onChange)
  }, [])
  return hash
}

export function App() {
  const hash = useHash()
  useEffect(() => { scrollTo({ top: 0 }) }, [hash.split('?')[0]])
  if (hash.startsWith('#/new')) return <NewRunPage key={hash} />
  const m = hash.match(/^#\/run\/([^/?#]+)/)
  if (!m) return <RunsPage />
  const runId = decodeURIComponent(m[1])
  return <RunPage key={runId} runId={runId} />
}
