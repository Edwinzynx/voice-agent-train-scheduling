import test from 'node:test'
import assert from 'node:assert/strict'
import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { createServer } from 'vite'

test('all trains have one card each, grouped classes, and selectable later results', async () => {
  const server = await createServer({ server: { middlewareMode: true, hmr: false }, appType: 'custom' })
  try {
    const { default: TrainOptions } = await server.ssrLoadModule('/src/components/TrainOptions.jsx')
    const trains = Array.from({ length: 13 }, (_, i) => ({
      no: String(14000 + i), name: `Service ${i}`, classes: ['CC', 'EC'],
      class_details: { CC: { status: 'AVL 14', seats: 14, price: 520 } },
    }))
    trains[0].classes = []
    const selected = []
    const props = { trains, slots: { source: 'Delhi', destination: 'Chandigarh', date: '2026-10-22' },
      disabled: false, onSelect: (...args) => selected.push(args) }
    const html = renderToStaticMarkup(React.createElement(TrainOptions, props))
    assert.equal((html.match(/<article /g) || []).length, 13)
    assert.equal((html.match(/<button /g) || []).length, 24)
    assert.match(html, /Service 12/)
    assert.match(html, /Class information was not returned/)
    assert.match(html, /AVL 14/)
    const buttons = []
    function visit(element) {
      if (!element || typeof element !== 'object') return
      if (element.type === 'button') buttons.push(element)
      React.Children.forEach(element.props?.children, visit)
    }
    visit(TrainOptions(props))
    buttons.at(-1).props.onClick()
    assert.deepEqual(selected, [[trains[12], 'EC']])
    const disabledHtml = renderToStaticMarkup(React.createElement(TrainOptions, { ...props, disabled: true }))
    assert.equal((disabledHtml.match(/disabled=""/g) || []).length, 24)
  } finally {
    await server.close()
  }
})
