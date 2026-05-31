import { reactive } from 'vue'
import {
  askQuestion,
  deleteDocument,
  deleteSession,
  getMessages,
  listDocuments,
  listSessions,
  setWakingHandler,
  uploadDocument,
} from './api/client.js'

const ACTIVE_KEY = 'rag.activeSessionId'

export const store = reactive({
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

  // ---- 초기화 ----
  async init() {
    // 콜드 스타트 중에는 API 클라이언트가 이 플래그를 켜고 끈다.
    setWakingHandler((active) => {
      this.waking = active
    })
    await this.loadSessions()
    await this.loadGlobalDocs()
    const saved = Number(localStorage.getItem(ACTIVE_KEY))
    if (saved && this.sessions.some((s) => s.id === saved)) {
      await this.selectSession(saved)
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

  newConversation() {
    if (this.streaming) return
    this.activeSessionId = null
    this.messages = []
    this.sessionDocs = []
    this.streamingText = ''
    localStorage.removeItem(ACTIVE_KEY)
  },

  async removeSession(id) {
    await deleteSession(id)
    if (this.activeSessionId === id) this.newConversation()
    await this.loadSessions()
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
  },
})
