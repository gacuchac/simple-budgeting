import { expect, test } from 'vitest'
import config from '../vite.config'

test('the dev server binds 127.0.0.1:5173 and refuses another port', () => {
  expect(config.server).toMatchObject({ host: '127.0.0.1', port: 5173, strictPort: true })
})

test('the dev server proxies /api to the API', () => {
  expect(config.server?.proxy).toMatchObject({ '/api': { target: 'http://127.0.0.1:8000' } })
})
