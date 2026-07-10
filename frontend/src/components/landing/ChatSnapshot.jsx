import React, { useState, useEffect, useRef } from 'react'
import { MessageSquare, Send, Mic, Volume2, ShieldCheck, Clock } from 'lucide-react'

export default function ChatSnapshot() {
  const [messages, setMessages] = useState([
    { sender: 'agent', text: 'Namaste! I am LocoVoice, your Indian Railways Assistant. How can I help you today? 🎙️', delay: 0 }
  ])
  const [isTyping, setIsTyping] = useState(false)
  const [currentLatency, setCurrentLatency] = useState(null)
  
  const chatBodyRef = useRef(null)

  const presetQueries = [
    {
      q: "Is Rajdhani delayed today?",
      a: "Train 12301 - Rajdhani Express is running on time today. It is expected to arrive at New Delhi Platform 4 at 10:15 AM.",
      latency: 310
    },
    {
      q: "Check PNR 4321098765",
      a: "PNR 4321098765: Status is CONFIRMED. Coach S3, Berth 24 (Middle Berth, Sleeper Class) on Goa Express.",
      latency: 420
    },
    {
      q: "Cancel ticket TXN9028",
      a: "Verifying credentials... Booking TXN9028 cancelled successfully. A refund of ₹740.00 will be credited to your account in 3-5 bank days.",
      latency: 480
    },
    {
      q: "Seat availability for tomorrow?",
      a: "For tomorrow (Kalka Shatabdi, 12005): 23 seats available in AC Chair Car (CC) and 8 seats available in Executive Class (EC).",
      latency: 340
    }
  ]

  const handleQueryClick = (query) => {
    if (isTyping) return

    // Add user message
    setMessages(prev => [...prev, { sender: 'user', text: query.q }])
    setIsTyping(true)
    setCurrentLatency(null)

    // Simulate network + generation delay
    setTimeout(() => {
      setIsTyping(false)
      setCurrentLatency(query.latency)
      setMessages(prev => [...prev, { sender: 'agent', text: query.a, latency: query.latency }])
    }, query.latency + 800) // add slight padding for natural feel
  }

  useEffect(() => {
    if (chatBodyRef.current) {
      const scrollContainer = chatBodyRef.current
      const timer = setTimeout(() => {
        scrollContainer.scrollTo({
          top: scrollContainer.scrollHeight,
          behavior: 'smooth'
        })
      }, 60)
      return () => clearTimeout(timer)
    }
  }, [messages, isTyping])

  return (
    <section id="chat-demo-section" className="landing-section" style={{
      borderTop: '1px solid var(--border-color)',
      paddingTop: '80px',
      paddingBottom: '100px'
    }}>
      <h2 className="landing-section-title">Experience the Natural Flow</h2>
      <p className="landing-section-subtitle">
        Click any of the preset passenger queries below to watch LocoVoice process requests and speak responses with ultra-low latency.
      </p>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '1.2fr 1fr',
        gap: '48px',
        alignItems: 'center'
      }}>
        
        {/* Left Side: Preset queries list */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div className="glass-panel" style={{ padding: '32px' }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: '800', fontFamily: 'var(--font-title)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <MessageSquare size={20} style={{ color: 'var(--color-primary)' }} />
              Test Queries Playground
            </h3>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '24px', lineHeight: '1.6' }}>
              LocoVoice is built using deterministic state machine guardrails (FSM). Try sending the commands below to see the instant response cycle.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {presetQueries.map((item, idx) => (
                <button 
                  key={idx}
                  onClick={() => handleQueryClick(item)}
                  disabled={isTyping}
                  className="preset-pill"
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '16px 20px',
                    borderRadius: '12px'
                  }}
                >
                  <span style={{ fontWeight: '600', color: 'var(--text-primary)' }}>"{item.q}"</span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--color-primary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    Run Simulation &rarr;
                  </span>
                </button>
              ))}
            </div>

            {/* Response speed details */}
            {currentLatency && (
              <div style={{
                marginTop: '24px',
                padding: '16px',
                borderRadius: '8px',
                background: 'rgba(16, 185, 129, 0.08)',
                border: '1px solid rgba(16, 185, 129, 0.2)',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                animation: 'pulse-glow 1s ease-out'
              }}>
                <Clock size={18} style={{ color: 'var(--color-success)' }} />
                <span style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                  Last transaction completed in <strong style={{ color: 'var(--color-success)' }}>{currentLatency}ms</strong> with 100% token consistency.
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Right Side: Virtual Mobile Phone Snapshot */}
        <div>
          <div className="phone-mockup">
            <div className="phone-screen">
              
              {/* Header */}
              <div className="phone-header">
                <div style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, var(--color-primary), var(--color-secondary))',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <Volume2 size={16} color="white" />
                </div>
                <div>
                  <h4 style={{ fontSize: '0.85rem', fontWeight: '700', color: 'white', margin: 0 }}>LocoVoice AI</h4>
                  <span style={{ fontSize: '0.65rem', color: 'var(--color-success)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--color-success)' }} />
                    Active Connection
                  </span>
                </div>
                <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <ShieldCheck size={16} style={{ color: 'var(--color-primary)' }} />
                </div>
              </div>

              {/* Chat Feed body */}
              <div className="phone-body" ref={chatBodyRef}>
                {messages.map((msg, idx) => (
                  <div key={idx} className={`bubble ${msg.sender}`} style={{
                    position: 'relative'
                  }}>
                    {msg.text}
                    {msg.latency && (
                      <span style={{
                        display: 'block',
                        fontSize: '0.65rem',
                        color: 'var(--text-muted)',
                        marginTop: '4px',
                        textAlign: 'right'
                      }}>
                        ⚡ {msg.latency}ms
                      </span>
                    )}
                  </div>
                ))}
                
                {/* Typing Indicator */}
                {isTyping && (
                  <div className="bubble agent" style={{ display: 'flex', gap: '4px', alignItems: 'center', padding: '12px 16px' }}>
                    <div style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--text-secondary)', animation: 'wave-animate 1s infinite 0.1s' }} />
                    <div style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--text-secondary)', animation: 'wave-animate 1s infinite 0.2s' }} />
                    <div style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--text-secondary)', animation: 'wave-animate 1s infinite 0.3s' }} />
                  </div>
                )}
              </div>

              {/* Input section (Mock) */}
              <div className="phone-footer">
                <div style={{
                  flex: 1,
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '20px',
                  padding: '8px 14px',
                  fontSize: '0.8rem',
                  color: 'var(--text-muted)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <span>Speak or type query...</span>
                  <Mic size={14} style={{ color: 'var(--text-secondary)' }} />
                </div>
                <button style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  background: 'var(--color-primary)',
                  border: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer'
                }}>
                  <Send size={12} color="white" />
                </button>
              </div>

            </div>
          </div>
        </div>

      </div>
    </section>
  )
}
