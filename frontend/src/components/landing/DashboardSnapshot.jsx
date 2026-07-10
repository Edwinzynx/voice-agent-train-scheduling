import React, { useState, useEffect, useRef } from 'react'
import { Activity, Phone, PhoneCall, BarChart2, ShieldCheck, PieChart, ToggleLeft, ToggleRight, List, AlertCircle } from 'lucide-react'

export default function DashboardSnapshot() {
  const [isSimulating, setIsSimulating] = useState(true)
  const [totalCalls, setTotalCalls] = useState(128)
  const [activeCalls, setActiveCalls] = useState(3)
  const [successRate, setSuccessRate] = useState(94.6)
  const [recentLogs, setRecentLogs] = useState([
    { id: 1, phone: "+91 98765-XXXXX", intent: "Check PNR", status: "COMPLETED", msg: "PNR 4321098765 is Confirmed. coach S3/24." },
    { id: 2, phone: "+91 87654-XXXXX", intent: "Seat Availability", status: "COMPLETED", msg: "12 seats available on Rajdhani Express tomorrow." },
    { id: 3, phone: "+91 76543-XXXXX", intent: "Cancel Ticket", status: "COMPLETED", msg: "Ticket cancelled successfully. Refund initiated." },
    { id: 4, phone: "+91 99887-XXXXX", intent: "Live Delay", status: "COMPLETED", msg: "Train 12626 is running late by 25 minutes." }
  ])

  const intents = ["Check PNR", "Seat Availability", "Cancel Ticket", "Live Delay", "Book Ticket", "Verify Berth"]
  const sampleResponses = [
    "PNR 6789012345: Waitlisted (WL-4). High confirmation chance.",
    "Checking availability. 45 berths available in Sleeper coach S4.",
    "Cancellation failed. Refund already processed for PNR 8877665544.",
    "Train 12213: Arrived at New Delhi Platform 3.",
    "Ticket booked successfully. PNR generated: 9081726354.",
    "Berth confirmation: Coach A1, Berth 12 (Lower)."
  ]

  const timerRef = useRef(null)

  useEffect(() => {
    if (isSimulating) {
      timerRef.current = setInterval(() => {
        // Increment calls
        setTotalCalls(prev => prev + 1)
        
        // Randomize active calls
        setActiveCalls(Math.floor(Math.random() * 5) + 2)

        // Randomize success rate slightly
        setSuccessRate(prev => {
          const delta = (Math.random() - 0.4) * 0.2
          const next = prev + delta
          return Math.min(Math.max(next, 92), 98)
        })

        // Add a new random log
        const randomPhone = `+91 ${Math.floor(Math.random() * 90000) + 10000}-XXXXX`
        const idx = Math.floor(Math.random() * intents.length)
        const newLog = {
          id: Date.now(),
          phone: randomPhone,
          intent: intents[idx],
          status: Math.random() > 0.05 ? "COMPLETED" : "FAILED",
          msg: sampleResponses[idx]
        }

        setRecentLogs(prev => [newLog, ...prev.slice(0, 4)])
      }, 4000)
    } else {
      if (timerRef.current) clearInterval(timerRef.current)
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [isSimulating])

  return (
    <section id="dashboard-demo" className="landing-section" style={{
      borderTop: '1px solid var(--border-color)',
      paddingTop: '80px'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '16px' }}>
        <h2 className="landing-section-title" style={{ margin: 0, textAlign: 'left' }}>
          Live Command Center Snapshot
        </h2>
        
        {/* Toggle button */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          background: 'rgba(255, 255, 255, 0.05)',
          padding: '8px 16px',
          borderRadius: '20px',
          border: '1px solid var(--border-color)'
        }}>
          <span style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--text-secondary)' }}>
            {isSimulating ? 'SIMULATION RUNNING' : 'SIMULATION PAUSED'}
          </span>
          <button 
            onClick={() => setIsSimulating(!isSimulating)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', color: isSimulating ? 'var(--color-success)' : 'var(--text-secondary)' }}
          >
            {isSimulating ? <ToggleRight size={32} /> : <ToggleLeft size={32} />}
          </button>
        </div>
      </div>

      <p className="landing-section-subtitle" style={{ textAlign: 'left', margin: '0 0 32px 0', maxWidth: '800px' }}>
        Observe real-time operations, success rates, latency distribution, and automatic classification of incoming call intents.
      </p>

      {/* Main Dashboard Widget Panel */}
      <div className="dashboard-grid glass-panel" style={{ boxShadow: '0 20px 50px rgba(0,0,0,0.4)' }}>
        
        {/* Mock Sidebar */}
        <div className="dashboard-sidebar">
          {/* Brand Logo */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
            <div style={{
              background: 'linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%)',
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 8px rgba(99,102,241,0.2)'
            }}>
              <Phone size={16} color="white" />
            </div>
            <span style={{ fontWeight: '800', fontSize: '1rem', fontFamily: 'var(--font-title)', letterSpacing: '0.05em' }}>
              LOCOVOICE
            </span>
          </div>

          {/* Nav items */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px', borderRadius: '8px', background: 'rgba(99, 102, 241, 0.15)', color: 'var(--text-primary)', fontSize: '0.85rem', fontWeight: '600' }}>
              <Activity size={16} style={{ color: 'var(--color-primary)' }} />
              Live Operations
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px', borderRadius: '8px', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              <PhoneCall size={16} />
              Call Records
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px', borderRadius: '8px', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              <BarChart2 size={16} />
              Performance
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px', borderRadius: '8px', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              <ShieldCheck size={16} />
              FSM Testing
            </div>
          </div>

          <div style={{ marginTop: 'auto', borderTop: '1px solid var(--border-color)', paddingTop: '16px' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>CONNECTED GATEWAY</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '6px', fontSize: '0.75rem', color: 'var(--color-success)', fontWeight: '600' }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--color-success)', animation: 'pulse-glow 1.5s infinite' }} />
              DELHI-EAST-GW-3
            </div>
          </div>
        </div>

        {/* Main Panel content */}
        <div className="dashboard-main-view">
          
          {/* Header row stats cards */}
          <div className="dashboard-cards-row">
            <div className="dashboard-mini-card">
              <span className="lbl">Active Calls</span>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                <span className="val" style={{ color: 'var(--color-warning)' }}>{activeCalls}</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>/ 10 max</span>
              </div>
            </div>

            <div className="dashboard-mini-card">
              <span className="lbl">Total Calls Today</span>
              <span className="val">{totalCalls}</span>
            </div>

            <div className="dashboard-mini-card">
              <span className="lbl">AI Success Rate</span>
              <span className="val" style={{ color: 'var(--color-success)' }}>{successRate.toFixed(1)}%</span>
            </div>

            <div className="dashboard-mini-card">
              <span className="lbl">Avg Latency</span>
              <span className="val" style={{ color: 'var(--color-primary)' }}>320ms</span>
            </div>
          </div>

          {/* Visual Charts section */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1.8fr 1fr',
            gap: '16px'
          }}>
            {/* Call analytics chart */}
            <div className="dashboard-chart-card">
              <h4 style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '16px', fontWeight: '700' }}>
                Call Traffic Metrics
              </h4>
              <div style={{ height: '140px', position: 'relative' }}>
                {/* SVG Line chart */}
                <svg width="100%" height="100%" style={{ overflow: 'visible' }}>
                  {/* Grid lines */}
                  <line x1="0" y1="110" x2="100%" y2="110" stroke="rgba(255,255,255,0.05)" />
                  <line x1="0" y1="60" x2="100%" y2="60" stroke="rgba(255,255,255,0.05)" />
                  <line x1="0" y1="10" x2="100%" y2="10" stroke="rgba(255,255,255,0.05)" />
                  
                  {/* Gradient for area under line */}
                  <defs>
                    <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="var(--color-primary)" stopOpacity="0.25" />
                      <stop offset="100%" stopColor="var(--color-primary)" stopOpacity="0" />
                    </linearGradient>
                  </defs>

                  {/* Filled area path */}
                  <path 
                    d="M0,80 Q60,40 120,90 T240,30 T360,70 T480,20 L480,110 L0,110 Z" 
                    fill="url(#areaGrad)" 
                    style={{ transition: 'd 0.5s' }}
                  />

                  {/* Line path */}
                  <path 
                    d="M0,80 Q60,40 120,90 T240,30 T360,70 T480,20" 
                    fill="none" 
                    stroke="var(--color-primary)" 
                    strokeWidth="2.5" 
                    style={{ transition: 'd 0.5s' }}
                  />
                  
                  {/* Glowing line points */}
                  <circle cx="120" cy="90" r="4" fill="var(--color-primary)" />
                  <circle cx="240" cy="30" r="4" fill="var(--color-primary)" />
                  <circle cx="360" cy="70" r="4" fill="var(--color-primary)" />
                  <circle cx="480" cy="20" r="4" fill="var(--color-secondary)" />
                </svg>
              </div>
            </div>

            {/* Sentiment analysis chart */}
            <div className="dashboard-chart-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
              <h4 style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '12px', fontWeight: '700' }}>
                Intent Sentiment
              </h4>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <div style={{ position: 'relative', width: '80px', height: '80px' }}>
                  <svg width="80" height="80" viewBox="0 0 36 36" style={{ transform: 'rotate(-90deg)' }}>
                    <circle cx="18" cy="18" r="15.9" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="3.5" />
                    <circle cx="18" cy="18" r="15.9" fill="none" stroke="var(--color-success)" strokeWidth="3.5" strokeDasharray="72 28" />
                    <circle cx="18" cy="18" r="15.9" fill="none" stroke="var(--color-warning)" strokeWidth="3.5" strokeDasharray="18 82" strokeDashoffset="-72" />
                    <circle cx="18" cy="18" r="15.9" fill="none" stroke="var(--color-danger)" strokeWidth="3.5" strokeDasharray="10 90" strokeDashoffset="-90" />
                  </svg>
                  <div style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    fontFamily: 'var(--font-title)',
                    fontSize: '0.85rem',
                    fontWeight: '700'
                  }}>
                    72%
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem' }}>
                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--color-success)' }} />
                    <span>Positive: 72%</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem' }}>
                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--color-warning)' }} />
                    <span>Neutral: 18%</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem' }}>
                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--color-danger)' }} />
                    <span>Negative: 10%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Activity Feed log and task breakdown */}
          <div className="dashboard-logs-row">
            {/* Live Logs Feed */}
            <div className="dashboard-chart-card" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h4 style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: '700' }}>
                  Live Call Activity Feed
                </h4>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <List size={12} />
                  <span>Showing last 4 entries</span>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {recentLogs.map((log) => (
                  <div key={log.id} style={{
                    padding: '10px 14px',
                    borderRadius: '8px',
                    background: 'rgba(255, 255, 255, 0.02)',
                    border: '1px solid rgba(255, 255, 255, 0.04)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '4px',
                    animation: 'pulse-glow 1s ease-out'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '0.8rem', fontWeight: '700', color: 'var(--text-primary)' }}>{log.phone}</span>
                      <span style={{
                        fontSize: '0.65rem',
                        fontWeight: '700',
                        color: log.status === 'COMPLETED' ? 'var(--color-success)' : 'var(--color-danger)',
                        background: log.status === 'COMPLETED' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                        padding: '2px 6px',
                        borderRadius: '4px'
                      }}>
                        {log.intent.toUpperCase()}
                      </span>
                    </div>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', margin: 0 }}>
                      {log.msg}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Task distributions */}
            <div className="dashboard-chart-card" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <h4 style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: '700' }}>
                Task Conversion Rate
              </h4>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {[
                  { label: "PNR Check", rate: 92, count: "54 calls" },
                  { label: "Seat Enquiry", rate: 86, count: "39 calls" },
                  { label: "Booking Done", rate: 74, count: "21 calls" }
                ].map((item, i) => (
                  <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                      <span style={{ fontWeight: '600' }}>{item.label}</span>
                      <span style={{ color: 'var(--color-success)', fontWeight: '700' }}>{item.rate}% ({item.count})</span>
                    </div>
                    <div style={{ height: '6px', borderRadius: '3px', background: 'rgba(255, 255, 255, 0.05)', overflow: 'hidden' }}>
                      <div style={{ height: '100%', borderRadius: '3px', background: 'var(--color-success)', width: `${item.rate}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

        </div>

      </div>
    </section>
  )
}
