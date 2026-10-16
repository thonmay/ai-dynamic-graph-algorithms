import { useEffect, useState } from 'react'
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
  const m = useHash().match(/^#\/run\/([^/?#]+)/)
  if (!m) return <RunsPage />
  const runId = decodeURIComponent(m[1])
  return <RunPage key={runId} runId={runId} />
}
