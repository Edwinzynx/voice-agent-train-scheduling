import React from 'react'
import Hero from './Hero'
import KeyFeatures from './KeyFeatures'
import LatencyMetrics from './LatencyMetrics'
import DashboardSnapshot from './DashboardSnapshot'
import ChatSnapshot from './ChatSnapshot'
import { Train, ExternalLink, Terminal } from 'lucide-react'

export default function LandingPage({ onLaunchConsole }) {
  const scrollToSection = (id) => {
    const el = document.getElementById(id)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      
      {/* Landing Page Navigation Header */}
      <header className="app-header" style={{
        background: 'rgba(11, 15, 25, 0.75)',
        backdropFilter: 'blur(16px)',
        borderBottom: '1px solid var(--border-color)'
      }}>
        {/* Logo */}
        <div className="app-title-container" style={{ cursor: 'pointer' }} onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
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
            <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Indian Railways Conversational Agent</span>
          </div>
        </div>

        {/* Mid Navigation items */}
        <nav style={{
          display: 'flex',
          gap: '24px',
          alignItems: 'center'
        }}>
          <button 
            onClick={() => scrollToSection('features-section')}
            style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', fontSize: '0.9rem', fontWeight: '600', cursor: 'pointer', transition: 'var(--transition-smooth)' }}
            className="preset-pill"
          >
            Features
          </button>
          <button 
            onClick={() => scrollToSection('latency-section')}
            style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', fontSize: '0.9rem', fontWeight: '600', cursor: 'pointer', transition: 'var(--transition-smooth)' }}
            className="preset-pill"
          >
            Latency Metrics
          </button>
          <button 
            onClick={() => scrollToSection('dashboard-demo')}
            style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', fontSize: '0.9rem', fontWeight: '600', cursor: 'pointer', transition: 'var(--transition-smooth)' }}
            className="preset-pill"
          >
            Live Dashboard
          </button>
          <button 
            onClick={() => scrollToSection('chat-demo-section')}
            style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', fontSize: '0.9rem', fontWeight: '600', cursor: 'pointer', transition: 'var(--transition-smooth)' }}
            className="preset-pill"
          >
            Chat Sandbox
          </button>
        </nav>

        {/* CTA Launch Button */}
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <button 
            onClick={onLaunchConsole}
            style={{
              background: 'linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%)',
              border: 'none',
              color: 'white',
              padding: '10px 20px',
              borderRadius: '10px',
              fontSize: '0.9rem',
              fontWeight: '700',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              boxShadow: '0 4px 12px rgba(99, 102, 241, 0.25)'
            }}
            className="clickable-card"
          >
            <Terminal size={14} />
            Launch Sandbox
          </button>
        </div>
      </header>

      {/* Main Sections */}
      <main style={{ flex: 1 }}>
        <Hero 
          onLaunchConsole={onLaunchConsole} 
          onScrollToSection={scrollToSection} 
        />
        
        <KeyFeatures />
        
        <LatencyMetrics />
        
        <DashboardSnapshot />
        
        <ChatSnapshot />
      </main>

      {/* Landing Footer */}
      <footer style={{
        padding: '32px 16px',
        textAlign: 'center',
        fontSize: '0.85rem',
        color: 'var(--text-secondary)',
        borderTop: '1px solid var(--border-color)',
        background: 'rgba(11, 15, 25, 0.4)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '12px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: '700', color: 'white' }}>
          <Train size={18} style={{ color: 'var(--color-primary)' }} />
          <span>LocoVoice AI</span>
        </div>
        <p style={{ maxWidth: '600px', margin: 0, lineHeight: '1.6' }}>
          An open-source, deterministic voice agent architecture optimized for Indian Railways travel booking, PNR verification, live statuses, and instant cancellations.
        </p>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '8px' }}>
          © {new Date().getFullYear()} LocoVoice. All rights reserved.
        </div>
      </footer>
      
    </div>
  )
}
