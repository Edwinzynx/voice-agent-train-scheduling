import React, { useState, useEffect } from 'react'
import { Train, Info } from 'lucide-react'
import WebRTCCall from './components/WebRTCCall'
import CallLogger from './components/CallLogger'
import Settings from './components/Settings'
import EvalRunner from './components/EvalRunner'
import './App.css'

// Backend URL pointing to the FastAPI port
const BACKEND_URL = "http://localhost:8000"

export default function App() {
  const [activeCallData, setActiveCallData] = useState({
    callId: null,
    state: 'IDLE',
    slots: {}
  })
  
  const [stats, setStats] = useState({
    total_calls: 0,
    success_rate: 0,
    avg_p50_ms: 0,
    avg_p90_ms: 0,
    active_calls: 0,
    latest_eval_accuracy: 0
  })

  const fetchStats = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/dashboard/stats`)
      if (res.ok) {
        const data = await res.json()
        setStats(data)
      }
    } catch (err) {
      console.warn("Error fetching stats:", err)
    }
  }

  useEffect(() => {
    fetchStats()
    // Poll stats occasionally
    const interval = setInterval(fetchStats, 5000)
    return () => clearInterval(interval)
  }, [])

  const handleCallStateUpdate = (update) => {
    setActiveCallData({
      callId: update.callId,
      state: update.state || activeCallData.state,
      slots: update.slots ? { ...activeCallData.slots, ...update.slots } : activeCallData.slots
    })
    
    // Refresh stats if call completes
    if (update.state === 'END') {
      fetchStats()
    }
  }

  return (
    <div className="app-container">
      {/* Premium Dashboard Header */}
      <header className="app-header">
        <div className="app-title-container">
          <div style={{
            background: 'linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%)',
            padding: '8px',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 12px rgba(99, 102, 241, 0.3)'
          }}>
            <Train size={24} color="white" />
          </div>
          <div>
            <h1 className="app-title">LocoVoice</h1>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Indian Railways Conversational Agent</span>
          </div>
        </div>

        {/* Real-time Ticker stats */}
        <div className="stats-bar">
          <div className="stat-item">
            <span className="stat-val">{stats.total_calls}</span>
            <span className="stat-lbl">Total Calls</span>
          </div>
          <div className="stat-item" style={{ borderLeft: '1px solid var(--border-color)', paddingLeft: '24px' }}>
            <span className="stat-val" style={{ color: 'var(--color-success)' }}>{stats.success_rate}%</span>
            <span className="stat-lbl">Call Success</span>
          </div>
          <div className="stat-item" style={{ borderLeft: '1px solid var(--border-color)', paddingLeft: '24px' }}>
            <span className="stat-val">{stats.avg_p50_ms.toFixed(0)}ms</span>
            <span className="stat-lbl">p50 Latency</span>
          </div>
          <div className="stat-item" style={{ borderLeft: '1px solid var(--border-color)', paddingLeft: '24px' }}>
            <span className="stat-val" style={{ color: 'var(--color-secondary)' }}>{stats.latest_eval_accuracy}%</span>
            <span className="stat-lbl">Eval Success</span>
          </div>
          <div className="stat-item" style={{ borderLeft: '1px solid var(--border-color)', paddingLeft: '24px' }}>
            <span className="stat-val" style={{ color: 'var(--color-warning)' }}>{stats.active_calls}</span>
            <span className="stat-lbl">Active calls</span>
          </div>
        </div>
      </header>

      {/* Main Grid Workspace */}
      <main className="app-main">
        {/* Left Column: Call Voice Terminal + Configurations */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <WebRTCCall 
            backendUrl={BACKEND_URL} 
            onCallStateChange={handleCallStateUpdate} 
          />
          <Settings 
            backendUrl={BACKEND_URL} 
          />
        </div>

        {/* Right Column: Active State Logs + Evaluation panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <CallLogger 
            backendUrl={BACKEND_URL} 
            activeCallData={activeCallData} 
          />
          <EvalRunner 
            backendUrl={BACKEND_URL}
            onNewEval={fetchStats}
          />
        </div>
      </main>

      {/* Footer info banner */}
      <footer style={{
        padding: '16px',
        textAlign: 'center',
        fontSize: '0.8rem',
        color: 'var(--text-muted)',
        borderTop: '1px solid var(--border-color)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        gap: '6px'
      }}>
        <Info size={14} />
        Supports dynamic voice transitions for booking, cancellations, seat availability, live train status, and PNR status checks.
      </footer>
    </div>
  )
}
