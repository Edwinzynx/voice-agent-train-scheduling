import React, { useState, useEffect } from 'react'
import { Timer, Zap, ShieldCheck, ChevronRight } from 'lucide-react'

export default function LatencyMetrics() {
  const [animate, setAnimate] = useState(false)

  useEffect(() => {
    // Trigger animations slightly after mount
    const t = setTimeout(() => setAnimate(true), 300)
    return () => clearTimeout(t)
  }, [])

  const latencyStats = [
    {
      percentile: "p50 Latency",
      value: "320 ms",
      color: "var(--color-primary)",
      desc: "Simpler intents like greetings, platform checks, and yes/no confirmations. Processes instantly in memory."
    },
    {
      percentile: "p90 Latency",
      value: "480 ms",
      color: "var(--color-secondary)",
      desc: "Comprehensive database transactions, such as live berth queries or seat confirmation lookups."
    },
    {
      percentile: "p99 Latency",
      value: "890 ms",
      color: "var(--color-warning)",
      desc: "Worst-case scenario timings caused by occasional cellular network packet loss or API cold starts."
    }
  ]

  const stackDetails = [
    { name: "Deepgram Nova-2 (STT)", ms: 120, pct: "25%", color: "#3b82f6", detail: "Fast streaming audio chunk processing & translation." },
    { name: "Llama 3 on Groq + FSM Guardrails", ms: 180, pct: "37.5%", color: "#a855f7", detail: "Deterministic State Machine matching & intent slots parsing." },
    { name: "ElevenLabs Turbo v2 (TTS)", ms: 150, pct: "31.25%", color: "#10b981", detail: "Low-latency streaming audio synthesis." },
    { name: "Network Overhead", ms: 30, pct: "6.25%", color: "#f59e0b", detail: "WebSocket connection overhead." }
  ]

  const comparisons = [
    { name: "LocoVoice (Groq + FSM)", ms: 480, color: "linear-gradient(90deg, var(--color-primary), var(--color-secondary))", width: "25%" },
    { name: "Typical Twilio + Dialogflow BOT", ms: 1850, color: "#4b5563", width: "65%" },
    { name: "Custom LangChain / GPT-4o Bot", ms: 3200, color: "#ef4444", width: "100%" }
  ]

  return (
    <section id="latency-section" className="landing-section" style={{
      borderTop: '1px solid var(--border-color)',
      paddingTop: '80px'
    }}>
      <h2 className="landing-section-title">Speed is Our Core Feature</h2>
      <p className="landing-section-subtitle">
        Studies show that voice bots with latency above 1 second feel sluggish and unnatural. LocoVoice leverages custom optimizations to stay well under the human conversation threshold.
      </p>

      {/* Latency Percentiles Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: '24px',
        marginBottom: '64px'
      }}>
        {latencyStats.map((stat, idx) => (
          <div 
            key={idx} 
            className="glass-panel" 
            style={{
              padding: '30px',
              display: 'flex',
              flexDirection: 'column',
              gap: '16px',
              position: 'relative',
              overflow: 'hidden'
            }}
          >
            <div style={{
              position: 'absolute',
              top: '-10px',
              right: '-10px',
              width: '80px',
              height: '80px',
              background: `radial-gradient(circle, ${stat.color} 5%, transparent 70%)`,
              opacity: 0.15,
              pointerEvents: 'none'
            }} />

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: '700', textTransform: 'uppercase', color: 'var(--text-secondary)', letterSpacing: '0.05em' }}>
                {stat.percentile}
              </span>
              <Timer size={18} style={{ color: stat.color }} />
            </div>

            <div style={{
              fontSize: '2.5rem',
              fontWeight: '900',
              color: stat.color,
              fontFamily: 'var(--font-title)',
              margin: '8px 0'
            }}>
              {stat.value}
            </div>

            <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
              {stat.desc}
            </p>
          </div>
        ))}
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '40px',
        alignItems: 'start'
      }}>
        {/* Comparison bars */}
        <div className="glass-panel" style={{ padding: '32px' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: '800', fontFamily: 'var(--font-title)', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Zap size={18} style={{ color: 'var(--color-primary)' }} />
            Latency Comparison (p90 response delay)
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {comparisons.map((c, i) => (
              <div key={i} className="latency-bar-row">
                <div className="latency-bar-info">
                  <span style={{ fontWeight: '600', color: i === 0 ? 'white' : 'var(--text-secondary)' }}>{c.name}</span>
                  <span style={{ fontWeight: '700', color: i === 0 ? 'var(--color-primary)' : 'var(--text-muted)' }}>{c.ms} ms</span>
                </div>
                <div className="latency-bar-outer">
                  <div 
                    className="latency-bar-inner"
                    style={{
                      background: c.color,
                      width: animate ? c.width : '0%',
                      transitionDelay: `${i * 150}ms`
                    }}
                  >
                    {animate && `${c.ms}ms`}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Stack breakdown list */}
        <div className="glass-panel" style={{ padding: '32px' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: '800', fontFamily: 'var(--font-title)', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShieldCheck size={18} style={{ color: 'var(--color-success)' }} />
            Where does the time go? (480ms p90 breakdown)
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {stackDetails.map((item, idx) => (
              <div key={idx} style={{
                display: 'flex',
                alignItems: 'center',
                gap: '16px',
                padding: '12px',
                borderRadius: '8px',
                background: 'rgba(255, 255, 255, 0.02)',
                border: '1px solid rgba(255, 255, 255, 0.03)'
              }}>
                <div style={{
                  width: '12px',
                  height: '12px',
                  borderRadius: '50%',
                  backgroundColor: item.color,
                  flexShrink: 0
                }} />
                
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', fontWeight: '600' }}>
                    <span>{item.name}</span>
                    <span style={{ color: 'var(--text-secondary)' }}>{item.ms}ms</span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                    {item.detail}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
