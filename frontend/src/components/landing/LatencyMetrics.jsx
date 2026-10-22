import React, { useEffect, useState } from 'react'
import { Activity, Clock, Timer, CheckCircle } from 'lucide-react'

export default function LatencyMetrics({ backendUrl }) {
  const [metrics, setMetrics] = useState(null)
  const [error, setError] = useState(false)
  const [refresh, setRefresh] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    let pending = false
    const load = async () => {
      if (pending) return
      pending = true
      try {
        const response = await fetch(`${backendUrl}/performance/summary`, { signal: controller.signal })
        if (!response.ok) throw new Error('Metrics unavailable')
        const data = await response.json()
        if (!controller.signal.aborted) { setMetrics(data); setError(false) }
      } catch (err) {
        if (err.name !== 'AbortError') setError(true)
      } finally { pending = false }
    }
    load()
    const interval = setInterval(() => { if (!document.hidden) load() }, 60000)
    return () => { controller.abort(); clearInterval(interval) }
  }, [backendUrl, refresh])

  const format = (key, unit = '') => {
    const value = metrics?.[key]
    if (value == null) return '—'
    if (unit === ' ms' && value > 0 && value < 1) return '<1 ms'
    return `${Number(value).toLocaleString('en-IN', { maximumFractionDigits: 2 })}${unit}`
  }
  const cards = [
    { icon: Activity, label: 'Average session p50', value: format('avg_session_p50_ms', ' ms'), note: 'Backend processing · typical response' },
    { icon: Timer, label: 'Average session p90', value: format('avg_session_p90_ms', ' ms'), note: 'Backend processing · slower responses' },
    { icon: CheckCircle, label: 'Completed sessions', value: format('completed_sessions'), note: 'Recorded in persistent storage' },
    { icon: Clock, label: 'Average session duration', value: format('avg_session_duration_seconds', ' s'), note: 'Time from session start to completion' },
  ]
  return <section id="latency-section" className="landing-section">
    <h2 className="landing-section-title">Real performance, measured.</h2>
    <p className="landing-section-subtitle">Recorded metrics from completed conversations. Updated every minute.</p>
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 20 }}>
      {cards.map(({ icon: Icon, label, value, note }) => <div className="glass-panel" key={label} style={{ padding: 28 }}>
        <Icon size={24} style={{ color: '#a5b4fc', marginBottom: 16 }} />
        <h3 style={{ fontSize: '.9rem', color: 'var(--text-secondary)', marginBottom: 12 }}>{label}</h3>
        <strong style={{ display: 'block', fontSize: '2rem', marginBottom: 12 }}>{value}</strong>
        <p style={{ color: 'var(--text-secondary)', fontSize: '.8rem', lineHeight: 1.6 }}>{note}</p>
      </div>)}
    </div>
    <div style={{ textAlign: 'center', color: 'var(--text-secondary)', fontSize: '.85rem', lineHeight: 1.8, marginTop: 24 }}>
      <p role="status">{error ? (metrics ? 'Showing the last available measurements. Refresh temporarily unavailable.' : 'Metrics are temporarily unavailable. The backend may be waking up.') : !metrics ? 'Loading recorded metrics…' : metrics.measured_sessions === 0 ? 'No measured responses yet. Completed conversations will populate these metrics.' : `Based on ${metrics.measured_sessions.toLocaleString('en-IN')} measured sessions · Updated ${new Date(metrics.updated_at).toLocaleTimeString()}`}</p>
      {error && <button className="playground-button" onClick={() => setRefresh(value => value + 1)}>Retry metrics</button>}
      <p>Latency values are averages of each session’s p50 and p90, not percentiles across all responses. They exclude microphone capture, speech synthesis, and playback. A dash means no measurement is available.</p>
    </div>
  </section>
}
