import React, { useState, useEffect, useRef } from 'react'
import { Phone, PhoneOff, Mic, MicOff, Volume2, Activity } from 'lucide-react'
import AudioWave from './AudioWave'

export default function WebRTCCall({ backendUrl, onCallStateChange }) {
  const [inCall, setInCall] = useState(false)
  const [callId, setCallId] = useState(null)
  const [currentState, setCurrentState] = useState('DISCONNECTED')
  const [transcript, setTranscript] = useState([])
  const [slots, setSlots] = useState({})
  const [useBrowserSpeech, setUseBrowserSpeech] = useState(true)
  const [isMuted, setIsMuted] = useState(false)
  const [agentSpeaking, setAgentSpeaking] = useState(false)

  const socketRef = useRef(null)
  const recognitionRef = useRef(null)
  const audioContextRef = useRef(null)
  const isListeningRef = useRef(false)
  const agentSpeakingRef = useRef(false)
  const isMutedRef = useRef(false)
  const activeAudioRef = useRef(null)

  // Sync state variables to refs to ensure safeStart/Stop always read fresh state
  useEffect(() => {
    agentSpeakingRef.current = agentSpeaking
  }, [agentSpeaking])

  useEffect(() => {
    isMutedRef.current = isMuted
  }, [isMuted])

  const safeStartRecognition = () => {
    if (recognitionRef.current && !isListeningRef.current && !isMutedRef.current) {
      try {
        recognitionRef.current.start()
      } catch (e) {
        // Defensive check: if it is already started, keep isListeningRef in sync
        if (e.message && (e.message.includes("already started") || e.name === "InvalidStateError")) {
          isListeningRef.current = true;
        } else {
          console.warn("safeStartRecognition failed:", e)
        }
      }
    }
  }

  const safeStopRecognition = () => {
    if (recognitionRef.current && isListeningRef.current) {
      try {
        // Use abort() instead of stop() to immediately discard current audio buffer
        // and prevent the microphone from picking up the agent's voice.
        recognitionRef.current.abort()
      } catch (e) {
        console.warn("safeStopRecognition failed:", e)
      }
    }
  }
  
  // Clean up on unmount
  useEffect(() => {
    return () => {
      endCall()
    }
  }, [])

  const startCall = async () => {
    // Check if configs on backend are using mock STT/TTS
    let mockStt = true
    let mockTts = true
    try {
      const res = await fetch(`${backendUrl}/dashboard/config`)
      if (res.ok) {
        const configData = await res.json()
        mockStt = configData.use_mock_stt
        mockTts = configData.use_mock_tts
        setUseBrowserSpeech(mockStt)
      }
    } catch (err) {
      console.warn("Could not fetch settings, defaulting browser speech to true.")
    }

    const uniqueId = `call-${Math.random().toString(36).substring(2, 9)}`
    setCallId(uniqueId)
    setInCall(true)
    setTranscript([])
    setSlots({})
    setCurrentState('CONNECTING')
    setAgentSpeaking(false)

    // Setup websocket
    const wsUrl = `${backendUrl.replace('http', 'ws')}/calls/ws/${uniqueId}`
    const ws = new WebSocket(wsUrl)
    socketRef.current = ws

    ws.onopen = () => {
      setCurrentState('GREET')
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      if (data.type === 'agent_response') {
        const text = data.text
        const state = data.state
        const newSlots = data.slots
        
        setCurrentState(state)
        setSlots(newSlots)
        
        // Dynamically adjust SpeechRecognition language based on dialect
        if (data.dialect && recognitionRef.current) {
          if (data.dialect === 'Hindi') {
            recognitionRef.current.lang = 'hi-IN'
          } else if (data.dialect === 'English') {
            recognitionRef.current.lang = 'en-US'
          } else {
            // Hinglish defaults to hi-IN which has excellent phonetics for mixed English/Hindi vocabulary
            recognitionRef.current.lang = 'hi-IN'
          }
          console.log("Speech recognition language updated dynamically:", recognitionRef.current.lang)
        }
        
        // Add to transcript list
        setTranscript(prev => [...prev, { sender: 'agent', text, timestamp: new Date() }])
        
        // Callback to parent component to update dashboard
        onCallStateChange({ callId: uniqueId, state, slots: newSlots, transcriptText: text, direction: 'outbound' })
        
        // Play TTS Response
        if (mockTts) {
          // Play via browser speechSynthesis
          setAgentSpeaking(true)
          agentSpeakingRef.current = true
          window.speechSynthesis.cancel() // clear any queue
          const utterance = new SpeechSynthesisUtterance(text)
          utterance.rate = 1.15
          
          // Try to select Hinglish/Hindi or English voice
          const voices = window.speechSynthesis.getVoices()
          const hindiVoice = voices.find(v => v.lang.includes('hi') || v.lang.includes('in'))
          if (hindiVoice) utterance.voice = hindiVoice
          
          utterance.onend = () => {
            agentSpeakingRef.current = false
            setAgentSpeaking(false)
            if (state === 'END') {
              endCall()
            } else {
              safeStartRecognition()
            }
          }
          utterance.onerror = () => {
            agentSpeakingRef.current = false
            setAgentSpeaking(false)
            if (state === 'END') {
              endCall()
            } else {
              safeStartRecognition()
            }
          }
          window.speechSynthesis.speak(utterance)
        } else if (data.audio) {
          // Play server base64 audio stream
          setAgentSpeaking(true)
          agentSpeakingRef.current = true
          const audio = new Audio("data:audio/mpeg;base64," + data.audio)
          activeAudioRef.current = audio
          audio.onended = () => {
            agentSpeakingRef.current = false
            setAgentSpeaking(false)
            if (state === 'END') {
              endCall()
            } else {
              safeStartRecognition()
            }
          }
          audio.play().catch(err => {
            console.error("Audio playback error:", err)
            agentSpeakingRef.current = false
            setAgentSpeaking(false)
            if (state === 'END') {
              endCall()
            }
          })
        }
      }
    }

    ws.onclose = () => {
      endCall()
    }

    ws.onerror = (err) => {
      console.error("WS connection error:", err)
      endCall()
    }

    // Setup Speech Recognition (STT) if in mock/browser mode
    if (mockStt) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition()
        recognitionRef.current = recognition
        recognition.continuous = false // turn off continuous to fire onend which lets us restart turn-by-turn
        recognition.interimResults = false
        recognition.lang = 'en-IN' // Start with en-IN (Indian English) which matches either English or Hindi keywords in language choice
        
        recognition.onstart = () => {
          isListeningRef.current = true
          console.log("Speech recognition started")
        }

        recognition.onspeechstart = () => {
          console.log("Mic detected speech sound onset.")
        }

        recognition.onresult = (event) => {
          const resultText = event.results[0][0].transcript
          
          // Double check interruption on result as well using conversational fillers/interrupt words
          const textClean = resultText.trim().toLowerCase()
          const words = textClean.split(/\s+/)
          const interruptWords = ["uh", "uhh", "um", "excuse", "wait", "stop", "hold on", "listen", "no", "hey", "hello", "sorry", "cancel", "bhai", "suno", "ek min", "ek minute"]
          const hasInterruptWord = interruptWords.some(w => textClean.includes(w))
          const isSignificantSpeech = words.length >= 2 || textClean.length >= 5
          
          if (agentSpeakingRef.current && (hasInterruptWord || isSignificantSpeech)) {
            console.log("Barge-in: valid speech interruption detected:", resultText)
            window.speechSynthesis.cancel()
            if (activeAudioRef.current) {
              try { activeAudioRef.current.pause() } catch(e){}
            }
            setAgentSpeaking(false)
          }

          setTranscript(prev => [...prev, { sender: 'user', text: resultText, timestamp: new Date() }])
          
          // Send transcript to FastAPI socket
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
              type: 'user_transcript',
              text: resultText
            }))
          }
          onCallStateChange({ callId: uniqueId, slots: {}, transcriptText: resultText, direction: 'inbound' })
        }

        recognition.onend = () => {
          isListeningRef.current = false
          // Restart loop if still in call and agent is not speaking
          setTimeout(() => {
            if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
              safeStartRecognition()
            }
          }, 300)
        }

        recognition.onerror = (event) => {
          console.warn("Speech recognition error:", event.error)
        }

        // Start listening
        safeStartRecognition()
      } else {
        alert("Web Speech API is not supported in this browser. Please use Chrome or Edge.")
      }
    } else {
      // In Real Audio Stream mode, we would access user mic and send PCM chunks over WS
      setupAudioStream(ws)
    }
  }

  const setupAudioStream = async (ws) => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 })
      audioContextRef.current = audioContext
      
      const source = audioContext.createMediaStreamSource(stream)
      const processor = audioContext.createScriptProcessor(4096, 1, 1)
      
      source.connect(processor)
      processor.connect(audioContext.destination)
      
      processor.onaudioprocess = (e) => {
        if (isMuted || agentSpeaking || ws.readyState !== WebSocket.OPEN) return
        
        const inputData = e.inputBuffer.getChannelData(0)
        // Convert to 16-bit PCM integer array
        const pcm16 = new Int16Array(inputData.length)
        for (let i = 0; i < inputData.length; i++) {
          pcm16[i] = Math.min(1, Math.max(-1, inputData[i])) * 0x7FFF
        }
        
        // Base64 encode and send
        const base64Audio = b64EncodeUnicode(pcm16.buffer)
        ws.send(JSON.stringify({
          event: "media",
          media: { payload: base64Audio }
        }))
      }
    } catch (err) {
      console.error("Error setting up browser mic capture stream:", err)
    }
  }

  const b64EncodeUnicode = (buffer) => {
    let binary = ''
    const bytes = new Uint8Array(buffer)
    const len = bytes.byteLength
    for (let i = 0; i < len; i++) {
      binary += String.fromCharCode(bytes[i])
    }
    return window.btoa(binary)
  }

  const endCall = () => {
    setInCall(false)
    setCurrentState('DISCONNECTED')
    
    if (socketRef.current) {
      if (socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.close()
      }
      socketRef.current = null
    }

    if (recognitionRef.current) {
      recognitionRef.current.onend = null
      try { recognitionRef.current.stop() } catch (e) {}
      recognitionRef.current = null
    }

    if (audioContextRef.current) {
      try { audioContextRef.current.close() } catch (e) {}
      audioContextRef.current = null
    }

    window.speechSynthesis.cancel()
    if (activeAudioRef.current) {
      try { activeAudioRef.current.pause() } catch (e){}
      activeAudioRef.current = null
    }
    setAgentSpeaking(false)
  }

  const toggleMute = () => {
    setIsMuted(!isMuted)
    if (recognitionRef.current) {
      if (!isMuted) {
        try { recognitionRef.current.stop() } catch (e) {}
      } else {
        try { recognitionRef.current.start() } catch (e) {}
      }
    }
  }

  return (
    <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Volume2 style={{ color: 'var(--color-primary)' }} />
          Voice Agent Terminal
        </h2>
        {inCall && (
          <span style={{
            background: 'rgba(99, 102, 241, 0.15)',
            border: '1px solid rgba(99, 102, 241, 0.3)',
            color: 'var(--color-primary)',
            padding: '4px 10px',
            borderRadius: '12px',
            fontSize: '0.75rem',
            fontWeight: 500,
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <Activity className="spinning-icon" size={12} />
            Live ID: {callId}
          </span>
        )}
      </div>

      <div style={{
        background: 'rgba(0, 0, 0, 0.2)',
        borderRadius: '12px',
        border: '1px solid var(--border-color)',
        height: '220px',
        overflowY: 'auto',
        padding: '16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px'
      }}>
        {transcript.length === 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)', textAlign: 'center', gap: '8px' }}>
            <Phone size={36} style={{ strokeWidth: 1 }} />
            <p style={{ fontSize: '0.85rem' }}>No active call. Dial in below to speak to the booking agent.</p>
          </div>
        ) : (
          transcript.map((t, idx) => (
            <div key={idx} style={{
              alignSelf: t.sender === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '80%',
              background: t.sender === 'user' ? 'rgba(99, 102, 241, 0.15)' : 'rgba(255, 255, 255, 0.05)',
              border: `1px solid ${t.sender === 'user' ? 'rgba(99, 102, 241, 0.25)' : 'var(--border-color)'}`,
              padding: '10px 14px',
              borderRadius: t.sender === 'user' ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
              fontSize: '0.9rem',
              lineHeight: 1.4
            }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginBottom: '4px', textTransform: 'capitalize' }}>
                {t.sender}
              </div>
              <div>{t.text}</div>
            </div>
          ))
        )}
      </div>

      {/* Visualizer wave while agent or user speaking */}
      <div style={{ height: '60px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <AudioWave isActive={inCall} isSilent={agentSpeaking || isMuted} />
      </div>

      <div style={{ display: 'flex', justifyContent: 'center', gap: '16px' }}>
        {!inCall ? (
          <button
            onClick={startCall}
            style={{
              padding: '12px 28px',
              borderRadius: '24px',
              border: 'none',
              background: 'linear-gradient(135deg, var(--color-success) 0%, #059669 100%)',
              color: 'white',
              fontWeight: 600,
              fontSize: '0.95rem',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              cursor: 'pointer',
              boxShadow: '0 4px 16px rgba(16, 185, 129, 0.35)',
              transition: 'var(--transition-smooth)'
            }}
          >
            <Phone size={18} />
            Start Voice Call
          </button>
        ) : (
          <>
            <button
              onClick={toggleMute}
              style={{
                width: '48px',
                height: '48px',
                borderRadius: '50%',
                border: '1px solid var(--border-color)',
                background: isMuted ? 'rgba(239, 68, 68, 0.15)' : 'rgba(255, 255, 255, 0.05)',
                color: isMuted ? 'var(--color-danger)' : 'var(--text-primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                transition: 'var(--transition-smooth)'
              }}
            >
              {isMuted ? <MicOff size={20} /> : <Mic size={20} />}
            </button>
            
            <button
              onClick={endCall}
              style={{
                padding: '12px 28px',
                borderRadius: '24px',
                border: 'none',
                background: 'linear-gradient(135deg, var(--color-danger) 0%, #b91c1c 100%)',
                color: 'white',
                fontWeight: 600,
                fontSize: '0.95rem',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                cursor: 'pointer',
                boxShadow: '0 4px 16px rgba(239, 68, 68, 0.35)',
                transition: 'var(--transition-smooth)'
              }}
            >
              <PhoneOff size={18} />
              End Call
            </button>
          </>
        )}
      </div>

      <div style={{
        textAlign: 'center',
        fontSize: '0.75rem',
        color: 'var(--text-secondary)',
        borderTop: '1px solid var(--border-color)',
        paddingTop: '12px',
        display: 'flex',
        justifyContent: 'space-around'
      }}>
        <span>Status: <strong style={{ color: inCall ? 'var(--color-success)' : 'var(--text-muted)' }}>{currentState}</strong></span>
        <span>Mode: <strong>{useBrowserSpeech ? "WebSpeech (Free)" : "WebRTC Stream"}</strong></span>
      </div>
    </div>
  )
}
