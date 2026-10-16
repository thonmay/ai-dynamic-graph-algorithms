import { useCallback, useEffect, useReducer, useRef, useState } from 'react'
import { applyEvents, describeCommand, initialState, type RunState } from './state'
import type { Command, RunEvent } from './types'

/** Fetch JSON from the evoalgo server (paths are relative to the page). */
export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(path, { headers: { 'content-type': 'application/json' }, ...init })
  const body = await r.json().catch(() => ({}))
  if (!r.ok) throw new Error(typeof body?.detail === 'string' ? body.detail : `HTTP ${r.status}`)
  return body as T
}

export interface Notice {
  id: number
  tone: 'ok' | 'error'
  text: string
}

const FLUSH_MS = 60

/**
 * Live event stream for one run. Reconnects with backoff and resumes from the
 * last event received, so a dropped connection never loses or repeats events.
 */
export function useRunStream(runId: string) {
  const [state, dispatch] = useReducer(
    (s: RunState, events: RunEvent[]) => applyEvents(s, events), undefined, initialState)
  const [connected, setConnected] = useState(false)
  const [notice, setNotice] = useState<Notice | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const lastSeq = useRef(-1)

  useEffect(() => {
    let closed = false
    let retry = 0
    let reconnect: number | undefined
    let flushTimer: number | undefined
    let buffer: RunEvent[] = []
    const flush = () => {
      flushTimer = undefined
      const batch = buffer
      buffer = []
      if (batch.length) dispatch(batch)
    }

    const connect = () => {
      const url = new URL(`api/runs/${encodeURIComponent(runId)}/ws?from=${lastSeq.current + 1}`, location.href)
      url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
      const ws = new WebSocket(url)
      wsRef.current = ws
      ws.onopen = () => {
        retry = 0
        setConnected(true)
      }
      ws.onmessage = (m) => {
        let msg: any
        try {
          msg = JSON.parse(m.data)
        } catch {
          return
        }
        if (msg?.type === 'queued') {
          setNotice({ id: Date.now(), tone: 'ok', text: `${describeCommand(msg)} queued · next generation` })
        } else if (msg?.type === 'error') {
          setNotice({ id: Date.now(), tone: 'error', text: String(msg.reason ?? 'rejected') })
        } else if (typeof msg?.seq === 'number') {
          lastSeq.current = Math.max(lastSeq.current, msg.seq)
          buffer.push(msg as RunEvent)
          flushTimer ??= window.setTimeout(flush, FLUSH_MS)
        }
      }
      ws.onclose = () => {
        setConnected(false)
        if (wsRef.current === ws) wsRef.current = null
        if (!closed) reconnect = window.setTimeout(connect, Math.min(10_000, 500 * 2 ** retry++))
      }
    }

    connect()
    return () => {
      closed = true
      clearTimeout(reconnect)
      clearTimeout(flushTimer)
      wsRef.current?.close()
    }
  }, [runId])

  const send = useCallback((command: Command) => {
    const ws = wsRef.current
    if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(command))
    else setNotice({ id: Date.now(), tone: 'error', text: 'Not connected. Retrying.' })
  }, [])

  return { state, connected, notice, send }
}
