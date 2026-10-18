import React from 'react'
import { Globe, ShieldAlert, Cpu, HeartHandshake, Database, BarChart2, CheckCircle2 } from 'lucide-react'

export default function KeyFeatures() {
  const features = [
    {
      icon: <Globe size={24} style={{ color: 'var(--color-primary)' }} />,
      title: "Multilingual Voice Support",
      desc: "Choose English, Hindi, or Hinglish for your conversation. Sarvam handles production speech input and spoken responses."
    },
    {
      icon: <ShieldAlert size={24} style={{ color: 'var(--color-secondary)' }} />,
      title: "Journey Validation",
      desc: "Checks required journey details, travel dates, and train selection before acting. Availability and fares come from the connected train service."
    },
    {
      icon: <Cpu size={24} style={{ color: 'var(--color-success)' }} />,
      title: "Natural Voice Conversations",
      desc: "Speak after the agent finishes, or type a reply during your call. Responses stay visible in the conversation."
    },
    {
      icon: <HeartHandshake size={24} style={{ color: 'var(--color-warning)' }} />,
      title: "Review Before Confirming",
      desc: "Review the route, date, and selected class before confirming. Change details whenever the readback does not match your journey."
    },
    {
      icon: <Database size={24} style={{ color: 'var(--color-danger)' }} />,
      title: "Connected Train Data",
      desc: "Search trains and inspect seat availability through the existing railway data provider. Unconnected booking services are explicitly unavailable."
    },
    {
      icon: <BarChart2 size={24} style={{ color: 'var(--color-primary)' }} />,
      title: "Automated Evaluation Framework",
      desc: "Owners can inspect recorded dialogue evaluations and backend processing metrics. Diagnostic results are separate from live railway operations."
    }
  ]

  const useCases = [
    "Train searches by route and date",
    "Travel date validation",
    "Train and class selection",
    "Seat availability checks",
    "Journey review and corrections",
    "Owner conversation records"
  ]

  return (
    <section id="features-section" className="landing-section">
      <h2 className="landing-section-title">Engineered for Indian Railways Operations</h2>
      <p className="landing-section-subtitle">
        Explore the connected train search and seat availability flow, with explicit confirmation and clear service limitations.
      </p>

      {/* Grid of Key Features */}
      <div className="feature-grid" style={{ marginBottom: '64px' }}>
        {features.map((feat, idx) => (
          <div 
            key={idx} 
            className="glass-panel clickable-card" 
            style={{
              padding: '30px',
              display: 'flex',
              flexDirection: 'column',
              gap: '16px',
              border: '1px solid var(--border-color)',
              borderRadius: '16px',
              background: 'var(--bg-secondary)'
            }}
          >
            <div style={{
              background: 'rgba(255, 255, 255, 0.03)',
              width: '48px',
              height: '48px',
              borderRadius: '10px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: '1px solid rgba(255, 255, 255, 0.05)'
            }}>
              {feat.icon}
            </div>
            <div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: '700', marginBottom: '8px', color: 'var(--text-primary)', fontFamily: 'var(--font-title)' }}>
                {feat.title}
              </h3>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                {feat.desc}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Top Use Cases checklist */}
      <div className="glass-panel" style={{
        padding: '40px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '32px',
        background: 'radial-gradient(circle at center, rgba(168, 85, 247, 0.03) 0%, transparent 80%), var(--bg-secondary)'
      }}>
        <h3 style={{ fontSize: '1.5rem', fontWeight: '800', fontFamily: 'var(--font-title)', color: 'var(--text-primary)' }}>
          Supported Use Cases
        </h3>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '20px',
          width: '100%',
          maxWidth: '900px'
        }}>
          {useCases.map((useCase, idx) => (
            <div key={idx} style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              fontSize: '0.95rem',
              color: 'var(--text-primary)'
            }}>
              <CheckCircle2 size={20} style={{ color: 'var(--color-success)', flexShrink: 0 }} />
              <span>{useCase}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
