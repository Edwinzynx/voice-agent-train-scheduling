import React, { useEffect, useRef, useState } from 'react'
import { ArrowRight, Check, Mic, Pause, Play, RotateCcw, Train, Volume2, VolumeX } from 'lucide-react'
import './ConversationDemo.css'

const scenes = [
  ['Passenger', 0, 7, 'Hi! Can you find me a train from New Delhi to Chandigarh tomorrow morning?'],
  ['LocoVoice', 1, 8, 'Of course. New Delhi to Chandigarh, tomorrow morning. Shall I search for trains on this route?'],
  ['Passenger', 1, 4, 'Yes, please. Show me the morning options.'],
  ['LocoVoice', 2, 11, 'Here is a morning option: the Kalka Shatabdi. In this example, it departs at 7:40 and reaches Chandigarh at 11:05. Would you like to check seats?'],
  ['Passenger', 2, 5, 'Yes. Are there seats in AC Chair Car, and what is the fare?'],
  ['LocoVoice', 3, 7, 'AC Chair Car on the Kalka Shatabdi for tomorrow. Shall I check availability and fare?'],
  ['Passenger', 3, 3, 'That is right. Please check.'],
  ['LocoVoice', 4, 10, 'In these sample results, 42 seats are available at 720 rupees per person. Your journey takes 3 hours and 25 minutes.'],
]
const total = scenes.reduce((sum, scene) => sum + scene[2], 0)
const clock = seconds => `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, '0')}`

