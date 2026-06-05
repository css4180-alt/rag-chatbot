import { reactive } from 'vue'
import {
  askQuestion,
  createSession,
  deleteDocument,
  deleteSession,
  getMe,
  getMessages,
  listDocuments,
  listSessions,
  login,
  renameSession,
  setToken,
  setUnauthorizedHandler,
  setWakingHandler,
  uploadDocument,
} from './api/client.js'

const ACTIVE_KEY = 'rag.activeSessionId'

export const store = reactive({
  // 인증/쿼터
  authed: false,
  account: null,
  quota: null, // { account_remaining, account_limit, site_remaining, ... }
  authReady: false, // 초기 세션 복원 시도 완료 여부

  // 대화
  sessions: [],
  activeSessionId: null, // null = 아직 저장되지 않은 새 대화
  messages: [],

  // 스트리밍 상태
  streaming: false,
  streamingText: '',

  // 문서
  globalDocs: [],
  sessionDocs: [],

  // 서버 콜드 스타트(깨어나는 중) 여부
  waking: false,

  // 세션 복원(새로고침)이 아닌 실제 로그인 직후인지 여부 — 튜토리얼 표시 판단에 사용
  freshLogin: false,

  // ---- 초기화 ----
  async init() {
    // 콜드 스타트 중에는 API 클라이언트가 이 플래그를 켜고 끈다.
    setWakingHandler((active) => {
      this.waking = active
    })
    // 토큰 만료/무효 시 로그인 화면으로 되돌린다.
    setUnauthorizedHandler(() => {
      this.authed = false
      this.account = null
      this.quota = null
    })
    // 저장된 토큰으로 세션 복원 시도
    const me = await getMe()
    if (me) {
      this.applyAuth(me)
      await this.loadAfterAuth()
    }
    this.authReady = true
  },

  // ---- 인증 ----
  applyAuth(quota) {
    this.authed = true
    this.account = quota.account
    this.quota = quota
  },

  async login(passcode) {
    const data = await login(passcode)
    this.freshLogin = true
    this.applyAuth(data.quota)
    await this.loadAfterAuth()
  },

  logout() {
    setToken(null)
    this.freshLogin = false
    this.authed = false
    this.account = null
    this.quota = null
    this.sessions = []
    this.messages = []
    this.globalDocs = []
    this.sessionDocs = []
    this.activeSessionId = null
  },

  async refreshQuota() {
    const me = await getMe()
    if (me) this.quota = me
  },

  async loadAfterAuth() {
    await this.loadSessions()
    await this.loadGlobalDocs()
    const saved = Number(localStorage.getItem(ACTIVE_KEY))
    if (saved && this.sessions.some((s) => s.id === saved)) {
      await this.selectSession(saved)
    } else {
      // 복원할 대화가 없으면 항상 새 대화 하나를 띄운다(첫 화면).
      await this.newConversation()
    }
  },

  // ---- 대화 ----
  async loadSessions() {
    this.sessions = await listSessions()
  },

  async selectSession(id) {
    if (this.streaming) return
    this.activeSessionId = id
    localStorage.setItem(ACTIVE_KEY, String(id))
    this.streamingText = ''
    this.messages = (await getMessages(id)).map((m) => ({
      role: m.role,
      content: m.content,
      sources: m.sources ?? [],
    }))
    await this.loadSessionDocs()
  },

  // 새 대화로 진입한다. 빈 대화를 DB에 즉시 만들어 활성화하므로,
  // 첫 메시지 전에도 이 대화 전용 문서를 업로드할 수 있다.
  // 이미 비어 있는 대화가 있으면 새로 만들지 않고 재사용해 빈 대화가 쌓이지 않게 한다.
  async newConversation() {
    if (this.streaming) return
    // 이미 빈 새 대화에 있다면 그대로 둔다.
    if (this.activeSessionId != null && this.messages.length === 0) return
    // 제목이 없는(=메시지가 없는) 기존 빈 대화가 있으면 재사용.
    const empty = this.sessions.find((s) => !s.title)
    if (empty) {
      await this.selectSession(empty.id)
      return
    }
    const session = await createSession()
    await this.loadSessions()
    await this.selectSession(session.id)
  },

  async renameSession(id, title) {
    const next = title.trim()
    if (!next) return
    const updated = await renameSession(id, next)
    // 목록의 해당 항목 제목을 갱신(전체 재조회 없이 즉시 반영).
    const s = this.sessions.find((x) => x.id === id)
    if (s) s.title = updated.title
  },

  async removeSession(id) {
    await deleteSession(id)
    await this.loadSessions()
    if (this.activeSessionId === id) {
      // 활성 대화가 삭제되면 초기 상태로 되돌린 뒤 새 대화를 띄운다.
      this.activeSessionId = null
      this.messages = []
      this.sessionDocs = []
      this.streamingText = ''
      localStorage.removeItem(ACTIVE_KEY)
      await this.newConversation()
    }
  },

  // ---- 문서 ----
  async loadGlobalDocs() {
    this.globalDocs = await listDocuments({ scope: 'global' })
  },

  async loadSessionDocs() {
    if (this.activeSessionId == null) {
      this.sessionDocs = []
      return
    }
    this.sessionDocs = await listDocuments({ sessionId: this.activeSessionId })
  },

  async uploadGlobalDoc(file) {
    await uploadDocument(file, null)
    await this.loadGlobalDocs()
  },

  async uploadSessionDoc(file) {
    if (this.activeSessionId == null) throw new Error('대화를 먼저 시작해 주세요.')
    await uploadDocument(file, this.activeSessionId)
    await this.loadSessionDocs()
  },

  async removeDocument(id, scope) {
    await deleteDocument(id)
    if (scope === 'global') await this.loadGlobalDocs()
    else await this.loadSessionDocs()
  },

  // ---- 채팅 ----
  send(question) {
    const q = question.trim()
    if (!q || this.streaming) return

    this.messages.push({ role: 'user', content: q })
    this.streaming = true
    this.streamingText = ''
    const wasNew = this.activeSessionId == null

    askQuestion(q, this.activeSessionId, {
      onSessionId: (id) => {
        this.activeSessionId = id
        localStorage.setItem(ACTIVE_KEY, String(id))
      },
      onToken: (token) => {
        this.streamingText += token
      },
      onSources: (sources) => {
        this.messages.push({
          role: 'assistant',
          content: this.streamingText,
          sources,
        })
        this.streamingText = ''
        this.streaming = false
        this._afterAnswer(wasNew)
      },
      onDone: () => {
        if (this.streaming) {
          this.messages.push({ role: 'assistant', content: this.streamingText })
          this.streamingText = ''
          this.streaming = false
          this._afterAnswer(wasNew)
        }
      },
      onError: (msg) => {
        this.messages.push({ role: 'assistant', content: `오류: ${msg}` })
        this.streamingText = ''
        this.streaming = false
      },
    })
  },

  async _afterAnswer(wasNew) {
    // 새 대화였다면 제목/목록을 갱신하고, 새로 만들어진 대화의 전용 문서 영역을 활성화
    await this.loadSessions()
    if (wasNew) await this.loadSessionDocs()
    // 답변 후 잔여 토큰을 갱신해 헤더 표시를 최신화
    await this.refreshQuota()
  },
})
