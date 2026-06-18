import React, { useState, useEffect } from 'react'
import { Database, FileText, CheckCircle, XCircle, Search, RefreshCw, Layers } from 'lucide-react'

export default function CallLogger({ backendUrl, activeCallData }) {
  const [calls, setCalls] = useState([])
  const [selectedCall, setSelectedCall] = useState(null)
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)

  const fetchCalls = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${backendUrl}/dashboard/calls?page=${page}&limit=5&search=${search}`)
      if (res.ok) {
        const data = await res.json()
        setCalls(data.calls)
        setTotal(data.total)
      }
    } catch (err) {
      console.error("Error fetching calls:", err)
    }
    setLoading(false)
  }

  useEffect(() => {
    fetchCalls()
  }, [backendUrl, page, search])

  const selectCall = async (callId) => {
    try {
      const res = await fetch(`${backendUrl}/dashboard/calls/${callId}`)
      if (res.ok) {
        const data = await res.json()
        setSelectedCall(data)
      }
    } catch (err) {
      console.error("Error fetching call details:", err)
    }
  }

  // Combine live data slots or fallback to empty
  const liveSlots = activeCallData?.slots || {}
  const liveState = activeCallData?.state || 'IDLE'

  const slotsToDisplay = [
    { label: 'Source Station', key: 'source', value: liveSlots.source },
    { label: 'Destination Station', key: 'destination', value: liveSlots.destination },
    { label: 'Travel Date', key: 'date', value: liveSlots.date },
    { label: 'Coach Class', key: 'class_code', value: liveSlots.class_code },
    { label: 'Passenger Name', key: 'passenger_name', value: liveSlots.passenger_name },
    { label: 'Train Number', key: 'train_no', value: liveSlots.train_no },
    { label: 'PNR Number', key: 'pnr_number', value: liveSlots.pnr_number },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* 1. Live Slots Monitor */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers style={{ color: 'var(--color-primary)' }} />
            Active Brain FSM Tracker
          </h2>
          <span style={{
            padding: '4px 10px',
            borderRadius: '12px',
            fontSize: '0.75rem',
            fontWeight: 600,
            background: liveState !== 'IDLE' && liveState !== 'DISCONNECTED' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(255, 255, 255, 0.05)',
            color: liveState !== 'IDLE' && liveState !== 'DISCONNECTED' ? 'var(--color-success)' : 'var(--text-muted)',
            border: `1px solid ${liveState !== 'IDLE' && liveState !== 'DISCONNECTED' ? 'rgba(16, 185, 129, 0.25)' : 'var(--border-color)'}`
          }}>
            FSM State: {liveState}
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '12px' }}>
          {slotsToDisplay.map((slot) => (
            <div key={slot.key} style={{
              background: slot.value ? 'rgba(16, 185, 129, 0.08)' : 'rgba(255, 255, 255, 0.02)',
              border: `1px solid ${slot.value ? 'rgba(16, 185, 129, 0.3)' : 'var(--border-color)'}`,
              borderRadius: '10px',
              padding: '12px',
              textAlign: 'center',
              transition: 'var(--transition-smooth)'
            }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                {slot.label}
              </div>
              <div style={{
                fontSize: '0.85rem',
                fontWeight: 600,
                color: slot.value ? 'var(--color-success)' : 'var(--text-muted)'
              }}>
                {slot.value || 'Unfilled'}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 2. Call History & Database Logs */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Database style={{ color: 'var(--color-primary)' }} />
            Call History Database
          </h2>
          <button 
            onClick={fetchCalls}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--color-primary)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.85rem'
            }}
          >
            <RefreshCw size={14} className={loading ? 'spinning-icon' : ''} />
            Refresh
          </button>
        </div>

        <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Search by transcript, summary or phone..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              style={{
                width: '100%',
                padding: '10px 12px 10px 36px',
                borderRadius: '8px',
                border: '1px solid var(--border-color)',
                background: 'rgba(255, 255, 255, 0.03)',
                color: 'var(--text-primary)',
                fontFamily: 'inherit',
                outline: 'none',
                fontSize: '0.9rem'
              }}
            />
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {calls.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)' }}>
              No call records found.
            </div>
          ) : (
            calls.map((call) => (
              <div
                key={call.id}
                onClick={() => selectCall(call.id)}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '12px 16px',
                  borderRadius: '10px',
                  background: selectedCall?.call.id === call.id ? 'rgba(99, 102, 241, 0.08)' : 'rgba(255, 255, 255, 0.01)',
                  border: `1px solid ${selectedCall?.call.id === call.id ? 'rgba(99, 102, 241, 0.3)' : 'var(--border-color)'}`,
                  cursor: 'pointer',
                  transition: 'var(--transition-smooth)'
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>{call.caller_number}</span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {new Date(call.start_time).toLocaleTimeString()}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', maxWidth: '400px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {call.summary || 'No summary generated'}
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    {call.duration_seconds.toFixed(0)}s
                  </span>
                  {call.success ? (
                    <CheckCircle size={18} style={{ color: 'var(--color-success)' }} />
                  ) : (
                    <XCircle size={18} style={{ color: 'var(--text-muted)' }} />
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Pagination */}
        {total > 5 && (
          <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginTop: '16px' }}>
            <button
              disabled={page === 1}
              onClick={() => setPage(p => p - 1)}
              style={{ padding: '6px 12px', border: '1px solid var(--border-color)', borderRadius: '6px', background: 'none', color: 'var(--text-primary)', cursor: page === 1 ? 'not-allowed' : 'pointer' }}
            >
              Prev
            </button>
            <span style={{ display: 'flex', alignItems: 'center', fontSize: '0.85rem' }}>Page {page} of {Math.ceil(total / 5)}</span>
            <button
              disabled={page >= Math.ceil(total / 5)}
              onClick={() => setPage(p => p + 1)}
              style={{ padding: '6px 12px', border: '1px solid var(--border-color)', borderRadius: '6px', background: 'none', color: 'var(--text-primary)', cursor: page >= Math.ceil(total / 5) ? 'not-allowed' : 'pointer' }}
            >
              Next
            </button>
          </div>
        )}
      </div>

      {/* 3. Call turns log inspector (modal style or under-panel) */}
      {selectedCall && (
        <div className="glass-panel" style={{ padding: '24px', borderTop: '2px solid var(--color-primary)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FileText size={18} style={{ color: 'var(--color-primary)' }} />
              Inspect Call: {selectedCall.call.id.substring(0, 12)}
            </h3>
            <button
              onClick={() => setSelectedCall(null)}
              style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.9rem' }}
            >
              Close
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px', background: 'rgba(0,0,0,0.1)', borderRadius: '8px', padding: '12px', fontSize: '0.85rem' }}>
            <div>
              <p style={{ color: 'var(--text-secondary)' }}>Status: <strong style={{ color: selectedCall.call.success ? 'var(--color-success)' : 'var(--text-muted)' }}>{selectedCall.call.success ? "Success" : "Failed / Cancelled"}</strong></p>
              <p style={{ color: 'var(--text-secondary)' }}>Duration: <strong>{selectedCall.call.duration_seconds.toFixed(1)} seconds</strong></p>
            </div>
            <div>
              <p style={{ color: 'var(--text-secondary)' }}>Avg p50 Latency: <strong>{selectedCall.call.p50_latency_ms.toFixed(0)} ms</strong></p>
              <p style={{ color: 'var(--text-secondary)' }}>Avg p90 Latency: <strong>{selectedCall.call.p90_latency_ms.toFixed(0)} ms</strong></p>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '250px', overflowY: 'auto' }}>
            {selectedCall.logs.map((log) => (
              <div key={log.id} style={{
                background: log.direction === 'inbound' ? 'rgba(99,102,241,0.06)' : 'rgba(255,255,255,0.02)',
                borderLeft: `3px solid ${log.direction === 'inbound' ? 'var(--color-primary)' : log.direction === 'outbound' ? 'var(--color-secondary)' : 'var(--text-muted)'}`,
                padding: '8px 12px',
                borderRadius: '0 8px 8px 0',
                fontSize: '0.85rem'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                  <span>{log.direction.toUpperCase()} ({log.state})</span>
                  {log.latency_ms > 0 && <span style={{ color: 'var(--color-secondary)' }}>Latency: {log.latency_ms.toFixed(0)}ms</span>}
                </div>
                <div>{log.text}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
