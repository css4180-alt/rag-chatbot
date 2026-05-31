<template>
  <ul v-if="docs.length" class="doc-list">
    <li v-for="doc in docs" :key="doc.id" class="doc-item" :class="doc.status">
      <span class="doc-dot" :class="doc.status" aria-hidden="true"></span>
      <span class="doc-name" :title="doc.filename">{{ doc.filename }}</span>
      <button class="del-btn" title="삭제" @click="$emit('delete', { id: doc.id, scope })">✕</button>
      <span class="doc-meta">{{ doc.chunk_count }} chunks · {{ statusLabel(doc.status) }}</span>
    </li>
  </ul>
  <p v-else class="empty">{{ empty }}</p>
</template>

<script setup>
defineProps({
  docs: { type: Array, required: true },
  scope: { type: String, required: true },
  empty: { type: String, default: '문서가 없습니다.' },
})
defineEmits(['delete'])

function statusLabel(status) {
  return { ready: '준비됨', processing: '처리 중', error: '오류' }[status] ?? status
}
</script>

<style scoped>
.doc-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.doc-item {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 8px;
  padding: 9px 11px;
  background: var(--surface);
  border-radius: var(--radius-sm);
  border: 1px solid var(--line);
  transition: border-color 0.16s, box-shadow 0.16s;
  animation: slide-in 0.3s ease backwards;
}
.doc-item:hover { border-color: var(--line-strong); box-shadow: var(--shadow-sm); }
@keyframes slide-in {
  from { opacity: 0; transform: translateY(4px); }
}

.doc-dot {
  width: 7px;
  height: 7px;
  border-radius: 99px;
  background: var(--ink-faint);
}
.doc-dot.ready { background: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }
.doc-dot.processing { background: #d99a2b; animation: pulse 1.2s ease-in-out infinite; }
.doc-dot.error { background: var(--danger); }
@keyframes pulse { 50% { opacity: 0.35; } }

.doc-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 600;
  font-size: 0.82rem;
  color: var(--ink);
}
.doc-meta {
  grid-column: 2 / 4;
  font-family: var(--font-mono);
  font-size: 0.65rem;
  color: var(--ink-faint);
  white-space: nowrap;
}
.del-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--ink-faint);
  font-size: 0.72rem;
  padding: 2px 4px;
  border-radius: 5px;
  transition: color 0.16s, background 0.16s;
}
.del-btn:hover { color: var(--danger); background: var(--surface-2); }

.empty {
  font-size: 0.78rem;
  color: var(--ink-faint);
  padding: 4px 2px;
}
</style>
