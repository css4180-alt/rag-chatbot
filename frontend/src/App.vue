<template>
  <div class="app">
    <header class="header">
      <div class="brand">
        <span class="mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 5.5A1.5 1.5 0 0 1 5.5 4H11v16H5.5A1.5 1.5 0 0 1 4 18.5z" />
            <path d="M20 5.5A1.5 1.5 0 0 0 18.5 4H13v16h5.5a1.5 1.5 0 0 0 1.5-1.5z" />
          </svg>
        </span>
        <span class="title">RAG Chatbot</span>
        <span class="tag">문서 기반 질의응답</span>
      </div>
      <a class="ghost-link" href="https://github.com/css4180-alt/rag-chatbot" target="_blank" rel="noopener">
        GitHub
      </a>
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
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import ConversationSidebar from './components/ConversationSidebar.vue'
import DocumentPanel from './components/DocumentPanel.vue'
import ChatPanel from './components/ChatPanel.vue'
import { store } from './store.js'

onMounted(() => store.init())
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

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.mark {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 9px;
  color: var(--accent-ink);
  background: var(--accent);
  box-shadow: var(--shadow-sm);
}

.title {
  font-weight: 700;
  font-size: 1.02rem;
  letter-spacing: -0.01em;
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
}
</style>
