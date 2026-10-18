import React from 'react'
import CommandCenter from '../CommandCenter'

export default function DashboardSnapshot({ backendUrl }) {
  return <section id="dashboard-demo" className="landing-section command-demo">
    <h2 className="landing-section-title">The LocoVoice Command Center</h2>
    <p className="landing-section-subtitle">Explore the same workspace used in the sandbox. Conversations use the connected backend; private metrics require owner access.</p>
    <CommandCenter backendUrl={backendUrl} embedded />
  </section>
}
