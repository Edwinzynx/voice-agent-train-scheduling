import { useEffect, useRef, useState } from 'react'

export default function useVoiceCall(backendUrl, onCallStateChange) {
  const [inCall, setInCall] = useState(false)
  const [callId, setCallId] = useState(null)
  const [currentState, setCurrentState] = useState('DISCONNECTED')
  const [transcript, setTranscript] = useState([])
  const [slots, setSlots] = useState({})
  const [isMuted, setIsMuted] = useState(false)
  const [agentSpeaking, setAgentSpeaking] = useState(false)
  const [error, setError] = useState('')
  const [mode, setMode] = useState('text')
  const [isProcessing, setIsProcessing] = useState(false)
  const [lastLatency, setLastLatency] = useState(null)
  const [environment, setEnvironment] = useState('')
  const socketRef = useRef(null)
  const resources = useRef({})
  const generation = useRef(0)
  const muted = useRef(false)
  const busy = useRef(true)
  const pending = useRef(true)
  const callback = useRef(onCallStateChange)
  callback.current = onCallStateChange

  const endCall = () => {
    generation.current++
    const r = resources.current
    resources.current = {}
    r.controller?.abort()
    clearTimeout(r.connectTimer)
    if (r.recognition) {
      r.recognition.onend = null
      r.recognition.onresult = null
      r.recognition.onerror = null
      try { r.recognition.abort() } catch { /* Recognition is already stopped. */ }
    }
    r.stream?.getTracks().forEach(track => track.stop())
    if (r.processor) {
      r.processor.port.onmessage = null
      r.processor.disconnect()
    }
    r.source?.disconnect()
    if (r.context?.state !== 'closed') r.context?.close().catch(() => {})
    if (r.audio) {
      r.audio.onended = null
      r.audio.onerror = null
      r.audio.pause()
    }
    window.speechSynthesis?.cancel()
    const ws = socketRef.current
    socketRef.current = null
    if (ws) {
      ws.onclose = null
      ws.onerror = null
      ws.onmessage = null
      if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ type: 'stop' }))
      ws.close()
    }
    busy.current = true
    pending.current = true
    setInCall(false)
    setAgentSpeaking(false)
    setIsProcessing(false)
    setCurrentState('DISCONNECTED')
    callback.current?.({ callId: null, state: 'DISCONNECTED', slots: {} })
  }

  useEffect(() => () => endCall(), [])

  const startCall = async ({ mode: requestedMode = 'voice', initialText = '' } = {}) => {
    endCall()
    const id = generation.current
    const current = () => generation.current === id
    const r = { controller: new AbortController(), playback: 0, speechEpoch: 0, initialText }
    resources.current = r
    setError('')
    setInCall(true)
    setCurrentState('CONNECTING')
    setMode(requestedMode)
    setIsProcessing(true)
    setLastLatency(null)
    setTranscript([])
    setSlots({})
    setIsMuted(false)
    muted.current = false
    busy.current = true
    const interruptPlayback = () => {
      r.playback++
      if (r.audio) {
        r.audio.onended = null
        r.audio.onerror = null
        r.audio.pause()
      }
      window.speechSynthesis?.cancel()
      setAgentSpeaking(false)
      busy.current = pending.current
    }
    const resumeListening = () => {
      if (!current()) return
      busy.current = false
      setAgentSpeaking(false)
      if (r.initialText) {
        const text = r.initialText
        r.initialText = ''
        sendText(text)
        return
      }
      if (!muted.current && r.recognition) {
        try { r.recognition.start() } catch { /* Already listening. */ }
      }
    }
    const speak = (data) => {
      busy.current = true
      r.recognition?.abort()
      const playback = ++r.playback
      const playing = () => current() && r.playback === playback
      const finish = () => data.state === 'END' ? endCall() : resumeListening()
      if (requestedMode === 'text') { finish(); return }
      setAgentSpeaking(true)
      if (r.browserSpeech) {
        const utterance = new SpeechSynthesisUtterance(data.text)
        utterance.lang = data.state === 'LANGUAGE' || data.dialect === 'English' ? 'en-IN' : 'hi-IN'
        utterance.onend = () => playing() && finish()
        utterance.onerror = () => playing() && finish()
        window.speechSynthesis.speak(utterance)
        return
      }
      const segments = [...(data.audio_segments || [])]
      if (!segments.length) {
        setError(data.audio_error || 'No spoken audio was returned. Read the response below and keep speaking.')
        finish()
        return
      }
      const playNext = () => {
        if (!playing()) return
        if (!segments.length) { finish(); return }
        const audio = new Audio(`data:${data.audio_mime || 'audio/wav'};base64,${segments.shift()}`)
        r.audio = audio
        audio.onended = playNext
        const failed = () => {
          if (!playing()) return
          audio.onended = null
          audio.onerror = null
          setError('Audio playback failed. The response is displayed below; you can keep speaking.')
          finish()
        }
        audio.onerror = failed
        audio.play().catch(failed)
      }
      playNext()
    }
    try {
      r.connectTimer = setTimeout(() => r.controller.abort(), 75000)
      const response = await fetch(`${backendUrl}/calls/capabilities`, { signal: r.controller.signal })
      if (!response.ok) throw new Error('The voice backend is unavailable. Please try again.')
      const config = await response.json()
      clearTimeout(r.connectTimer)
      if (!current()) return
      setEnvironment(config.environment)
      if (requestedMode === 'text' ? !(config.text_ready ?? config.ready) : !config.ready) throw new Error(requestedMode === 'text' ? config.text_message || config.message : config.message)
      r.browserSpeech = config.speech_provider === 'browser'
      if (requestedMode === 'voice' && !r.browserSpeech) {
        if (!navigator.mediaDevices?.getUserMedia || !window.AudioWorkletNode) throw new Error('This browser cannot stream microphone audio. Please use a current browser over HTTPS.')
        const stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true, channelCount: 1 } })
        if (!current()) { stream.getTracks().forEach(track => track.stop()); return }
        r.stream = stream
        r.context = new AudioContext({ sampleRate: 16000 })
        await r.context.resume()
        if (!current()) return
        if (r.context.sampleRate !== 16000) throw new Error('This browser does not support the required microphone sample rate.')
        await r.context.audioWorklet.addModule('/pcm-worklet.js')
        if (!current()) return
        r.source = r.context.createMediaStreamSource(stream)
        r.processor = new AudioWorkletNode(r.context, 'pcm-capture')
        r.source.connect(r.processor)
        r.processor.connect(r.context.destination)
        r.processor.port.onmessage = ({ data }) => {
          const ws = socketRef.current
          // Keep sending echo-cancelled microphone audio during playback and processing.
          // Sarvam's speech-start event interrupts output before the final transcript.
          if (!current() || muted.current || ws?.readyState !== WebSocket.OPEN) return
          if (ws.bufferedAmount > 64000) {
            setError('The connection is too slow for live audio. Please reconnect.')
            endCall()
            return
          }
          let binary = ''
          for (const byte of new Uint8Array(data)) binary += String.fromCharCode(byte)
          ws.send(JSON.stringify({ type: 'audio', audio: btoa(binary) }))
        }
      } else if (requestedMode === 'voice') {
        const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition
        if (!Recognition || !window.speechSynthesis) throw new Error('Browser speech debugging requires Chrome or Edge.')
        r.recognition = new Recognition()
        r.recognition.lang = 'en-IN'
        r.recognition.onresult = event => {
          if (!current() || muted.current || busy.current) return
          const text = event.results[0][0].transcript
          busy.current = true
          pending.current = true
          setIsProcessing(true)
          setTranscript(prev => [...prev, { sender: 'user', text, timestamp: new Date() }])
          socketRef.current?.send(JSON.stringify({ type: 'user_transcript', text }))
        }
        r.recognition.onend = () => { if (current() && !busy.current) resumeListening() }
        r.recognition.onerror = event => {
          if (['not-allowed', 'audio-capture', 'service-not-allowed'].includes(event.error)) {
            setError(`Microphone recognition failed: ${event.error}`)
            endCall()
          }
        }
      }
      if (!current()) return
      const uniqueId = `call-${crypto.randomUUID()}`
      setCallId(uniqueId)
      const url = new URL(`${backendUrl}/calls/ws/${uniqueId}`)
      url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
      const ws = new WebSocket(url)
      socketRef.current = ws
      r.connectTimer = setTimeout(() => {
        if (current()) { setError('The voice connection timed out. Please try again.'); endCall() }
      }, 45000)
      ws.onopen = () => ws.send(JSON.stringify({ type: 'start', mode: requestedMode, sample_rate: 16000, encoding: 'linear16' }))
      ws.onmessage = event => {
        if (!current()) return
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'ready') clearTimeout(r.connectTimer)
          if (data.type === 'speech_started') {
            r.speechEpoch = Math.max(r.speechEpoch, data.speech_epoch || 0)
            interruptPlayback()
          }
          if (data.type === 'processing') { busy.current = true; pending.current = true; setIsProcessing(true) }
          if (data.type === 'error') {
            setError(data.message)
            pending.current = false
            setIsProcessing(false)
            if (data.fatal) endCall()
            else resumeListening()
          }
          if (data.type === 'user_transcript') {
            interruptPlayback()
            pending.current = true
            setIsProcessing(true)
            setTranscript(prev => [...prev, { sender: 'user', text: data.text, timestamp: new Date() }])
          }
          if (data.type === 'agent_response') {
            const interrupted = data.interrupted || (data.speech_epoch ?? r.speechEpoch) < r.speechEpoch
            if (!interrupted) {
              pending.current = false
              setIsProcessing(false)
            }
            if (data.latency_ms > 0) setLastLatency(Math.round(data.latency_ms))
            setCurrentState(data.state)
            setSlots(data.slots || {})
            setTranscript(prev => [...prev, { sender: 'agent', text: data.text, timestamp: new Date(), availableTrains: data.available_trains || [], lastActionResult: data.last_action_result, slots: data.slots, state: data.state }])
            callback.current?.({ callId: uniqueId, state: data.state, slots: data.slots, transcriptText: data.text, direction: 'outbound' })
            if (r.recognition) r.recognition.lang = data.dialect === 'English' ? 'en-IN' : 'hi-IN'
            if (!interrupted) speak(data)
          }
        } catch {
          setError('The voice server sent an invalid response. Please reconnect.')
          endCall()
        }
      }
      ws.onerror = () => { if (current()) { setError('Could not connect to the voice service.'); endCall() } }
      ws.onclose = () => { if (current()) { setError('The call has disconnected. Start a new call to continue.'); endCall() } }
    } catch (err) {
      if (!current()) return
      setError(err.name === 'NotAllowedError' ? 'Microphone permission is required. Allow access and try again.' : err.name === 'AbortError' ? 'The backend did not respond in time. Please try again.' : err.message)
      endCall()
    }
  }

  const toggleMute = () => {
    muted.current = !muted.current
    setIsMuted(muted.current)
    resources.current.stream?.getAudioTracks().forEach(track => { track.enabled = !muted.current })
    if (muted.current) resources.current.recognition?.abort()
    else if (!busy.current) { try { resources.current.recognition?.start() } catch {} }
  }

  const selectTrain = (train, classCode) => {
    if (socketRef.current?.readyState !== WebSocket.OPEN || pending.current) return
    prepareInput()
    setTranscript(prev => [...prev, { sender: 'user', text: `Selected ${train.name} (${train.no}) - ${classCode}`, timestamp: new Date() }])
    socketRef.current.send(JSON.stringify({ type: 'select_train', train_no: String(train.no), class_code: classCode }))
  }

  const prepareInput = () => {
    const r = resources.current
    r.playback++
    if (r.audio) { r.audio.onended = null; r.audio.onerror = null }
    r.audio?.pause()
    r.recognition?.abort()
    window.speechSynthesis?.cancel()
    setAgentSpeaking(false)
    setError('')
    setIsProcessing(true)
    busy.current = true
    pending.current = true
  }

  const sendText = (value) => {
    const text = value.trim().slice(0, 2000)
    if (!text) return false
    if (socketRef.current?.readyState !== WebSocket.OPEN) return false
    if (pending.current) return false
    prepareInput()
    setTranscript(prev => [...prev, { sender: 'user', text, timestamp: new Date() }])
    socketRef.current.send(JSON.stringify({ type: 'user_transcript', text }))
    return true
  }
  return { inCall, callId, currentState, transcript, slots, isMuted, agentSpeaking, error, mode, isProcessing, lastLatency, environment, startCall, endCall, toggleMute, selectTrain, sendText }
}
