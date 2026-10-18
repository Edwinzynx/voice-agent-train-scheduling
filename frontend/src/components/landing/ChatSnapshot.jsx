import React from 'react'
import { ArrowRight, MessageSquare } from 'lucide-react'

export default function ChatSnapshot({ onLaunchConsole }) {
  return <section id="chat-demo-section" className="landing-section">
    <h2 className="landing-section-title">Plan your next journey</h2>
    <p className="landing-section-subtitle">Open Live Operations to speak or type a query, choose a train, and review your travel details.</p>
    <div style={{ display: 'flex', justifyContent: 'center' }}><button className="playground-button primary" onClick={onLaunchConsole}><MessageSquare size={18} /> Open conversation workspace <ArrowRight size={18} /></button></div>
  </section>
}
