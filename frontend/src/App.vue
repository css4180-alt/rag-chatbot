<template>
  <!-- 세션 복원 전: 깜빡임 방지용 빈 화면 -->
  <div v-if="!store.authReady" class="boot" aria-hidden="true"></div>

  <!-- 미인증: 패스코드 게이트 -->
  <LoginGate v-else-if="!store.authed" />

  <!-- 인증 완료: 본 앱 -->
  <div v-else class="app">
    <header class="header">
      <div class="brand">
        <span class="mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="22" height="22">
            <rect class="ln" x="5" y="6" width="14" height="2.1" rx="1.05" />
            <rect class="ln" x="5" y="11" width="14" height="2.1" rx="1.05" />
            <rect class="ln accent" x="5" y="16" width="7.5" height="2.1" rx="1.05" />
            <circle class="dot" cx="16.5" cy="17.05" r="2.3" />
          </svg>
        </span>
        <span class="title">RAG Chatbot</span>
        <span class="tag">문서 기반 질의응답</span>
      </div>
      <div class="header-right">
        <div v-if="quotaVisible" class="quota-chip" :title="quotaTitle">
          <div class="quota-head">
            <span class="quota-label">남은 사용량 {{ accountRemainingPct }}%</span>
            <span class="quota-reset">{{ resetText }}</span>
          </div>
          <div class="quota-bar">
            <div
              class="quota-fill"
              :class="{ low: accountRemainingPct <= 15 }"
              :style="{ width: accountRemainingPct + '%' }"
            ></div>
          </div>
        </div>
        <button v-if="store.authed" class="ghost-link" type="button" @click="store.logout()">
          로그아웃
        </button>
        <a class="ghost-link" href="https://github.com/css4180-alt/rag-chatbot" target="_blank" rel="noopener">
          GitHub
        </a>
      </div>
    </header>
    <transition name="wake-slide">
      <div v-if="store.waking" class="waking-banner" role="status">
        <span class="wake-dot" aria-hidden="true"></span>
        서버가 절전 상태에서 깨어나는 중입니다. 최대 2~3분 정도 걸릴 수 있어요…
      </div>
    </transition>
    <main class="main">
      <ConversationSidebar />
      <ChatPanel />
      <DocumentPanel />
    </main>
    <TutorialOverlay />
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import ConversationSidebar from './components/ConversationSidebar.vue'
import DocumentPanel from './components/DocumentPanel.vue'
import ChatPanel from './components/ChatPanel.vue'
import LoginGate from './components/LoginGate.vue'
import TutorialOverlay from './components/TutorialOverlay.vue'
import { store } from './store.js'

onMounted(() => store.init())

// 잔여 토큰 칩(인증이 켜진 데모에서만 표시). 계정 잔여를 퍼센트로 보여준다.
const quotaVisible = computed(() => Boolean(store.quota && store.quota.auth_enabled))

const accountRemainingPct = computed(() => {
  const q = store.quota
  if (!q || !q.account_limit) return 0
  return Math.max(0, Math.min(100, Math.round((q.account_remaining / q.account_limit) * 100)))
})

// 다음 UTC 자정까지 남은 시간(쿼터는 UTC 자정마다 초기화된다).
const resetText = computed(() => {
  const now = new Date()
  const next = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() + 1, 0, 0, 0)
  const ms = next - now.getTime()
  const h = Math.floor(ms / 3_600_000)
  const m = Math.floor((ms % 3_600_000) / 60_000)
  return h >= 1 ? `${h}시간 후 초기화` : `${m}분 후 초기화`
})

const quotaTitle = computed(() => {
  const q = store.quota
  if (!q || !q.auth_enabled) return ''
  return (
    `계정(${q.account}) ${q.account_used.toLocaleString()}/${q.account_limit.toLocaleString()} 토큰 · ` +
    `사이트 전체 ${q.site_used.toLocaleString()}/${q.site_limit.toLocaleString()} 토큰`
  )
})
</script>

<style scoped>
.app {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.header {
  height: 58px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 22px;
  background: var(--surface);
  border-bottom: 1px solid var(--line);
}

.boot {
  height: 100%;
  background: var(--paper);
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.quota-chip {
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 168px;
  padding: 6px 11px 7px;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--surface-2);
}
.quota-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
  white-space: nowrap;
}
.quota-label {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--ink);
}
.quota-reset {
  font-family: var(--font-mono);
  font-size: 0.64rem;
  color: var(--ink-faint);
}
.quota-bar {
  height: 4px;
  border-radius: 99px;
  background: var(--line-strong);
  overflow: hidden;
}
.quota-fill {
  height: 100%;
  border-radius: 99px;
  background: var(--accent);
  transition: width 0.4s ease, background 0.3s ease;
}
.quota-fill.low {
  background: var(--danger);
}

.mark {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 9px;
  background: var(--ink);
  box-shadow: var(--shadow-sm);
}
.mark .ln { fill: var(--paper); }
.mark .ln.accent,
.mark .dot { fill: var(--accent); }

.title {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 1.28rem;
  letter-spacing: -0.015em;
  color: var(--ink);
}

.tag {
  font-family: var(--font-mono);
  font-size: 0.68rem;
  letter-spacing: 0.02em;
  color: var(--ink-faint);
  padding: 3px 8px;
  border: 1px solid var(--line);
  border-radius: 99px;
}

.ghost-link {
  font-family: var(--font-mono);
  font-size: 0.78rem;
  text-decoration: none;
  color: var(--ink-soft);
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid var(--line);
  background: transparent;
  cursor: pointer;
  transition: color 0.18s, border-color 0.18s, background 0.18s;
}
.ghost-link:hover {
  color: var(--ink);
  border-color: var(--line-strong);
  background: var(--surface-2);
}

.main {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* 콜드 스타트 안내 배너 */
.waking-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  flex-shrink: 0;
  padding: 9px 16px;
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--accent);
  background: var(--accent-soft);
  border-bottom: 1px solid color-mix(in srgb, var(--accent) 25%, transparent);
}
.wake-dot {
  width: 8px;
  height: 8px;
  border-radius: 99px;
  background: var(--accent);
  animation: wake-pulse 1.1s ease-in-out infinite;
}
@keyframes wake-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.35; transform: scale(0.7); }
}
.wake-slide-enter-active,
.wake-slide-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.wake-slide-enter-from,
.wake-slide-leave-to {
  opacity: 0;
  transform: translateY(-100%);
}

@media (max-width: 720px) {
  .tag {
    display: none;
  }
  .quota-chip {
    min-width: 0;
  }
  .quota-reset {
    display: none;
  }
}
</style>
