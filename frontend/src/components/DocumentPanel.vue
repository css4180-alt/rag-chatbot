<template>
  <aside class="doc-panel">
    <!-- 전역 문서 -->
    <section class="doc-section">
      <div class="sec-head">
        <h2>전역 문서</h2>
        <span class="count" v-if="store.globalDocs.length">{{ store.globalDocs.length }}</span>
      </div>
      <p class="sec-desc">모든 대화에서 참조됩니다.</p>

      <label class="upload-btn" :class="{ loading: uploadingGlobal }">
        <input type="file" accept=".pdf,.md,.txt" :disabled="uploadingGlobal" @change="onUpload($event, 'global')" />
        <span class="upload-icon" aria-hidden="true">{{ uploadingGlobal ? '⟳' : '＋' }}</span>
        <span>{{ uploadingGlobal ? '업로드 중…' : '전역 문서 추가' }}</span>
        <small>PDF · Markdown · TXT</small>
      </label>

      <DocList :docs="store.globalDocs" scope="global" empty="전역 문서가 없습니다." @delete="onDelete" />
    </section>

    <div class="divider"></div>

    <!-- 이 대화 문서 -->
    <section class="doc-section">
      <div class="sec-head">
        <h2>이 대화 문서</h2>
        <span class="count" v-if="store.sessionDocs.length">{{ store.sessionDocs.length }}</span>
      </div>
      <p class="sec-desc">현재 대화에서만 참조됩니다.</p>

      <template v-if="hasSession">
        <label class="upload-btn" :class="{ loading: uploadingSession }">
          <input type="file" accept=".pdf,.md,.txt" :disabled="uploadingSession" @change="onUpload($event, 'session')" />
          <span class="upload-icon" aria-hidden="true">{{ uploadingSession ? '⟳' : '＋' }}</span>
          <span>{{ uploadingSession ? '업로드 중…' : '대화 문서 추가' }}</span>
          <small>PDF · Markdown · TXT</small>
        </label>
        <DocList :docs="store.sessionDocs" scope="session" empty="이 대화 전용 문서가 없습니다." @delete="onDelete" />
      </template>
      <div v-else class="locked">
        <span class="lock-mark" aria-hidden="true">⌁</span>
        <p>질문을 한 번 보내 대화를 시작하면<br />이 대화 전용 문서를 추가할 수 있습니다.</p>
      </div>
    </section>

    <p v-if="uploadError" class="error">{{ uploadError }}</p>
  </aside>
</template>

<script setup>
import { ref, computed } from 'vue'
import { store } from '../store.js'
import DocList from './DocList.vue'

const uploadingGlobal = ref(false)
const uploadingSession = ref(false)
const uploadError = ref('')

const hasSession = computed(() => store.activeSessionId != null)

async function onUpload(e, scope) {
  const file = e.target.files[0]
  if (!file) return
  uploadError.value = ''
  const flag = scope === 'global' ? uploadingGlobal : uploadingSession
  flag.value = true
  try {
    if (scope === 'global') await store.uploadGlobalDoc(file)
    else await store.uploadSessionDoc(file)
  } catch (err) {
    uploadError.value = err.message
  } finally {
    flag.value = false
    e.target.value = ''
  }
}

async function onDelete({ id, scope }) {
  if (!confirm('이 문서를 삭제할까요?')) return
  await store.removeDocument(id, scope)
}
</script>

<style scoped>
.doc-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 22px 16px;
  background: var(--surface);
  border-left: 1px solid var(--line);
  width: 290px;
  min-width: 290px;
  overflow-y: auto;
}

.doc-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.sec-head {
  display: flex;
  align-items: baseline;
  gap: 8px;
}
h2 {
  margin: 0;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.13em;
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
.sec-desc {
  font-size: 0.74rem;
  color: var(--ink-faint);
  margin-top: -4px;
}

.divider {
  height: 1px;
  background: var(--line);
  margin: 2px 0;
}

/* Upload dropzone */
.upload-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  padding: 14px 12px;
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
.upload-btn .upload-icon { font-size: 1.1rem; line-height: 1; }
.upload-btn span:nth-of-type(2) { font-size: 0.84rem; font-weight: 600; }
.upload-btn small {
  font-family: var(--font-mono);
  font-size: 0.6rem;
  letter-spacing: 0.03em;
  color: var(--ink-faint);
}
.upload-btn.loading { opacity: 0.6; cursor: not-allowed; }
.upload-btn.loading .upload-icon { animation: spin 0.9s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.upload-btn input { display: none; }

.locked {
  text-align: center;
  color: var(--ink-faint);
  padding: 16px 8px;
  border: 1px dashed var(--line);
  border-radius: var(--radius-sm);
  background: var(--paper);
}
.locked .lock-mark { display: block; font-size: 1.4rem; opacity: 0.5; margin-bottom: 6px; }
.locked p { font-size: 0.76rem; line-height: 1.6; }

.error {
  font-size: 0.78rem;
  color: var(--danger);
  font-family: var(--font-mono);
}
</style>
