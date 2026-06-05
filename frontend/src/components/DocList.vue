<template>
  <ul v-if="docs.length" class="doc-list">
    <li v-for="doc in docs" :key="doc.id" class="doc-item" :class="doc.status">
      <span class="doc-dot" :class="doc.status" aria-hidden="true"></span>
      <span class="doc-name" :title="doc.filename">{{ doc.filename }}</span>
      <span class="doc-tools">
        <button
          v-if="doc.has_file"
          class="tool-btn"
          data-tip="미리보기"
          @click="store.openPreview(doc)"
        >
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2.5 12s3.5-6.5 9.5-6.5S21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z" />
            <circle cx="12" cy="12" r="2.6" />
          </svg>
        </button>
        <a
          v-if="doc.has_file"
          class="tool-btn"
          data-tip="다운로드"
          :href="documentDownloadUrl(doc.id)"
          :download="doc.filename"
        >↓</a>
        <button class="tool-btn del" data-tip="삭제" @click="$emit('delete', { id: doc.id, scope })">✕</button>
      </span>
      <span class="doc-meta">{{ doc.chunk_count }} chunks · {{ statusLabel(doc.status) }}</span>
    </li>
  </ul>
  <p v-else class="empty">{{ empty }}</p>
</template>

<script setup>
import { store } from '../store.js'
import { documentDownloadUrl } from '../api/client.js'

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
.doc-tools {
  display: inline-flex;
  align-items: center;
  gap: 1px;
}
.tool-btn {
  position: relative;
  display: inline-grid;
  place-items: center;
  min-width: 22px;
  height: 22px;
  background: none;
  border: none;
  cursor: pointer;
  text-decoration: none;
  color: var(--ink-faint);
  font-size: 0.78rem;
  line-height: 1;
  padding: 0 4px;
  border-radius: 5px;
  transition: color 0.16s, background 0.16s;
}
.tool-btn:hover { color: var(--accent); background: var(--surface-2); }
.tool-btn.del:hover { color: var(--danger); background: var(--surface-2); }

/* CSS 툴팁 — data-tip 속성 값을 말풍선으로 표시 */
.tool-btn::after {
  content: attr(data-tip);
  pointer-events: none;
  position: absolute;
  bottom: calc(100% + 5px);
  left: 50%;
  transform: translateX(-50%) scale(0.9);
  white-space: nowrap;
  font-family: var(--font-sans);
  font-size: 0.67rem;
  font-weight: 500;
  color: var(--surface);
  background: var(--ink);
  padding: 3px 7px;
  border-radius: 5px;
  opacity: 0;
  transition: opacity 0.12s ease, transform 0.12s ease;
  z-index: 10;
}
.tool-btn:hover::after {
  opacity: 1;
  transform: translateX(-50%) scale(1);
}

.empty {
  font-size: 0.78rem;
  color: var(--ink-faint);
  padding: 4px 2px;
}
</style>
