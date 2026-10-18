import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import vm from 'node:vm'

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
