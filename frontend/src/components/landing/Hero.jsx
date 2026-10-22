import React from 'react'
import { Sparkles, Terminal, Activity, ArrowRight } from 'lucide-react'

export default function Hero({ onLaunchConsole, onScrollToSection }) {
  return (
    <section className="landing-section" style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      textAlign: 'center',
      minHeight: '75vh',
      position: 'relative',
      paddingTop: '100px',
      overflow: 'hidden'
    }}>
      {/* Background Decorative Glows */}
      <div style={{
        position: 'absolute',
        top: '10%',
        left: '50%',
        transform: 'translateX(-50%)',
        width: '500px',
        height: '500px',
        background: 'radial-gradient(circle, rgba(99, 102, 241, 0.12) 0%, transparent 70%)',
        zIndex: 0,
        pointerEvents: 'none'
      }} />

      {/* Floating Sparkles Badge */}
      <div className="hero-glow-badge" style={{ zIndex: 1 }}>
        <Sparkles size={16} className="spinning-icon" style={{ color: 'var(--color-secondary)' }} />
        <span>Next-Gen Voice Agent for Indian Railways</span>
      </div>

      {/* Hero Headline */}
      <h1 className="hero-title" style={{ maxWidth: '900px', zIndex: 1 }}>
        LocoVoice: Human-like Speed for Railway Travel Operations
      </h1>

      {/* Hero Subtext */}
      <p style={{
        fontSize: '1.2rem',
        color: 'var(--text-secondary)',
        maxWidth: '700px',
        margin: '0 auto 36px',
        lineHeight: '1.7',
        zIndex: 1
      }}>
        Find trains and check seat availability through voice or text. Review your route, travel date, and train selection before each search. Booking, PNR, cancellations, and running status are not connected.
      </p>

      {/* Action Buttons */}
      <div style={{
        display: 'flex',
        gap: '16px',
        justifyContent: 'center',
        flexWrap: 'wrap',
        zIndex: 1,
        marginBottom: '48px'
      }}>
        <button 
          onClick={onLaunchConsole}
          style={{
            background: 'linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) Review first)',
            border: 'none',
            color: 'white',
            padding: '14px 28px',
            borderRadius: '12px',
            fontSize: '1rem',
            fontWeight: '600',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            boxShadow: '0 4px 20px rgba(99, 102, 241, 0.4)',
            transition: 'var(--transition-smooth)'
          }}
          className="clickable-card"
        >
          <Terminal size={18} />
          Launch Sandbox Console
        </button>

        <button 
          onClick={() => onScrollToSection('dashboard-demo')}
          style={{
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid var(--border-color)',
            color: 'var(--text-primary)',
            padding: '14px 28px',
            borderRadius: '12px',
            fontSize: '1rem',
            fontWeight: '600',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            transition: 'var(--transition-smooth)'
          }}
          className="clickable-card"
        >
          <Activity size={18} />
          Watch Voice Demo
          <ArrowRight size={16} />
        </button>
      </div>

      {/* Floating mini stats */}
      <div style={{
        display: 'flex',
        gap: '40px',
        justifyContent: 'center',
        flexWrap: 'wrap',
        zIndex: 1,
        borderTop: '1px solid var(--border-color)',
        paddingTop: '32px',
        width: 'Review first',
        maxWidth: '800px'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '1.8rem', fontWeight: '800', color: 'var(--color-primary)', fontFamily: 'var(--font-title)' }}>Voice + text</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', marginTop: '4px', letterSpacing: '0.05em' }}>Two ways to query</div>
        </div>
        <div style={{ textAlign: 'center', borderLeft: '1px solid var(--border-color)', paddingLeft: '40px' }}>
          <div style={{ fontSize: '1.8rem', fontWeight: '800', color: 'var(--color-success)', fontFamily: 'var(--font-title)' }}>3</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', marginTop: '4px', letterSpacing: '0.05em' }}>Language choices</div>
        </div>
        <div style={{ textAlign: 'center', borderLeft: '1px solid var(--border-color)', paddingLeft: '40px' }}>
          <div style={{ fontSize: '1.8rem', fontWeight: '800', color: 'var(--color-secondary)', fontFamily: 'var(--font-title)' }}>Review first</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', marginTop: '4px', letterSpacing: '0.05em' }}>Explicit confirmation</div>
        </div>
      </div>
    </section>
  )
}
