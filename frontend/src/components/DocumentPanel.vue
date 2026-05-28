<template>
  <aside class="doc-panel">
    <h2>문서</h2>

    <label class="upload-btn" :class="{ loading: uploading }">
      <input type="file" accept=".pdf,.md,.txt" @change="handleUpload" :disabled="uploading" />
      {{ uploading ? '업로드 중…' : '+ 파일 추가' }}
    </label>
    <p v-if="uploadError" class="error">{{ uploadError }}</p>

    <ul v-if="documents.length" class="doc-list">
      <li v-for="doc in documents" :key="doc.id" class="doc-item">
        <span class="doc-name" :title="doc.filename">{{ doc.filename }}</span>
        <span class="doc-meta">{{ doc.chunk_count }}청크 · {{ statusLabel(doc.status) }}</span>
        <button class="del-btn" @click="handleDelete(doc.id)" title="삭제">✕</button>
      </li>
    </ul>
    <p v-else class="empty">업로드된 문서가 없습니다.</p>
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
  gap: 12px;
  padding: 20px;
  background: #f8f9fa;
  border-right: 1px solid #dee2e6;
  width: 260px;
  min-width: 260px;
  overflow-y: auto;
}

h2 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #343a40;
}

.upload-btn {
  display: block;
  text-align: center;
  padding: 8px;
  border: 2px dashed #adb5bd;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.875rem;
  color: #495057;
  transition: border-color 0.2s;
}
.upload-btn:hover { border-color: #4361ee; color: #4361ee; }
.upload-btn.loading { opacity: 0.6; cursor: not-allowed; }
.upload-btn input { display: none; }

.doc-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }

.doc-item {
  display: grid;
  grid-template-columns: 1fr auto auto;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  background: #fff;
  border-radius: 6px;
  border: 1px solid #dee2e6;
  font-size: 0.8rem;
}
.doc-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 500; }
.doc-meta { color: #868e96; white-space: nowrap; }
.del-btn {
  background: none; border: none; cursor: pointer;
  color: #adb5bd; font-size: 0.75rem; padding: 2px 4px;
}
.del-btn:hover { color: #e03131; }

.empty { font-size: 0.8rem; color: #adb5bd; text-align: center; margin-top: 20px; }
.error { font-size: 0.8rem; color: #e03131; }
</style>
