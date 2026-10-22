import React, { useCallback, useEffect, useState } from 'react'
import { Activity, ArrowLeft, BarChart2, LockKeyhole, PhoneCall, RefreshCw, ShieldCheck, Train } from 'lucide-react'
import WebRTCCall from './WebRTCCall'
import CallLogger from './CallLogger'
import EvalRunner from './EvalRunner'
import './CommandCenter.css'

const sections = [
  { id: 'operations', label: 'Live Operations', icon: Activity },
  { id: 'records', label: 'Call Records', icon: PhoneCall },
  { id: 'performance', label: 'Performance', icon: BarChart2 },
  { id: 'testing', label: 'FSM Testing', icon: ShieldCheck },
]

export default function CommandCenter({ backendUrl, onExit, embedded = false, initialSection = 'operations' }) {
  const [section, setSection] = useState(initialSection)
  const [adminToken, setAdminToken] = useState('')
  const [tokenDraft, setTokenDraft] = useState('')
  const [adminError, setAdminError] = useState('')
  const [unlocking, setUnlocking] = useState(false)
  const [stats, setStats] = useState(null)
  const [statsError, setStatsError] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)
  const [capabilities, setCapabilities] = useState(null)
  const [activeCallData, setActiveCallData] = useState({ callId: null, state: 'DISCONNECTED', slots: {} })
  const handleCallStateChange = useCallback(update => setActiveCallData(previous => ({ ...previous, ...update })), [])

  useEffect(() => {
    const controller = new AbortController()
    fetch(`${backendUrl}/calls/capabilities`, { signal: controller.signal }).then(response => {
      if (!response.ok) throw new Error('Service unavailable')
      return response.json()
    }).then(setCapabilities).catch(error => { if (error.name !== 'AbortError') setCapabilities({ ready: false, message: 'Backend unavailable. Try refreshing.' }) })
    return () => controller.abort()
  }, [backendUrl, refreshKey])

  useEffect(() => {
    if (!adminToken) return
    let active = true
    const controller = new AbortController()
    const refresh = async () => {
      try {
        const response = await fetch(`${backendUrl}/dashboard/stats`, { headers: { Authorization: `Bearer ${adminToken}` }, signal: controller.signal })
        if (!response.ok) throw new Error('Metrics could not be refreshed. Check owner access and retry.')
        const next = await response.json()
        if (active) { setStats(next); setStatsError('') }
      } catch (error) { if (active) { setStatsError(error.message); setStats(null) } }
    }
    refresh()
    const interval = setInterval(refresh, 5000)
    return () => { active = false; controller.abort(); clearInterval(interval) }
  }, [adminToken, backendUrl, refreshKey])

  const unlock = async event => {
    event.preventDefault()
    if (!tokenDraft.trim()) return
    setUnlocking(true)
    setAdminError('')
    try {
      const response = await fetch(`${backendUrl}/dashboard/stats`, { headers: { Authorization: `Bearer ${tokenDraft.trim()}` } })
      if (!response.ok) throw new Error(response.status === 503 ? 'Set ADMIN_TOKEN in Render and redeploy before signing in.' : response.status === 401 ? 'The owner token did not match. Try again.' : 'Owner access could not be verified. Try again.')
      setStats(await response.json())
      setAdminToken(tokenDraft.trim())
      setTokenDraft('')
    } catch (error) { setAdminError(error.message) }
    finally { setUnlocking(false) }
  }
  const lock = () => { setAdminToken(''); setStats(null); setStatsError(''); setAdminError('') }
  const metric = (key, suffix = '') => {
    if (stats?.[key] == null) return '—'
    const value = Number(stats[key])
    if (suffix === ' ms' && value < 1) return '<1 ms'
    return `${value.toLocaleString('en-IN', { maximumFractionDigits: suffix === ' ms' ? 2 : 0 })}${suffix}`
  }
  const current = sections.find(item => item.id === section)

  return <div className={`command-center ${embedded ? 'embedded' : ''}`}>
    <aside className="command-sidebar">
      <div className="command-brand"><span><Train size={21} /></span><div>LOCOVOICE<small>COMMAND CENTER</small></div></div>
      <nav aria-label="Command center">
        {sections.map(({ id, label, icon: Icon }) => <button key={id} aria-current={section === id ? 'page' : undefined} onClick={() => setSection(id)}><Icon size={17} />{label}{id !== 'operations' && !adminToken && <LockKeyhole size={12} className="nav-lock" />}</button>)}
      </nav>
      <div className="sidebar-access">
        <div className="sidebar-label"><ShieldCheck size={14} /> OWNER ACCESS</div>
        {adminToken ? <><p>Owner dashboard unlocked.</p><button className="playground-button" onClick={lock}><LockKeyhole size={14} /> Lock dashboard</button></> : <form onSubmit={unlock}>
          <p>Unlock private metrics, call records, and evaluations.</p>
          <input aria-label="Owner access token" type="password" autoComplete="off" placeholder="Owner access token" value={tokenDraft} onChange={event => setTokenDraft(event.target.value)} />
          <button className="playground-button" disabled={unlocking || !tokenDraft.trim()}>{unlocking ? 'Verifying…' : 'Unlock dashboard'}</button>
          {adminError && <p role="alert" className="owner-error">{adminError}</p>}
        </form>}
      </div>
      <div className="sidebar-service"><span className="sidebar-label">VOICE SERVICE</span><strong className={capabilities?.ready ? 'service-ready' : ''}><i />{!capabilities ? 'Checking backend…' : capabilities.ready ? capabilities.environment === 'development' ? 'Local debugging' : 'Configured' : 'Unavailable'}</strong><small>{capabilities?.environment === 'development' ? 'Development backend' : 'Sarvam + Groq'}</small></div>
      {onExit && <button className="exit-console" onClick={onExit}><ArrowLeft size={15} /> Back to project</button>}
    </aside>
    <main className="command-main">
      <header className="command-heading"><div><span className="playground-eyebrow">RAILWAY CONVERSATION WORKSPACE</span><h1>{current.label}</h1><p>{section === 'operations' ? 'Search, speak, and review your journey in one place.' : section === 'records' ? 'Review saved conversations and their extracted journey details.' : section === 'performance' ? 'Measured backend processing times from completed sessions.' : 'Inspect dialogue evaluations and run owner diagnostics.'}</p></div><button className="command-refresh" onClick={() => setRefreshKey(key => key + 1)} aria-label="Refresh backend status and metrics"><RefreshCw size={16} /></button></header>
      {adminToken && section === 'performance' && <div className="command-metrics">
        <div className="dashboard-mini-card"><span className="lbl">Active sessions</span><strong className="val metric-amber">{metric('active_calls')}</strong><small>{stats ? 'Connected right now' : 'Owner access required'}</small></div>
        <div className="dashboard-mini-card"><span className="lbl">Total sessions</span><strong className="val">{metric('total_calls')}</strong><small>{stats ? 'Recorded in this database' : 'Owner access required'}</small></div>
        <div className="dashboard-mini-card"><span className="lbl">Avg. session p50</span><strong className="val metric-indigo">{metric('avg_p50_ms', ' ms')}</strong><small>{stats ? 'Backend processing time' : 'Owner access required'}</small></div>
        <div className="dashboard-mini-card"><span className="lbl">Avg. session p90</span><strong className="val metric-purple">{metric('avg_p90_ms', ' ms')}</strong><small>{stats ? 'Backend processing time' : 'Owner access required'}</small></div>
      </div>}
      {statsError && section === 'performance' && <p className="owner-error" role="alert">{statsError}</p>}
      {adminToken && section === 'performance' && stats && <p className="metrics-context" role="status">{stats.total_calls === 0 ? 'No calls are stored in the connected database yet. If previous calls are missing, check that the backend uses persistent database storage.' : `${stats.completed_calls ?? 'Recorded'} completed sessions in the connected database.`} A dash means no measurement is available. Dialogue evaluation appears only after an evaluation run.</p>}
      {capabilities && !capabilities.ready && <p className="backend-notice" role="status">{capabilities.message}</p>}
      <section hidden={section !== 'operations'} aria-label="Live operations workspace">
        <div className="operations-title"><h2>Passenger conversation</h2><span>{activeCallData.callId ? activeCallData.state.replaceAll('_', ' ') : 'NO ACTIVE SESSION'}</span></div>
        <WebRTCCall backendUrl={backendUrl} onCallStateChange={handleCallStateChange} />
      </section>
      {section !== 'operations' && !adminToken && <div className="owner-gate glass-panel"><LockKeyhole size={30} /><h2>Owner access required</h2><p>Use your owner token in the sidebar to view {current.label.toLowerCase()}.</p><p>Your token is the <code>ADMIN_TOKEN</code> you set in Render. Public train queries do not need one.</p></div>}
      {adminToken && section === 'records' && <CallLogger backendUrl={backendUrl} adminToken={adminToken} activeCallData={activeCallData} />}
      {adminToken && section === 'performance' && <section className="performance-panel glass-panel"><h2>Session performance</h2><p>Metrics refresh every five seconds. Processing time excludes microphone capture, speech synthesis, and audio playback.</p><dl><div><dt>Average session duration</dt><dd>{metric('avg_duration_seconds', ' s')}</dd></div><div><dt>Latest dialogue evaluation</dt><dd>{metric('latest_eval_accuracy', '%')}</dd></div></dl><p>Evaluation scores describe the diagnostic suite; they do not measure successful railway bookings. History reflects the current backend database.</p></section>}
      {adminToken && section === 'testing' && <EvalRunner backendUrl={backendUrl} adminToken={adminToken} onNewEval={() => setRefreshKey(key => key + 1)} />}
      <footer className="command-footer">Train search & seat availability · Booking services are not connected</footer>
    </main>
  </div>
}
