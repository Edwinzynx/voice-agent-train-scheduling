import React, { useState, useEffect } from 'react'
import { Award, BarChart3, TrendingUp, Play, CheckCircle2, AlertCircle, Clock } from 'lucide-react'

export default function EvalRunner({ backendUrl, onNewEval }) {
  const [runs, setRuns] = useState([])
  const [running, setRunning] = useState(false)
  const [selectedRun, setSelectedRun] = useState(null)

  const fetchRuns = async () => {
    try {
      const res = await fetch(`${backendUrl}/eval/runs`)
      if (res.ok) {
        const data = await res.json()
        setRuns(data)
        if (data.length > 0 && !selectedRun) {
          setSelectedRun(data[0])
        }
      }
    } catch (err) {
      console.error("Error fetching evaluations:", err)
    }
  }

  useEffect(() => {
    fetchRuns()
  }, [backendUrl])

  const runEvaluation = async () => {
    setRunning(true)
    try {
      const res = await fetch(`${backendUrl}/eval/run`, { method: 'POST' })
      if (res.ok) {
        // Poll for completion
        let attempts = 0
        const interval = setInterval(async () => {
          attempts++
          const checkRes = await fetch(`${backendUrl}/eval/runs`)
          if (checkRes.ok) {
            const data = await checkRes.json()
            setRuns(data)
            // If the latest run is fully complete (total matches completed)
            if (data.length > 0 && data[0].completed_cases === data[0].total_cases) {
              clearInterval(interval)
              setRunning(false)
              setSelectedRun(data[0])
              if (onNewEval) onNewEval()
            }
          }
          if (attempts > 30) {
            clearInterval(interval)
            setRunning(false)
          }
        }, 1000)
      } else {
        setRunning(false)
      }
    } catch (err) {
      console.error(err)
      setRunning(false)
    }
  }

  return (
    <div className="glass-panel" style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Award style={{ color: 'var(--color-primary)' }} />
          LLM-as-a-Judge Evaluation Suite
        </h2>
        <button
          onClick={runEvaluation}
          disabled={running}
          style={{
            padding: '8px 16px',
            borderRadius: '8px',
            border: 'none',
            background: running ? 'var(--text-muted)' : 'linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%)',
            color: 'white',
            fontWeight: 600,
            cursor: running ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '0.85rem'
          }}
        >
          <Play size={14} />
          {running ? "Simulating..." : "Run Eval Suite"}
        </button>
      </div>

      {/* Stats Cards */}
      {selectedRun && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '16px', marginBottom: '24px' }}>
          
          <div style={{ background: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--border-color)', padding: '16px', borderRadius: '12px', textAlign: 'center' }}>
            <div style={{ display: 'flex', justifyContent: 'center', color: 'var(--color-success)', marginBottom: '8px' }}>
              <TrendingUp size={20} />
            </div>
            <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{selectedRun.overall_success_rate}%</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Task Success Rate</div>
          </div>

          <div style={{ background: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--border-color)', padding: '16px', borderRadius: '12px', textAlign: 'center' }}>
            <div style={{ display: 'flex', justifyContent: 'center', color: 'var(--color-primary)', marginBottom: '8px' }}>
              <BarChart3 size={20} />
            </div>
            <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{selectedRun.avg_slot_accuracy}%</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Slot Accuracy</div>
          </div>

          <div style={{ background: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--border-color)', padding: '16px', borderRadius: '12px', textAlign: 'center' }}>
            <div style={{ display: 'flex', justifyContent: 'center', color: 'var(--color-secondary)', marginBottom: '8px' }}>
              <Clock size={20} />
            </div>
            <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{selectedRun.p50_latency}ms</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>p50 Turn Latency</div>
          </div>

          <div style={{ background: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--border-color)', padding: '16px', borderRadius: '12px', textAlign: 'center' }}>
            <div style={{ display: 'flex', justifyContent: 'center', color: 'var(--color-warning)', marginBottom: '8px' }}>
              <Clock size={20} />
            </div>
            <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{selectedRun.p90_latency}ms</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>p90 Turn Latency</div>
          </div>

        </div>
      )}

      {/* Latency Comparison Graph */}
      {selectedRun && (
        <div style={{ marginBottom: '24px' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '12px' }}>Latency Percentiles Curve (p50 / p90 / p99)</h3>
          
          <div style={{ background: 'rgba(0,0,0,0.15)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '16px 20px', display: 'flex', alignItems: 'flex-end', height: '140px', gap: '30px', justifyContent: 'center' }}>
            
            {/* p50 Bar */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1, maxWidth: '80px' }}>
              <div style={{ color: 'var(--color-secondary)', fontSize: '0.8rem', fontWeight: 600, marginBottom: '6px' }}>{selectedRun.p50_latency}ms</div>
              <div style={{
                width: '100%',
                height: `${Math.min(100, (selectedRun.p50_latency / 1200) * 100)}px`,
                background: 'linear-gradient(to top, var(--color-primary), var(--color-secondary))',
                borderRadius: '6px 6px 0 0',
                minHeight: '15px'
              }}></div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '6px' }}>p50</div>
            </div>

            {/* p90 Bar */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1, maxWidth: '80px' }}>
              <div style={{ color: 'var(--color-warning)', fontSize: '0.8rem', fontWeight: 600, marginBottom: '6px' }}>{selectedRun.p90_latency}ms</div>
              <div style={{
                width: '100%',
                height: `${Math.min(100, (selectedRun.p90_latency / 1200) * 100)}px`,
                background: 'linear-gradient(to top, var(--color-secondary), var(--color-warning))',
                borderRadius: '6px 6px 0 0',
                minHeight: '15px'
              }}></div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '6px' }}>p90</div>
            </div>

            {/* p99 Bar */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1, maxWidth: '80px' }}>
              <div style={{ color: 'var(--color-danger)', fontSize: '0.8rem', fontWeight: 600, marginBottom: '6px' }}>{selectedRun.p99_latency}ms</div>
              <div style={{
                width: '100%',
                height: `${Math.min(100, (selectedRun.p99_latency / 1200) * 100)}px`,
                background: 'linear-gradient(to top, var(--color-warning), var(--color-danger))',
                borderRadius: '6px 6px 0 0',
                minHeight: '15px'
              }}></div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '6px' }}>p99</div>
            </div>

          </div>
        </div>
      )}

      {/* Case-by-Case Breakdown */}
      {selectedRun && selectedRun.results && (
        <div>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '12px' }}>Scenario Test Suite Breakdown</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {selectedRun.results.map((res, index) => (
              <div key={index} style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 14px',
                borderRadius: '8px',
                background: 'rgba(255, 255, 255, 0.02)',
                border: '1px solid var(--border-color)',
                fontSize: '0.85rem'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  {res.success ? (
                    <CheckCircle2 size={16} style={{ color: 'var(--color-success)' }} />
                  ) : (
                    <AlertCircle size={16} style={{ color: 'var(--color-danger)' }} />
                  )}
                  <span>{res.description}</span>
                </div>
                <div style={{ display: 'flex', gap: '12px', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  <span>Intent: <strong style={{ color: 'var(--text-primary)' }}>{res.intent_matched ? "Match" : "Mismatch"}</strong></span>
                  <span>Slots: <strong style={{ color: 'var(--text-primary)' }}>{(res.slot_accuracy * 100).toFixed(0)}%</strong></span>
                  <span>Latency: <strong style={{ color: 'var(--text-primary)' }}>{res.avg_latency.toFixed(0)}ms</strong></span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
