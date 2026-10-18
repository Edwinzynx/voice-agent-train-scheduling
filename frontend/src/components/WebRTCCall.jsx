import React, { useEffect, useRef, useState } from 'react'
import { ArrowRight, Clock, MessageSquare, Mic, MicOff, PhoneOff, Send, Train, Volume2 } from 'lucide-react'
import useVoiceCall from './useVoiceCall'
import './VoicePlayground.css'

const queries = [
  'Find trains from Delhi to Chandigarh tomorrow',
  'Find trains from Mumbai to Pune tomorrow',
  'Check seat availability from Chennai to Bangalore tomorrow',
]

function displayDate(value) {
  if (!value) return 'Date not selected'
  const date = /^\d{4}-\d{2}-\d{2}$/.test(value) ? new Date(`${value}T12:00:00+05:30`) : null
  return date && !Number.isNaN(date.getTime())
    ? date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'Asia/Kolkata' }) : value
}

export default function WebRTCCall({ backendUrl, onCallStateChange }) {
  const call = useVoiceCall(backendUrl, onCallStateChange)
  const { inCall, currentState, transcript, isMuted, agentSpeaking, error, mode, isProcessing,
    lastLatency, environment, startCall, endCall, toggleMute, selectTrain, sendText } = call
  const [draft, setDraft] = useState('')
  const feed = useRef(null)
  const input = useRef(null)
  const latestAgentIndex = transcript.findLastIndex(message => message.sender === 'agent')
  const canSend = !isProcessing && currentState !== 'CONNECTING'
  const status = currentState === 'CONNECTING' ? 'Connecting…' : !inCall ? 'Ready when you are'
    : isProcessing ? 'Thinking…' : agentSpeaking ? 'Speaking…' : mode === 'text' ? 'Chat connected' : isMuted ? 'Microphone muted' : 'Listening…'

  useEffect(() => {
    feed.current?.scrollTo({ top: feed.current.scrollHeight, behavior: 'smooth' })
  }, [transcript, isProcessing])

  const submit = (value) => {
    const text = value.trim()
    if (!text || !canSend) return
    if (!inCall) { startCall({ mode: 'text', initialText: text }); setDraft('') }
    else if (sendText(text)) setDraft('')
  }

  return (
    <div className="voice-playground">
      <div className="playground-context">
        <div className="glass-panel query-panel">
          <span className="playground-eyebrow">YOUR JOURNEY STARTS HERE</span>
          <h2><MessageSquare size={22} /> Train queries playground</h2>
          <p>Find a train, choose your class, and check availability. Type a message or speak in English, Hindi, or Hinglish.</p>
          <div className="query-list">
            {queries.map(query => <button key={query} className="preset-pill query-shortcut" disabled={!canSend} onClick={() => submit(query)}>
              <span>{query}</span><ArrowRight size={18} />
            </button>)}
          </div>
          <p className="query-hint">Each query goes to the connected backend. Review the route and date before confirming.</p>
          <div className="session-actions">
            {!inCall ? <>
              <button className="playground-button primary" onClick={() => startCall({ mode: 'voice' })}><Mic size={17} /> Start voice call</button>
              <button className="playground-button" onClick={() => startCall({ mode: 'text' })}><MessageSquare size={17} /> Start chat</button>
            </> : <>
              {mode === 'voice' && <button className="playground-button" aria-pressed={isMuted} onClick={toggleMute}>{isMuted ? <MicOff size={17} /> : <Mic size={17} />}{isMuted ? 'Unmute' : 'Mute'}</button>}
              <button className="playground-button end-session" onClick={endCall}><PhoneOff size={17} /> End {mode === 'voice' ? 'call' : 'chat'}</button>
            </>}
          </div>
          {lastLatency !== null && <div className="processing-metric"><Clock size={16} /><span>Last agent processing time <strong>{lastLatency.toLocaleString()} ms</strong></span></div>}
        </div>
        <div className="service-note"><Train size={18} /><p>Train search and seat checks are available. Booking, cancellations, PNR lookup, and live running status are not connected.</p></div>
        {environment === 'development' && <p className="debug-note">Local debugging backend · responses may use the local parser.</p>}
      </div>

      <div className="phone-mockup live-phone">
        <div className="phone-screen">
          <div className="phone-header">
            <div className="agent-avatar"><Volume2 size={19} /></div>
            <div><h3>LocoVoice AI</h3><span className={`connection-status ${inCall ? 'connected' : ''}`} role="status"><i />{status}</span></div>
            <span className="session-mode">{inCall ? mode === 'text' ? 'CHAT' : 'VOICE' : 'SANDBOX'}</span>
          </div>
          <div className="phone-body" ref={feed} role="log" aria-label="Conversation" aria-live="polite">
            {!transcript.length && <div className="conversation-welcome"><div className="welcome-icon"><Train size={30} /></div><h3>Where are you headed?</h3><p>Choose a query to get started, or tell LocoVoice about your journey.</p><span>English · हिंदी · Hinglish</span></div>}
            {transcript.map((message, index) => <React.Fragment key={index}>
              <div className={`bubble ${message.sender}`}><span className="message-speaker">{message.sender === 'agent' ? 'LocoVoice' : 'You'}</span>{message.text}</div>
              {index === latestAgentIndex && message.availableTrains?.length > 0 && <div className="train-options" aria-label="Train options">
                <span className="train-options-title">Choose a train & class to check seats</span>
                {message.availableTrains.flatMap(train => (train.classes || []).map(classCode => ({ train, classCode }))).slice(0, 4).map(({ train, classCode }, option) => {
                  const info = train.class_details?.[classCode] || {}
                  return <button className="train-option" key={`${train.no}-${classCode}`} disabled={!inCall || !canSend} onClick={() => selectTrain(train, classCode)}>
                    <span className="train-option-heading"><span>Option {option + 1} · {train.no}</span><strong>{classCode}</strong></span>
                    <strong>{train.name || train.no}</strong>
                    <span>{train.src || message.slots?.source || 'Origin unavailable'} → {train.dst || message.slots?.destination || 'Destination unavailable'}</span>
                    <span>{displayDate(message.slots?.date)}</span>
                    <span>{train.dep || 'Time unavailable'} → {train.arr || 'Time unavailable'}</span>
                    <span className="train-availability">{info.status || 'Availability not returned'}{info.seats != null ? ` · ${info.seats} seats` : ''}{info.price != null ? ` · ₹${info.price}` : ''}</span>
                    <span className="train-option-action">Select & review <ArrowRight size={14} /></span>
                  </button>
                })}
              </div>}
            </React.Fragment>)}
            {isProcessing && <div className="bubble agent typing-indicator" aria-label="Agent is responding"><i /><i /><i /></div>}
          </div>
          {error && <div className="conversation-error" role="alert">{error}</div>}
          {inCall && currentState === 'LANGUAGE' && <div className="quick-replies" aria-label="Choose language">{['English', 'Hindi', 'Hinglish'].map(language => <button className="preset-pill" key={language} disabled={!canSend} onClick={() => sendText(language)}>{language}</button>)}</div>}
          {inCall && currentState === 'CONFIRM' && <div className="quick-replies" aria-label="Confirm journey"><button className="preset-pill" disabled={!canSend} onClick={() => sendText('Yes')}>Yes, confirm</button><button className="preset-pill" disabled={!canSend} onClick={() => { sendText('No'); input.current?.focus() }}>Change details</button></div>}
          <form className="phone-footer" onSubmit={event => { event.preventDefault(); submit(draft) }}>
            <input ref={input} aria-label="Message LocoVoice" placeholder={inCall ? 'Type your message…' : 'Where would you like to go?'} maxLength={2000} value={draft} onChange={event => setDraft(event.target.value)} />
            <button className="composer-send" type="submit" aria-label="Send message" disabled={!draft.trim() || !canSend}><Send size={16} /></button>
          </form>
        </div>
      </div>
    </div>
  )
}
