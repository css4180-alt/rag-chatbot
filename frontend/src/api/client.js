const BASE = '/api'

// 콜드 스타트(머신 자동 중지 후 재기동) 동안 프록시가 돌려주는 상태 코드.
// 이 환경에선 기동에 수 분이 걸릴 수 있어 넉넉히 재시도한다.
const COLD_STATUSES = new Set([502, 503, 504])
const MAX_RETRIES = 60
const RETRY_DELAY = 4000

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

const TOKEN_KEY = 'rag.token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}
export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

// 저장된 토큰을 Authorization 헤더로 만든다(없으면 빈 객체).
function authHeaders() {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

// 서버가 깨어나는 중일 때 UI에 알리기 위한 훅(스토어가 등록)
let wakingHandler = null
export function setWakingHandler(fn) {
  wakingHandler = fn
}
function notifyWaking(active) {
  wakingHandler?.(active)
}

// 401(미인증/세션 만료) 발생 시 스토어가 로그인 화면으로 되돌리기 위한 훅
let unauthorizedHandler = null
export function setUnauthorizedHandler(fn) {
  unauthorizedHandler = fn
}
function notifyUnauthorized() {
  unauthorizedHandler?.()
}

/**
 * 콜드 스타트(502/503/504/네트워크 오류)에 대해 자동 재시도하는 fetch.
 * 첫 재시도 시 '깨어나는 중' 상태를 알리고, 성공하면 해제한다.
 */
async function fetchRetry(url, opts = {}) {
  // 저장된 토큰을 항상 헤더에 실어 보낸다(기존 헤더는 보존).
  opts = { ...opts, headers: { ...authHeaders(), ...(opts.headers || {}) } }
  let signaled = false
  for (let attempt = 0; ; attempt++) {
    try {
      const res = await fetch(url, opts)
      if (res.status === 401) {
        // 토큰 만료/무효: 세션 정리 후 로그인 화면으로.
        setToken(null)
        notifyUnauthorized()
        return res
      }
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

// ---- 인증 ----

/**
 * 패스코드로 로그인. 성공 시 토큰을 저장하고 쿼터 정보를 반환한다.
 * @param {string} passcode
 * @returns {Promise<{token: string, quota: object}>}
 */
export async function login(passcode) {
  const res = await fetch(`${BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ passcode }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || '로그인에 실패했습니다.')
  }
  const data = await res.json()
  setToken(data.token)
  return data
}

/** 현재 토큰의 계정·쿼터 정보 조회(세션 복원용). 실패 시 null. */
export async function getMe() {
  const token = getToken()
  if (!token) return null
  const res = await fetch(`${BASE}/auth/me`, { headers: authHeaders() })
  if (!res.ok) {
    if (res.status === 401) setToken(null)
    return null
  }
  return res.json()
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

/** 빈 대화를 미리 만든다(첫 메시지 전에도 전용 문서를 올릴 수 있도록). */
export async function createSession() {
  const res = await fetchRetry(`${BASE}/chat/sessions`, { method: 'POST' })
  if (!res.ok) throw new Error('새 대화 생성 실패')
  return res.json()
}

export async function getMessages(sessionId) {
  const res = await fetchRetry(`${BASE}/chat/sessions/${sessionId}/messages`)
  if (!res.ok) throw new Error('대화 내용 조회 실패')
  return res.json()
}

/** 대화 제목 변경. 변경된 세션을 반환한다. */
export async function renameSession(sessionId, title) {
  const res = await fetchRetry(`${BASE}/chat/sessions/${sessionId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || '제목 수정 실패')
  }
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
        // 429(쿼터 초과) 등은 서버가 detail 메시지를 준다. 그대로 전달.
        const err = await res.json().catch(() => ({}))
        callbacks.onError?.(err.detail || '서버 오류가 발생했습니다.')
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
