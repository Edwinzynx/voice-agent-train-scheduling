import React, { useState } from 'react'
import LandingPage from './components/landing/LandingPage'
import CommandCenter from './components/CommandCenter'
import './App.css'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || (import.meta.env.DEV ? 'http://localhost:8000' : 'https://voice-agent-train-scheduling.onrender.com')

export default function App() {
  const [viewMode, setViewMode] = useState('landing')
  const navigate = mode => { setViewMode(mode); window.scrollTo({ top: 0 }) }
  return viewMode === 'landing'
    ? <LandingPage onLaunchConsole={() => navigate('sandbox')} onOpenMetrics={() => navigate('performance')} />
    : <CommandCenter backendUrl={BACKEND_URL} initialSection={viewMode === 'performance' ? 'performance' : 'operations'} onExit={() => navigate('landing')} />
}
