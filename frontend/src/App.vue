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
    <main class="main">
      <DocumentPanel />
      <ChatPanel />
    </main>
  </div>
</template>

<script setup>
import DocumentPanel from './components/DocumentPanel.vue'
import ChatPanel from './components/ChatPanel.vue'
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

@media (max-width: 720px) {
  .tag {
    display: none;
  }
}
</style>
