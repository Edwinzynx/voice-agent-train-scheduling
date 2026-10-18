// Mono PCM16 in 100 ms frames. The AudioContext is explicitly created at 16 kHz.
class PcmCapture extends AudioWorkletProcessor {
  constructor() {
    super()
    this.samples = new Int16Array(1600)
    this.position = 0
  }
  process(inputs) {
    const input = inputs[0]?.[0]
    if (!input) return true
    for (const value of input) {
      const sample = Math.max(-1, Math.min(1, value))
      this.samples[this.position++] = sample < 0 ? sample * 32768 : sample * 32767
      if (this.position === this.samples.length) {
        this.port.postMessage(this.samples.buffer, [this.samples.buffer])
        this.samples = new Int16Array(1600)
        this.position = 0
      }
    }
    return true
  }
}
registerProcessor('pcm-capture', PcmCapture)
