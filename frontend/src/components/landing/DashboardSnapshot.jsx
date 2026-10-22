import React, { useEffect, useRef, useState } from 'react'
import { ArrowRight, Check, MessageSquare, Pause, Play, RotateCcw, Train, Volume2, VolumeX } from 'lucide-react'
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
  const [muted, setMuted] = useState(false)
  const [audioFailed, setAudioFailed] = useState(false)
  const music = useRef(null)
  const feed = useRef(null)
  let boundary = 0
  const found = scenes.findIndex(scene => { boundary += scene[2]; return position < boundary })
  const index = found < 0 ? scenes.length - 1 : found
  const [speaker, stage, duration, text] = scenes[index]
  const elapsed = position - (boundary - duration)
  const visibleCharacters = position === 0 && !playing ? text.length : Math.max(0, Math.ceil((elapsed - .5) / (duration * .65) * text.length))
  const typing = visibleCharacters < text.length
  const ended = position >= total

  useEffect(() => {
    if (!playing) return
    let previous = performance.now()
    const timer = window.setInterval(() => {
      const now = performance.now()
      const delta = (now - previous) / 1000
      previous = now
      setPosition(current => Math.min(current + delta, total))
    }, 100)
    return () => window.clearInterval(timer)
  }, [playing])
  useEffect(() => { if (ended) setPlaying(false) }, [ended])
  useEffect(() => {
    if (!playing || muted || ended) music.current?.pause()
  }, [playing, muted, ended])
  useEffect(() => {
    feed.current?.scrollTo({ top: feed.current.scrollHeight, behavior: 'instant' })
  }, [index, visibleCharacters])
  useEffect(() => {
    const pauseWhenHidden = () => { if (document.hidden) setPlaying(false) }
    document.addEventListener('visibilitychange', pauseWhenHidden)
    return () => document.removeEventListener('visibilitychange', pauseWhenHidden)
  }, [])

  const playMusic = () => {
    if (!music.current || audioFailed) return
    music.current.volume = .22
    music.current.play().catch(() => { setAudioFailed(true); setMuted(true) })
  }
  const togglePlayback = () => {
    if (ended) { setPosition(0); if (music.current) music.current.currentTime = 0 }
    if (!playing && !muted) playMusic()
    setPlaying(value => !value)
  }
  const restart = () => {
    setPlaying(false)
    setPosition(0)
    if (music.current) { music.current.pause(); music.current.currentTime = 0 }
  }

  return <section id="dashboard-demo" className="landing-section conversation-demo">
    <div className="demo-eyebrow">A CONVERSATION, FROM START TO FINISH</div>
    <h2 className="landing-section-title">Ask. Listen. Find your train.</h2>
    <p className="landing-section-subtitle">Follow a voice conversation through animated chat, from the first question to train times, seats, and fares.</p>
    <div className={`demo-player ${playing ? 'is-playing' : ''}`}>
      <div className="demo-topbar"><strong>● &nbsp; LocoVoice in action</strong><span>SIMULATED DEMO · SAMPLE DATA</span></div>
      <div className="demo-stage">
        <div className="demo-conversation">
          <div className="demo-scene-label">0{index + 1} / 08 <span>{['Tell us your journey', 'Confirm the route', 'Explore a train', 'Choose your class', 'Get the details'][stage]}</span></div>
          <div className="demo-chat-heading"><div className="demo-chat-avatar"><Train size={22} /></div><div><strong>LocoVoice</strong><span>{playing ? speaker === 'Passenger' ? 'Listening to the passenger…' : typing ? 'Preparing a reply…' : 'Reply delivered' : ended ? 'Journey details ready' : 'A preview of your next conversation'}</span></div><MessageSquare size={19} /></div>
          <div className="demo-chat-feed" ref={feed} aria-label="Simulated conversation">
            {scenes.slice(0, index + 1).map(([name, , , message], messageIndex) => {
              const current = messageIndex === index
              const content = current ? message.slice(0, visibleCharacters) : message
              return <div key={messageIndex} className={`demo-chat-message ${name === 'Passenger' ? 'passenger' : 'agent'}`}>
                <span className="demo-message-label">{name === 'Passenger' ? 'YOU' : 'LOCOVOICE'}</span>
                <div className="demo-chat-bubble" aria-hidden="true">{content || <span className="demo-typing"><i /><i /><i /></span>}{current && typing && content && <span className="demo-caret" />}</div>
                <span className="demo-sr-only">{message}</span>
              </div>
            })}
          </div>
          <div className="demo-chat-status"><span className={playing ? 'demo-pulse' : ''} />{ended ? 'Train found. Details checked. Ready for your journey.' : 'Voice experience, illustrated in chat'}</div>
          <span className="demo-sr-only" aria-live="polite" aria-atomic="true">{speaker}: {text}</span>
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
        <button className="demo-play" onClick={togglePlayback} aria-label={playing ? 'Pause demo' : ended ? 'Replay demo' : 'Play demo'}>{playing ? <Pause size={18} /> : <Play size={18} />}<span>{playing ? 'Pause' : ended ? 'Replay' : 'Play demo'}</span></button>
        <button onClick={restart} aria-label="Restart demo" title="Restart demo"><RotateCcw size={18} /></button>
        <input aria-label="Demo playback position" type="range" min="0" max={total} step="0.1" value={position} onChange={event => { setPlaying(false); setPosition(Number(event.target.value)); if (music.current) music.current.currentTime = Number(event.target.value) % 24 }} />
        <span className="demo-time">{clock(position)} / {clock(total)}</span>
        <button onClick={() => { if (muted && playing) playMusic(); setMuted(value => !value) }} disabled={audioFailed} aria-label={muted ? 'Enable background music' : 'Mute background music'} title="Gentle instrumental background music" aria-pressed={!muted}>{muted ? <VolumeX size={19} /> : <Volume2 size={19} />}</button>
      </div>
      <div className="demo-audio-note">{audioFailed ? 'Music unavailable. The chat walkthrough is still ready to play.' : muted ? 'Music muted · Animated conversation, no spoken audio.' : 'Soft instrumental music · Animated conversation, no spoken audio.'}</div>
      <audio ref={music} src={`${import.meta.env.BASE_URL}demo-ambient.wav`} loop preload="none" onError={() => { setAudioFailed(true); setMuted(true) }} />
    </div>
  </section>
}
