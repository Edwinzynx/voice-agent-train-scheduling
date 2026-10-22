import React from 'react'
import { Clock, Mic, MessageSquare } from 'lucide-react'

export default function LatencyMetrics({ onOpenMetrics }) {
  return <section id="latency-section" className="landing-section">
    <h2 className="landing-section-title">Measure the conversation</h2>
    <p className="landing-section-subtitle">Response time depends on the providers, network, and backend warm-up. The owner dashboard shows recorded processing metrics.</p>
    <div className="feature-grid">
      {[
        { icon: Mic, title: 'Voice input & output', text: 'Sarvam transcribes microphone audio and speaks the agent response. Speech time is separate from backend processing time.' },
        { icon: MessageSquare, title: 'Conversation & validation', text: 'Groq extracts intent and journey details. The dialogue flow validates dates, selections, and confirmation before querying trains.' },
        { icon: Clock, title: 'Recorded performance', text: 'Unlock Performance in the command center to inspect average session p50 and p90 processing times. No fixed latency guarantee is displayed.' },
      ].map(({ icon: Icon, title, text }) => <div className="glass-panel" key={title} style={{ padding: 28 }}><Icon size={24} style={{ color: '#a5b4fc', marginBottom: 16 }} /><h3 style={{ fontFamily: 'var(--font-title)', marginBottom: 12 }}>{title}</h3><p style={{ color: 'var(--text-secondary)', fontSize: '.88rem', lineHeight: 1.7 }}>{text}</p></div>)}
    </div>
    <div style={{ textAlign: 'center', marginTop: 24 }}>
      <button className="playground-button" onClick={onOpenMetrics}>View recorded latency metrics</button>
      <p style={{ color: 'var(--text-secondary)', fontSize: '.85rem', marginTop: 12 }}>Owner access required · Backend processing p50 and p90 from saved sessions. End-to-end voice latency is not yet measured.</p>
    </div>
  </section>
}
