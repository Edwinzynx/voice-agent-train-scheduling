import React from 'react'
import { Globe, ShieldAlert, Cpu, HeartHandshake, Database, BarChart2, CheckCircle2 } from 'lucide-react'

export default function KeyFeatures() {
  const features = [
    {
      icon: <Globe size={24} style={{ color: 'var(--color-primary)' }} />,
      title: "Multilingual Voice Support",
      desc: "Supports 50+ languages and dialects, specifically optimized for Indian English, Hindi, and Hinglish (code-switching) with dynamic context adaptation."
    },
    {
      icon: <ShieldAlert size={24} style={{ color: 'var(--color-secondary)' }} />,
      title: "Hallucination-Free Guardrails",
      desc: "Uses a deterministic Finite State Machine (FSM) to bind the LLM response flow, ensuring zero hallucination for ticket fares, seat bookings, and PNR details."
    },
    {
      icon: <Cpu size={24} style={{ color: 'var(--color-success)' }} />,
      title: "Natural Voice Conversations",
      desc: "Sub-500ms voice response latency, active voice interruption handling, and intelligent filler-word ingestion for a highly conversational flow."
    },
    {
      icon: <HeartHandshake size={24} style={{ color: 'var(--color-warning)' }} />,
      title: "Human-in-the-Loop",
      desc: "Seamless escalation to human railway station desk agents when conversational parameters fall outside the automated FSM rules, maintaining full call transcript history."
    },
    {
      icon: <Database size={24} style={{ color: 'var(--color-danger)' }} />,
      title: "Deep API Integrations",
      desc: "Direct database connectors to real-time seat inventory, live PNR databases, SMS-gateways, and Twilio voice networks for out-of-the-box deployment."
    },
    {
      icon: <BarChart2 size={24} style={{ color: 'var(--color-primary)' }} />,
      title: "Automated Evaluation Framework",
      desc: "Integrated offline and online simulator evaluating success rates, intent-matching accuracy, and slot correctness over hundreds of concurrent testing threads."
    }
  ]

  const useCases = [
    "Automatic Ticket Booking & Confirmation",
    "Real-time PNR Status Checks",
    "Seat Availability & Berth Selection Querying",
    "Live Train Delays & Platform Notifications",
    "Ticket Cancellations & Instant Refunds Processing",
    "Passenger Grievances & Emergency Handoffs"
  ]

  return (
    <section id="features-section" className="landing-section">
      <h2 className="landing-section-title">Engineered for Indian Railways Operations</h2>
      <p className="landing-section-subtitle">
        LocoVoice replaces slow and frustrating IVR interfaces with an intelligent, conversational voice bot that resolves booking flows in seconds.
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
