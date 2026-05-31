const BASE = '/api'

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
  const res = await fetch(`${BASE}/documents${qs ? `?${qs}` : ''}`)
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
  const res = await fetch(`${BASE}/documents`, { method: 'POST', body: form })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || '업로드 실패')
  }
  return res.json()
}

export async function deleteDocument(id) {
  const res = await fetch(`${BASE}/documents/${id}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('삭제 실패')
}

// ---- 대화(세션) ----

export async function listSessions() {
  const res = await fetch(`${BASE}/chat/sessions`)
  if (!res.ok) throw new Error('대화 목록 조회 실패')
  return res.json()
}

export async function getMessages(sessionId) {
  const res = await fetch(`${BASE}/chat/sessions/${sessionId}/messages`)
  if (!res.ok) throw new Error('대화 내용 조회 실패')
  return res.json()
}

export async function deleteSession(sessionId) {
  const res = await fetch(`${BASE}/chat/sessions/${sessionId}`, { method: 'DELETE' })
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
  fetch(`${BASE}/chat`, {
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
