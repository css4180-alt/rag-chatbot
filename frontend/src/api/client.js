const BASE = '/api'

// 콜드 스타트(머신 자동 중지 후 재기동) 동안 프록시가 돌려주는 상태 코드.
// 이 환경에선 기동에 수 분이 걸릴 수 있어 넉넉히 재시도한다.
const COLD_STATUSES = new Set([502, 503, 504])
const MAX_RETRIES = 60
const RETRY_DELAY = 4000

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

// 서버가 깨어나는 중일 때 UI에 알리기 위한 훅(스토어가 등록)
let wakingHandler = null
export function setWakingHandler(fn) {
  wakingHandler = fn
}
function notifyWaking(active) {
  wakingHandler?.(active)
}

/**
 * 콜드 스타트(502/503/504/네트워크 오류)에 대해 자동 재시도하는 fetch.
 * 첫 재시도 시 '깨어나는 중' 상태를 알리고, 성공하면 해제한다.
 */
async function fetchRetry(url, opts = {}) {
  let signaled = false
  for (let attempt = 0; ; attempt++) {
    try {
      const res = await fetch(url, opts)
      if (COLD_STATUSES.has(res.status) && attempt < MAX_RETRIES) {
        if (!signaled) {
          signaled = true
          notifyWaking(true)
        }
        await sleep(RETRY_DELAY)
        continue
      }
      if (signaled) notifyWaking(false)
      return res
    } catch (err) {
      // 네트워크 단절(기동 중 연결 거부 등)도 재시도 대상
      if (attempt < MAX_RETRIES) {
        if (!signaled) {
          signaled = true
          notifyWaking(true)
        }
        await sleep(RETRY_DELAY)
        continue
      }
      if (signaled) notifyWaking(false)
      throw err
    }
  }
}

// ---- 문서 ----

/**
 * 문서 목록 조회
 * @param {{ scope?: 'global', sessionId?: number }} [opts]
 */
export async function listDocuments(opts = {}) {
  const params = new URLSearchParams()
  if (opts.scope) params.set('scope', opts.scope)
  if (opts.sessionId != null) params.set('session_id', opts.sessionId)
  const qs = params.toString()
  const res = await fetchRetry(`${BASE}/documents${qs ? `?${qs}` : ''}`)
  if (!res.ok) throw new Error('문서 목록 조회 실패')
  return res.json()
}

/**
 * 문서 업로드
 * @param {File} file
 * @param {number|null} [sessionId] 지정 시 해당 대화 전용 문서, 없으면 전역 문서
 */
export async function uploadDocument(file, sessionId = null) {
  const form = new FormData()
  form.append('file', file)
  if (sessionId != null) form.append('session_id', sessionId)
  const res = await fetchRetry(`${BASE}/documents`, { method: 'POST', body: form })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || '업로드 실패')
  }
  return res.json()
}

export async function deleteDocument(id) {
  const res = await fetchRetry(`${BASE}/documents/${id}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('삭제 실패')
}

// ---- 대화(세션) ----

export async function listSessions() {
  const res = await fetchRetry(`${BASE}/chat/sessions`)
  if (!res.ok) throw new Error('대화 목록 조회 실패')
  return res.json()
}

export async function getMessages(sessionId) {
  const res = await fetchRetry(`${BASE}/chat/sessions/${sessionId}/messages`)
  if (!res.ok) throw new Error('대화 내용 조회 실패')
  return res.json()
}

export async function deleteSession(sessionId) {
  const res = await fetchRetry(`${BASE}/chat/sessions/${sessionId}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('대화 삭제 실패')
}

// ---- 채팅(SSE 스트리밍) ----

/**
 * SSE 스트리밍 채팅 요청
 * @param {string} question
 * @param {number|null} sessionId
 * @param {{ onSessionId, onToken, onSources, onDone, onError }} callbacks
 */
export function askQuestion(question, sessionId, callbacks) {
  // POST 자체는 콜드 스타트(502 등)에 대해 재시도한다. 502는 요청이 앱에
  // 도달하기 전 프록시 단에서 막힌 것이라 중복 처리 위험이 없다.
  fetchRetry(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, session_id: sessionId }),
  })
    .then(async (res) => {
      if (!res.ok) {
        callbacks.onError?.('서버 오류가 발생했습니다.')
        return
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() // 마지막 불완전한 줄은 다음 청크와 합침

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const payload = JSON.parse(line.slice(6))
            if (payload.type === 'session_id') callbacks.onSessionId?.(payload.session_id)
            else if (payload.type === 'token') callbacks.onToken?.(payload.content)
            else if (payload.type === 'sources') callbacks.onSources?.(payload.sources)
            else if (payload.type === 'done') callbacks.onDone?.()
          } catch {
            // JSON 파싱 실패 무시
          }
        }
      }
    })
    .catch((err) => {
      callbacks.onError?.(err.message)
    })
}
