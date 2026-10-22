import React, { useEffect, useRef, useState } from 'react'
import { ArrowRight, MessageSquare, Mic, MicOff, PhoneOff, Send, Train, Volume2 } from 'lucide-react'
import useVoiceCall from './useVoiceCall'
import TrainOptions from './TrainOptions'
import './VoicePlayground.css'

const queries = [
  'Find trains from Delhi to Chandigarh tomorrow',
  'Find trains from Mumbai to Pune tomorrow',
  'Check seat availability from Chennai to Bangalore tomorrow',
]

export default function WebRTCCall({ backendUrl, onCallStateChange }) {
  const call = useVoiceCall(backendUrl, onCallStateChange)
  const { inCall, currentState, transcript, isMuted, agentSpeaking, error, mode, isProcessing,
    environment, startCall, endCall, toggleMute, selectTrain, sendText } = call
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
          <span className="playground-eyebrow">MEET YOUR RAILWAY VOICE ASSISTANT</span>
          <div className={`voice-call-orb ${inCall && mode === 'voice' ? 'call-active' : ''}`}><Mic size={36} /></div>
          <h2>{inCall ? mode === 'voice' ? 'Your conversation is live' : 'Your chat is connected' : 'Your next journey starts with a hello.'}</h2>
          <p>Speak naturally. LocoVoice helps you find trains, choose a class, and check seat availability.</p>
          <div className="voice-languages">English <span>·</span> हिंदी <span>·</span> Hinglish</div>
          <div className="session-actions voice-primary-actions">
            {!inCall ? <>
              <button className="playground-button primary voice-start-button" disabled={!canSend} onClick={() => startCall({ mode: 'voice' })}><Mic size={24} /> Start voice call <ArrowRight size={20} /></button>
              <p className="voice-permission-note">Allow microphone access when prompted, then say hello.</p>
              <button className="voice-text-alternative" disabled={!canSend} onClick={() => { startCall({ mode: 'text' }); input.current?.focus() }}><MessageSquare size={14} /> Prefer typing? Start a chat</button>
            </> : <>
              <div className="voice-live-status" role="status">{status}</div>
              {mode === 'voice' && <button className="playground-button" aria-pressed={isMuted} onClick={toggleMute}>{isMuted ? <MicOff size={17} /> : <Mic size={17} />}{isMuted ? 'Unmute' : 'Mute'}</button>}
              <button className="playground-button end-session" onClick={endCall}><PhoneOff size={17} /> End {mode === 'voice' ? 'call' : 'chat'}</button>
            </>}
          </div>
          <details className="voice-query-examples"><summary>Need an idea? Try asking…</summary><div className="query-list">
            {queries.map(query => <div key={query} className="voice-example">“{query}”</div>)}
          </div></details>
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
            {!transcript.length && <div className="conversation-welcome"><div className="welcome-icon"><Volume2 size={30} /></div><h3>{inCall ? 'LocoVoice is getting ready' : 'Your conversation appears here'}</h3><p>{inCall ? 'Follow the agent’s replies here as you plan your journey.' : 'Start a voice call, then tell us where you want to go. You’ll see your words, the agent’s replies, and train options here.'}</p><span>Speak · Confirm your journey · Explore trains</span></div>}
            {transcript.map((message, index) => <React.Fragment key={index}>
              <div className={`bubble ${message.sender}`}><span className="message-speaker">{message.sender === 'agent' ? 'LocoVoice' : 'You'}</span>{message.text}</div>
              {index === latestAgentIndex && message.availableTrains?.length > 0 && <TrainOptions
                trains={message.availableTrains} slots={message.slots} disabled={!inCall || !canSend} onSelect={selectTrain} />}
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
