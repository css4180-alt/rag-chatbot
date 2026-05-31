<template>
  <aside class="conv-sidebar">
    <button class="new-btn" :disabled="store.streaming" @click="store.newConversation()">
      <span class="plus" aria-hidden="true">＋</span> 새 대화
    </button>

    <div class="list-head">대화 목록</div>

    <ul v-if="store.sessions.length" class="conv-list">
      <li
        v-for="s in store.sessions"
        :key="s.id"
        class="conv-item"
        :class="{ active: s.id === store.activeSessionId }"
        @click="store.selectSession(s.id)"
      >
        <span class="conv-title">{{ s.title || '새 대화' }}</span>
        <span class="conv-time">{{ relTime(s.last_message_at) }}</span>
        <button class="conv-del" title="대화 삭제" @click.stop="confirmDelete(s)">✕</button>
      </li>
    </ul>
    <div v-else class="conv-empty">
      <p>아직 대화가 없습니다.</p>
      <p class="muted">질문을 보내면 대화가 저장됩니다.</p>
    </div>
  </aside>
</template>

<script setup>
import { store } from '../store.js'

function relTime(iso) {
  if (!iso) return ''
  const then = new Date(iso.endsWith('Z') ? iso : iso + 'Z')
  const diff = (Date.now() - then.getTime()) / 1000
  if (diff < 60) return '방금'
  if (diff < 3600) return `${Math.floor(diff / 60)}분 전`
  if (diff < 86400) return `${Math.floor(diff / 3600)}시간 전`
  if (diff < 604800) return `${Math.floor(diff / 86400)}일 전`
  return then.toLocaleDateString('ko-KR', { month: 'numeric', day: 'numeric' })
}

async function confirmDelete(s) {
  if (!confirm(`'${s.title || '새 대화'}' 대화를 삭제할까요?\n이 대화 전용 문서도 함께 삭제됩니다.`)) return
  await store.removeSession(s.id)
}
</script>

<style scoped>
.conv-sidebar {
  display: flex;
  flex-direction: column;
  gap: 14px;
  width: 240px;
  min-width: 240px;
  padding: 18px 14px;
  background: var(--surface);
  border-right: 1px solid var(--line);
  overflow-y: auto;
}

.new-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 14px;
  border: 1px solid var(--accent);
  border-radius: var(--radius-sm);
  background: var(--accent-soft);
  color: var(--accent);
  font-weight: 600;
  font-size: 0.86rem;
  cursor: pointer;
  transition: background 0.16s, transform 0.12s;
}
.new-btn:hover:not(:disabled) { background: var(--accent); color: var(--accent-ink); }
.new-btn:active:not(:disabled) { transform: scale(0.98); }
.new-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.new-btn .plus { font-size: 1rem; line-height: 1; }

.list-head {
  font-family: var(--font-mono);
  font-size: 0.66rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--ink-faint);
  padding: 0 4px;
}

.conv-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.conv-item {
  display: grid;
  grid-template-columns: 1fr auto;
  grid-template-areas: 'title del' 'time del';
  align-items: center;
  gap: 0 6px;
  padding: 9px 10px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  border: 1px solid transparent;
  transition: background 0.14s, border-color 0.14s;
}
.conv-item:hover { background: var(--surface-2); }
.conv-item:hover .conv-del { opacity: 1; }
.conv-item.active {
  background: var(--accent-soft);
  border-color: color-mix(in srgb, var(--accent) 30%, transparent);
}

.conv-title {
  grid-area: title;
  font-size: 0.84rem;
  font-weight: 600;
  color: var(--ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.conv-time {
  grid-area: time;
  font-family: var(--font-mono);
  font-size: 0.64rem;
  color: var(--ink-faint);
}
.conv-del {
  grid-area: del;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--ink-faint);
  font-size: 0.72rem;
  padding: 4px;
  border-radius: 5px;
  opacity: 0;
  transition: opacity 0.14s, color 0.14s, background 0.14s;
}
.conv-del:hover { color: var(--danger); background: var(--surface); }

.conv-empty {
  margin-top: 12px;
  padding: 0 4px;
  font-size: 0.8rem;
  color: var(--ink-soft);
}
.conv-empty .muted { color: var(--ink-faint); font-size: 0.74rem; margin-top: 4px; }
</style>
