import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import vm from 'node:vm'

test('production barge-in stops playback and queued audio while the microphone stays active', async () => {
  const sockets = [], audios = [], processors = []
  const track = { enabled: true, stop() {} }
  class Socket {
    static OPEN = 1
    constructor() { this.readyState = 1; this.bufferedAmount = 0; this.sent = []; sockets.push(this) }
    send(raw) { this.sent.push(JSON.parse(raw)) }
    close() { this.readyState = 3 }
    receive(data) { this.onmessage({ data: JSON.stringify(data) }) }
  }
  const context = {
    useState: value => [value, () => {}], useRef: value => ({ current: value }), useEffect() {},
    AbortController, URL, WebSocket: Socket, Date, Uint8Array, setTimeout, clearTimeout,
    crypto: { randomUUID: () => 'voice-test' }, btoa: value => Buffer.from(value, 'binary').toString('base64'),
    fetch: async () => ({ ok: true, json: async () => ({ ready: true, speech_provider: 'sarvam', environment: 'production' }) }),
    navigator: { mediaDevices: { getUserMedia: async () => ({ getTracks: () => [track], getAudioTracks: () => [track] }) } },
    window: { speechSynthesis: { cancel() {} }, AudioWorkletNode: true },
    Audio: class {
      constructor() { this.paused = false; audios.push(this) }
      play() { return Promise.resolve() }
      pause() { this.paused = true }
    },
    AudioContext: class {
      sampleRate = 16000
      audioWorklet = { addModule: async () => {} }
      resume() { return Promise.resolve() }
      close() { return Promise.resolve() }
      createMediaStreamSource() { return { connect() {}, disconnect() {} } }
    },
    AudioWorkletNode: class {
      constructor() { this.port = {}; processors.push(this) }
      connect() {}
      disconnect() {}
    },
  }
  const source = readFileSync(new URL('../src/components/useVoiceCall.js', import.meta.url), 'utf8')
    .replace(/^import .*\n/, '').replace('export default function', 'function')
  vm.runInNewContext(source + '\nglobalThis.hook = useVoiceCall;', context)
  const call = context.hook('https://example.com')
  try {
    await call.startCall({ mode: 'voice' })
    const ws = sockets[0]
    ws.onopen()
    ws.receive({ type: 'ready' })
    ws.receive({ type: 'agent_response', state: 'LANGUAGE', text: 'Hello', speech_epoch: 0, audio_segments: ['first', 'second'] })
    assert.equal(audios.length, 1)
    const staleEnded = audios[0].onended
    const sendMic = () => processors[0].port.onmessage({ data: new Int16Array(1600).buffer })
    sendMic()
    assert.equal(ws.sent.at(-1).type, 'audio')
    ws.receive({ type: 'speech_started', speech_epoch: 1 })
    assert.equal(audios[0].paused, true)
    staleEnded()
    assert.equal(audios.length, 1, 'queued audio must not restart')
    ws.receive({ type: 'agent_response', state: 'END', text: 'Old reply', speech_epoch: 0, audio_segments: ['late'] })
    assert.equal(audios.length, 1)
    assert.equal(ws.readyState, Socket.OPEN, 'stale END must not close the call')
    ws.receive({ type: 'processing' })
    sendMic()
    assert.equal(ws.sent.filter(e => e.type === 'audio').length, 2)
    call.toggleMute()
    sendMic()
    assert.equal(ws.sent.filter(e => e.type === 'audio').length, 2)
    call.toggleMute()
    ws.receive({ type: 'agent_response', state: 'INTENT', text: 'New reply', speech_epoch: 1, audio_segments: ['new'] })
    assert.equal(audios.length, 2)
    ws.receive({ type: 'speech_started', speech_epoch: 2 })
    ws.receive({ type: 'input_ignored', processing: false })
    assert.equal(call.sendText('Hindi'), true, 'ignored hesitation must not leave input locked')
  } finally {
    call.endCall()
  }
  assert.equal(audios.at(-1).paused, true)
})

test('microphone worklet produces exact 100 ms PCM16 frames without monitoring audio', () => {
  let Processor
  const frames = []
  vm.runInNewContext(readFileSync(new URL('../public/pcm-worklet.js', import.meta.url), 'utf8'), {
    AudioWorkletProcessor: class { constructor() { this.port = { postMessage: buffer => frames.push(new Int16Array(buffer)) } } },
    registerProcessor: (name, processor) => { assert.equal(name, 'pcm-capture'); Processor = processor },
    Int16Array,
  })
  const processor = new Processor()
  const input = new Float32Array(128).fill(0.5)
  input[0] = -2
  input[1] = 2
  for (let i = 0; i < 12; i++) assert.equal(processor.process([[input]]), true)
  assert.equal(frames.length, 0)
  processor.process([[input]])
  assert.equal(frames.length, 1)
  assert.equal(frames[0].length, 1600)
  assert.equal(frames[0][0], -32768)
  assert.equal(frames[0][1], 32767)
  assert.equal(frames[0][2], 16383)
  assert.equal(processor.position, 64)
  assert.equal(processor.process([]), true)
})
