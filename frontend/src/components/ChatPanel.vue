<template>
  <section class="chat-panel">
    <div class="messages" ref="messagesEl">
      <div v-if="!store.messages.length && !store.streaming" class="welcome">
        <span class="welcome-mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="34" height="34" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            <path d="M8 9h8M8 13h5" />
          </svg>
        </span>
        <h3>무엇이든 물어보세요</h3>
        <p>왼쪽에서 문서를 업로드한 뒤, 내용을 자연어로 질문하면<br />근거가 되는 출처와 함께 답변해 드립니다.</p>
        <div class="hint-chips">
          <span>요약해줘</span>
          <span>핵심만 정리해줘</span>
          <span>이 문서의 결론은?</span>
        </div>
      </div>

      <div
        v-for="(msg, i) in store.messages"
        :key="i"
        class="message"
        :class="msg.role"
      >
        <span class="role-tag">{{ msg.role === 'user' ? 'YOU' : 'AI' }}</span>
        <div class="bubble">
          <span class="text">{{ msg.content }}</span>
          <div v-if="msg.sources?.length" class="sources">
            <span class="sources-label">참조 문서</span>
            <span v-for="(src, j) in dedupeSources(msg.sources)" :key="j" class="source-tag">
              {{ src.filename }}
            </span>
          </div>
        </div>
      </div>

      <!-- 스트리밍 중인 답변 -->
      <div v-if="store.streaming" class="message assistant">
        <span class="role-tag">AI</span>
        <div class="bubble">
          <span v-if="store.streamingText" class="text">{{ store.streamingText }}<span class="cursor">▋</span></span>
          <span v-else class="typing" aria-label="생각 중"><i></i><i></i><i></i></span>
        </div>
      </div>
    </div>

    <form class="input-row" @submit.prevent="send">
      <input
        v-model="input"
        placeholder="질문을 입력하세요…"
        :disabled="store.streaming"
        class="chat-input"
      />
      <button type="submit" :disabled="store.streaming || !input.trim()" class="send-btn">
        {{ store.streaming ? '…' : '전송' }}
      </button>
    </form>
  </section>
</template>

<script setup>
import { ref, nextTick, watch } from 'vue'
import { store } from '../store.js'

const input = ref('')
const messagesEl = ref(null)

async function scrollToBottom() {
  await nextTick()
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}

// 메시지/스트리밍 변화에 맞춰 자동 스크롤
watch(
  () => [store.messages.length, store.streamingText, store.activeSessionId],
  scrollToBottom,
)

function dedupeSources(sources) {
  const seen = new Set()
  return sources.filter((s) => {
    if (seen.has(s.filename)) return false
    seen.add(s.filename)
    return true
  })
}

function send() {
  const q = input.value.trim()
  if (!q || store.streaming) return
  input.value = ''
  store.send(q)
  scrollToBottom()
}
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  background: var(--paper);
  position: relative;
}
/* subtle dotted paper texture */
.chat-panel::before {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background-image: radial-gradient(var(--line) 1px, transparent 1px);
  background-size: 22px 22px;
  opacity: 0.35;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.6), transparent 60%);
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 28px clamp(16px, 5vw, 56px);
  display: flex;
  flex-direction: column;
  gap: 22px;
  position: relative;
}

/* Empty state */
.welcome {
  margin: auto;
  text-align: center;
  color: var(--ink-soft);
  max-width: 420px;
  animation: rise 0.5s ease;
}
.welcome-mark {
  display: inline-grid;
  place-items: center;
  width: 64px;
  height: 64px;
  border-radius: 18px;
  color: var(--accent);
  background: var(--accent-soft);
  margin-bottom: 18px;
}
.welcome h3 {
  font-size: 1.3rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--ink);
  margin-bottom: 8px;
}
.welcome p {
  font-size: 0.9rem;
  line-height: 1.7;
  color: var(--ink-soft);
}
.hint-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  margin-top: 20px;
}
.hint-chips span {
  font-family: var(--font-mono);
  font-size: 0.74rem;
  color: var(--ink-soft);
  padding: 6px 12px;
  border: 1px solid var(--line);
  border-radius: 99px;
  background: var(--surface);
}
@keyframes rise {
  from { opacity: 0; transform: translateY(10px); }
}

/* Messages */
.message {
  display: flex;
  flex-direction: column;
  gap: 5px;
  max-width: min(76%, 680px);
  animation: rise 0.32s ease;
}
.message.user { align-self: flex-end; align-items: flex-end; }
.message.assistant { align-self: flex-start; align-items: flex-start; }

.role-tag {
  font-family: var(--font-mono);
  font-size: 0.6rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  color: var(--ink-faint);
  padding: 0 4px;
}

.bubble {
  padding: 12px 16px;
  border-radius: var(--radius);
  font-size: 0.92rem;
  line-height: 1.62;
  white-space: pre-wrap;
  word-break: break-word;
  box-shadow: var(--shadow-sm);
}
.user .bubble {
  background: var(--user-bubble);
  color: var(--user-ink);
  border-bottom-right-radius: 5px;
}
.assistant .bubble {
  background: var(--surface);
  color: var(--ink);
  border: 1px solid var(--line);
  border-bottom-left-radius: 5px;
}

.cursor {
  color: var(--accent);
  animation: blink 1s step-start infinite;
}
@keyframes blink { 50% { opacity: 0; } }

/* typing indicator */
.typing {
  display: inline-flex;
  gap: 4px;
  padding: 2px 0;
}
.typing i {
  width: 6px;
  height: 6px;
  border-radius: 99px;
  background: var(--ink-faint);
  animation: bounce 1.2s ease-in-out infinite;
}
.typing i:nth-child(2) { animation-delay: 0.18s; }
.typing i:nth-child(3) { animation-delay: 0.36s; }
@keyframes bounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.5; }
  30% { transform: translateY(-5px); opacity: 1; }
}

/* Sources */
.sources {
  margin-top: 10px;
  padding-top: 9px;
  border-top: 1px dashed var(--line-strong);
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}
.sources-label {
  font-family: var(--font-mono);
  font-size: 0.62rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--ink-faint);
}
.source-tag {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  background: var(--accent-soft);
  color: var(--accent);
  padding: 3px 8px;
  border-radius: 6px;
}

/* Composer */
.input-row {
  display: flex;
  gap: 10px;
  padding: 16px clamp(16px, 5vw, 56px);
  border-top: 1px solid var(--line);
  background: var(--surface);
}

.chat-input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid var(--line-strong);
  border-radius: 11px;
  font-size: 0.92rem;
  color: var(--ink);
  background: var(--paper);
  outline: none;
  transition: border-color 0.18s, box-shadow 0.18s;
}
.chat-input::placeholder { color: var(--ink-faint); }
.chat-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}
.chat-input:disabled { opacity: 0.6; }

.send-btn {
  padding: 0 22px;
  background: var(--accent);
  color: var(--accent-ink);
  border: none;
  border-radius: 11px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.18s, transform 0.12s;
}
.send-btn:hover:not(:disabled) { background: var(--accent-strong); }
.send-btn:active:not(:disabled) { transform: scale(0.97); }
.send-btn:disabled { opacity: 0.45; cursor: not-allowed; }
</style>
