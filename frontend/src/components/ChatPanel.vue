<template>
  <section class="chat-panel">
    <div class="messages" ref="messagesEl">
      <div v-if="!messages.length" class="welcome">
        <p>📄 문서를 업로드하고 질문해보세요.</p>
      </div>

      <div
        v-for="(msg, i) in messages"
        :key="i"
        class="message"
        :class="msg.role"
      >
        <div class="bubble">
          <span class="text">{{ msg.content }}</span>
          <div v-if="msg.sources?.length" class="sources">
            <span class="sources-label">참조 문서</span>
            <span v-for="(src, j) in msg.sources" :key="j" class="source-tag">
              {{ src.filename }}
            </span>
          </div>
        </div>
      </div>

      <!-- 스트리밍 중인 답변 -->
      <div v-if="streaming" class="message assistant">
        <div class="bubble">
          <span class="text">{{ streamingText }}<span class="cursor">▋</span></span>
        </div>
      </div>
    </div>

    <form class="input-row" @submit.prevent="send">
      <input
        v-model="input"
        placeholder="질문을 입력하세요…"
        :disabled="streaming"
        class="chat-input"
      />
      <button type="submit" :disabled="streaming || !input.trim()" class="send-btn">
        {{ streaming ? '…' : '전송' }}
      </button>
    </form>
  </section>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { askQuestion } from '../api/client.js'

const messages = ref([])
const input = ref('')
const streaming = ref(false)
const streamingText = ref('')
const sessionId = ref(null)
const messagesEl = ref(null)

async function scrollToBottom() {
  await nextTick()
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}

function send() {
  const question = input.value.trim()
  if (!question || streaming.value) return

  messages.value.push({ role: 'user', content: question })
  input.value = ''
  streaming.value = true
  streamingText.value = ''
  scrollToBottom()

  askQuestion(question, sessionId.value, {
    onSessionId(id) {
      sessionId.value = id
    },
    onToken(token) {
      streamingText.value += token
      scrollToBottom()
    },
    onSources(sources) {
      // sources는 done 이벤트 이후 메시지에 첨부
      messages.value.push({
        role: 'assistant',
        content: streamingText.value,
        sources,
      })
      streamingText.value = ''
      streaming.value = false
      scrollToBottom()
    },
    onDone() {
      // sources 없이 done이 오는 경우 대비
      if (streaming.value) {
        messages.value.push({ role: 'assistant', content: streamingText.value })
        streamingText.value = ''
        streaming.value = false
      }
      scrollToBottom()
    },
    onError(msg) {
      messages.value.push({ role: 'assistant', content: `오류: ${msg}` })
      streaming.value = false
      scrollToBottom()
    },
  })
}
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.welcome {
  text-align: center;
  color: #adb5bd;
  margin-top: 60px;
  font-size: 0.95rem;
}

.message { display: flex; }
.message.user { justify-content: flex-end; }
.message.assistant { justify-content: flex-start; }

.bubble {
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 0.9rem;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}
.user .bubble { background: #4361ee; color: #fff; border-bottom-right-radius: 4px; }
.assistant .bubble { background: #f1f3f5; color: #212529; border-bottom-left-radius: 4px; }

.cursor { animation: blink 1s step-start infinite; }
@keyframes blink { 50% { opacity: 0; } }

.sources { margin-top: 8px; display: flex; flex-wrap: wrap; gap: 4px; align-items: center; }
.sources-label { font-size: 0.7rem; color: #868e96; }
.source-tag {
  font-size: 0.7rem;
  background: #dee2e6;
  color: #495057;
  padding: 2px 6px;
  border-radius: 4px;
}

.input-row {
  display: flex;
  gap: 8px;
  padding: 16px 20px;
  border-top: 1px solid #dee2e6;
  background: #fff;
}

.chat-input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  font-size: 0.9rem;
  outline: none;
  transition: border-color 0.2s;
}
.chat-input:focus { border-color: #4361ee; }

.send-btn {
  padding: 10px 20px;
  background: #4361ee;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.2s;
}
.send-btn:hover:not(:disabled) { background: #3451d1; }
.send-btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
