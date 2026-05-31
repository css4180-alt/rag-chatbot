<template>
  <aside class="doc-panel">
    <div class="panel-head">
      <h2>문서</h2>
      <span class="count" v-if="documents.length">{{ documents.length }}</span>
    </div>

    <label class="upload-btn" :class="{ loading: uploading }">
      <input type="file" accept=".pdf,.md,.txt" @change="handleUpload" :disabled="uploading" />
      <span class="upload-icon" aria-hidden="true">{{ uploading ? '⟳' : '＋' }}</span>
      <span>{{ uploading ? '업로드 중…' : '파일 추가' }}</span>
      <small>PDF · Markdown · TXT</small>
    </label>
    <p v-if="uploadError" class="error">{{ uploadError }}</p>

    <ul v-if="documents.length" class="doc-list">
      <li v-for="doc in documents" :key="doc.id" class="doc-item" :class="doc.status">
        <span class="doc-dot" :class="doc.status" aria-hidden="true"></span>
        <span class="doc-name" :title="doc.filename">{{ doc.filename }}</span>
        <button class="del-btn" @click="handleDelete(doc.id)" title="삭제">✕</button>
        <span class="doc-meta">{{ doc.chunk_count }} chunks · {{ statusLabel(doc.status) }}</span>
      </li>
    </ul>
    <div v-else class="empty">
      <span class="empty-mark" aria-hidden="true">⌁</span>
      <p>업로드된 문서가 없습니다.</p>
    </div>
  </aside>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listDocuments, uploadDocument, deleteDocument } from '../api/client.js'

const documents = ref([])
const uploading = ref(false)
const uploadError = ref('')

async function loadDocuments() {
  documents.value = await listDocuments()
}

async function handleUpload(e) {
  const file = e.target.files[0]
  if (!file) return
  uploading.value = true
  uploadError.value = ''
  try {
    await uploadDocument(file)
    await loadDocuments()
  } catch (err) {
    uploadError.value = err.message
  } finally {
    uploading.value = false
    e.target.value = ''
  }
}

async function handleDelete(id) {
  if (!confirm('이 문서를 삭제할까요?')) return
  await deleteDocument(id)
  await loadDocuments()
}

function statusLabel(status) {
  return { ready: '준비됨', processing: '처리 중', error: '오류' }[status] ?? status
}

onMounted(loadDocuments)
</script>

<style scoped>
.doc-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 22px 18px;
  background: var(--surface);
  border-right: 1px solid var(--line);
  width: 280px;
  min-width: 280px;
  overflow-y: auto;
}

.panel-head {
  display: flex;
  align-items: baseline;
  gap: 8px;
}
h2 {
  margin: 0;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--ink-faint);
  font-family: var(--font-mono);
}
.count {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  color: var(--accent);
  background: var(--accent-soft);
  padding: 1px 7px;
  border-radius: 99px;
}

/* Upload dropzone */
.upload-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  padding: 18px 12px;
  border: 1.5px dashed var(--line-strong);
  border-radius: var(--radius-sm);
  cursor: pointer;
  color: var(--ink-soft);
  background: var(--paper);
  transition: border-color 0.18s, color 0.18s, background 0.18s;
}
.upload-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--accent-soft);
}
.upload-btn .upload-icon {
  font-size: 1.1rem;
  line-height: 1;
}
.upload-btn span:nth-of-type(2) {
  font-size: 0.86rem;
  font-weight: 600;
}
.upload-btn small {
  font-family: var(--font-mono);
  font-size: 0.62rem;
  letter-spacing: 0.03em;
  color: var(--ink-faint);
}
.upload-btn.loading {
  opacity: 0.6;
  cursor: not-allowed;
}
.upload-btn.loading .upload-icon {
  animation: spin 0.9s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
.upload-btn input { display: none; }

/* Document list */
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
  padding: 10px 12px;
  background: var(--surface);
  border-radius: var(--radius-sm);
  border: 1px solid var(--line);
  transition: border-color 0.16s, box-shadow 0.16s, transform 0.16s;
  animation: slide-in 0.3s ease backwards;
}
.doc-item:hover {
  border-color: var(--line-strong);
  box-shadow: var(--shadow-sm);
}
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
@keyframes pulse {
  50% { opacity: 0.35; }
}

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
.del-btn:hover {
  color: var(--danger);
  background: var(--surface-2);
}

.empty {
  margin-top: 28px;
  text-align: center;
  color: var(--ink-faint);
}
.empty-mark {
  display: block;
  font-size: 1.6rem;
  opacity: 0.5;
  margin-bottom: 6px;
}
.empty p {
  font-size: 0.8rem;
}
.error {
  font-size: 0.78rem;
  color: var(--danger);
  font-family: var(--font-mono);
}
</style>
