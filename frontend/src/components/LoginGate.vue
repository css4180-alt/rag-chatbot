<template>
  <div class="gate">
    <div class="gate-card">
      <span class="mark" aria-hidden="true">
        <svg viewBox="0 0 24 24" width="28" height="28">
          <rect class="ln" x="5" y="6" width="14" height="2.1" rx="1.05" />
          <rect class="ln" x="5" y="11" width="14" height="2.1" rx="1.05" />
          <rect class="ln accent" x="5" y="16" width="7.5" height="2.1" rx="1.05" />
          <circle class="dot" cx="16.5" cy="17.05" r="2.3" />
        </svg>
      </span>
      <h1 class="gate-title">RAG Chatbot</h1>
      <p class="gate-sub">문서 기반 질의응답 · 데모 접속</p>
      <p class="gate-note">
        공개 데모입니다. 비용 보호를 위해 <strong>패스코드</strong>로 접속하며,
        계정마다 하루 사용량이 제한됩니다.
      </p>

      <form class="gate-form" @submit.prevent="submit">
        <input
          ref="input"
          v-model="passcode"
          type="password"
          class="gate-input"
          placeholder="패스코드"
          autocomplete="off"
          :disabled="loading"
        />
        <button type="submit" class="gate-btn" :disabled="loading || !passcode.trim()">
          {{ loading ? '확인 중…' : '입장' }}
        </button>
      </form>

      <transition name="fade">
        <p v-if="error" class="gate-error">{{ error }}</p>
      </transition>

      <a class="gate-link" href="https://github.com/css4180-alt/rag-chatbot" target="_blank" rel="noopener">
        소스 코드 (GitHub)
      </a>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { store } from '../store.js'

const passcode = ref('')
const loading = ref(false)
const error = ref('')
const input = ref(null)

onMounted(() => input.value?.focus())

async function submit() {
  if (loading.value || !passcode.value.trim()) return
  loading.value = true
  error.value = ''
  try {
    await store.login(passcode.value.trim())
  } catch (err) {
    error.value = err.message || '로그인에 실패했습니다.'
    passcode.value = ''
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.gate {
  display: grid;
  place-items: center;
  height: 100%;
  padding: 24px;
  background:
    radial-gradient(120% 120% at 50% 0%, var(--accent-soft) 0%, transparent 55%),
    var(--paper);
}

.gate-card {
  width: 100%;
  max-width: 380px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 38px 34px 30px;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow-md);
}

.mark {
  display: grid;
  place-items: center;
  width: 52px;
  height: 52px;
  border-radius: 14px;
  background: var(--ink);
  box-shadow: var(--shadow-sm);
}
.mark .ln { fill: var(--paper); }
.mark .ln.accent,
.mark .dot { fill: var(--accent); }

.gate-title {
  margin-top: 18px;
  font-family: var(--font-display);
  font-size: 1.7rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: var(--ink);
}

.gate-sub {
  margin-top: 4px;
  font-family: var(--font-mono);
  font-size: 0.74rem;
  letter-spacing: 0.02em;
  color: var(--ink-faint);
}

.gate-note {
  margin-top: 18px;
  font-size: 0.84rem;
  line-height: 1.55;
  color: var(--ink-soft);
}
.gate-note strong {
  color: var(--ink);
  font-weight: 600;
}

.gate-form {
  width: 100%;
  margin-top: 22px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.gate-input {
  width: 100%;
  padding: 12px 14px;
  font-family: var(--font-mono);
  font-size: 0.95rem;
  letter-spacing: 0.08em;
  text-align: center;
  color: var(--ink);
  background: var(--surface-2);
  border: 1px solid var(--line-strong);
  border-radius: var(--radius-sm);
  transition: border-color 0.18s, box-shadow 0.18s;
}
.gate-input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.gate-btn {
  width: 100%;
  padding: 12px 14px;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--accent-ink);
  background: var(--accent);
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 0.18s, transform 0.08s;
}
.gate-btn:hover:not(:disabled) {
  background: var(--accent-strong);
}
.gate-btn:active:not(:disabled) {
  transform: translateY(1px);
}
.gate-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.gate-error {
  margin-top: 14px;
  font-size: 0.82rem;
  color: var(--danger);
}

.gate-link {
  margin-top: 22px;
  font-family: var(--font-mono);
  font-size: 0.72rem;
  color: var(--ink-faint);
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: color 0.18s, border-color 0.18s;
}
.gate-link:hover {
  color: var(--ink-soft);
  border-color: var(--line-strong);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