export default function DashboardSnapshot() {
  const [position, setPosition] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [muted, setMuted] = useState(true)
  const [audioFailed, setAudioFailed] = useState(false)
  const speaking = useRef(false)
  const audioSupported = typeof window !== 'undefined' && 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window
  let boundary = 0
  const found = scenes.findIndex(scene => { boundary += scene[2]; return position < boundary })
  const index = found < 0 ? scenes.length - 1 : found
  const [speaker, stage, , text] = scenes[index]
  const ended = position >= total

  useEffect(() => {
    if (!playing) return
    let previous = performance.now()
    const timer = window.setInterval(() => {
      const now = performance.now()
      const delta = (now - previous) / 1000
      previous = now
      setPosition(current => Math.min(current + delta, speaking.current ? boundary - .05 : total))
    }, 100)
    return () => window.clearInterval(timer)
  }, [playing, boundary])
  useEffect(() => { if (ended) setPlaying(false) }, [ended])
  useEffect(() => {
    if (!audioSupported || muted || !playing || ended) return
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = 'en-IN'
    utterance.pitch = speaker === 'Passenger' ? .85 : 1.15
    const voices = window.speechSynthesis.getVoices().filter(voice => voice.lang.startsWith('en'))
    const voice = voices.find(voice => voice.lang === 'en-IN') || voices[0]
    if (voice) utterance.voice = voice
    speaking.current = true
    utterance.onend = () => { speaking.current = false }
    utterance.onerror = event => { speaking.current = false; if (!['canceled', 'interrupted'].includes(event.error)) { setAudioFailed(true); setMuted(true) } }
    window.speechSynthesis.speak(utterance)
    return () => { utterance.onend = null; utterance.onerror = null; speaking.current = false; window.speechSynthesis.cancel() }
  }, [index, muted, playing, audioSupported, ended, speaker, text])

  return <section id="dashboard-demo" className="landing-section conversation-demo">
    <div className="demo-eyebrow">A CONVERSATION, FROM START TO FINISH</div>
    <h2 className="landing-section-title">Ask. Listen. Find your train.</h2>
    <p className="landing-section-subtitle">Watch a passenger find a morning train, ask about seats, and get the details — all through conversation.</p>
    <div className={`demo-player ${playing ? 'is-playing' : ''}`}>
      <div className="demo-topbar"><strong>● &nbsp; LocoVoice in action</strong><span>SIMULATED DEMO · SAMPLE DATA</span></div>
      <div className="demo-stage">
        <div className="demo-conversation">
          <div className="demo-scene-label">0{index + 1} / 08 <span>{['Tell us your journey', 'Confirm the route', 'Explore a train', 'Choose your class', 'Get the details'][stage]}</span></div>
          <div className="demo-speakers">{['Passenger', 'LocoVoice'].map(name => <div className={`demo-speaker ${speaker === name ? 'is-active' : ''}`} key={name}>
            <div className={`demo-avatar ${name === 'LocoVoice' ? 'agent' : ''}`}>{name === 'Passenger' ? <Mic size={29} /> : <Train size={29} />}</div>
            <strong>{name}</strong><span>{speaker === name ? playing ? 'Speaking' : ended ? 'Complete' : 'Ready to play' : 'Listening'}</span>
          </div>)}</div>
          <div className="demo-wave" aria-hidden="true">{Array.from({ length: 35 }, (_, i) => <i key={i} style={{ '--bar-height': `${10 + ((i * 17) % 36)}px`, '--bar-delay': `${(i % 7) * -.13}s` }} />)}</div>
          <div className="demo-caption" aria-live="polite" aria-atomic="true"><span>{speaker === 'Passenger' ? 'YOU ASK' : 'LOCOVOICE REPLIES'}</span><p>“{text}”</p></div>
        </div>
        <aside className="demo-journey" aria-label="Example journey details">
          <div className="demo-eyebrow">YOUR JOURNEY, COMING TOGETHER</div>
          <h3>From a question<br />to a travel plan.</h3>
          <div className="demo-route"><span>New Delhi <small>NDLS</small></span><ArrowRight size={19} /><span>Chandigarh <small>CDG</small></span></div>
          <div className="demo-detail"><span>Travel date</span><strong>{stage >= 1 ? 'Tomorrow · Morning' : 'Listening to your request'}</strong></div>
          <div className={`demo-result ${stage >= 2 ? 'revealed' : ''}`}><Train size={20} /><strong>{stage >= 2 ? 'Kalka Shatabdi' : 'Your train appears here'}</strong><p>{stage >= 2 ? '07:40 → 11:05 · 3h 25m' : 'The agent confirms your route first.'}</p></div>
          <div className="demo-detail"><span>Travel class</span><strong>{stage >= 3 ? 'AC Chair Car (CC)' : 'Not selected yet'}</strong></div>
          <div className={`demo-availability ${stage === 4 ? 'revealed' : ''}`}><Check size={18} /><div><strong>{stage === 4 ? '42 seats available · ₹720' : 'Availability & fare'}</strong><p>{stage === 4 ? 'Sample result · per person' : 'Checked after your confirmation'}</p></div></div>
          <p className="demo-note">Illustrative timings, seats, and fare. No live search or booking is made.</p>
        </aside>
      </div>
      <div className="demo-controls">
        <button className="demo-play" onClick={() => { if (ended) setPosition(0); setPlaying(value => !value) }} aria-label={playing ? 'Pause demo' : ended ? 'Replay demo' : 'Play demo'}>{playing ? <Pause size={18} /> : <Play size={18} />}<span>{playing ? 'Pause' : ended ? 'Replay' : 'Play demo'}</span></button>
        <button onClick={() => { setPlaying(false); setPosition(0) }} aria-label="Restart demo" title="Restart demo"><RotateCcw size={18} /></button>
        <input aria-label="Demo playback position" type="range" min="0" max={total} step="0.1" value={position} onChange={event => { setPlaying(false); setPosition(Number(event.target.value)) }} />
        <span className="demo-time">{clock(position)} / {clock(total)}</span>
        <button onClick={() => setMuted(value => !value)} disabled={!audioSupported || audioFailed} aria-label={muted ? 'Enable demo narration' : 'Mute demo narration'} title="Browser-generated demo voices" aria-pressed={!muted}>{muted ? <VolumeX size={19} /> : <Volume2 size={19} />}</button>
      </div>
      <div className="demo-audio-note">{!audioSupported || audioFailed ? 'Audio unavailable in this browser. Captions are always on.' : muted ? 'Captions on · Enable sound to hear the conversation.' : 'Sound on · Browser-generated voices for this simulation.'}</div>
    </div>
  </section>
}
