<template>
  <Teleport to="body">
    <transition name="pv-fade">
      <div v-if="store.preview" class="pv-back" @click.self="store.closePreview()">
        <div class="pv-modal" role="dialog" aria-modal="true">
          <header class="pv-head">
            <span class="pv-ext">{{ ext.toUpperCase() }}</span>
            <span class="pv-name" :title="filename">{{ filename }}</span>
            <div class="pv-actions">
              <a class="pv-btn" :href="downloadUrl" :download="filename" title="다운로드">
                <span aria-hidden="true">↓</span> 다운로드
              </a>
              <button class="pv-close" title="닫기" @click="store.closePreview()">✕</button>
            </div>
          </header>

          <div class="pv-body" :class="{ pdf: isPdf }">
            <div v-if="loading" class="pv-state">불러오는 중…</div>
            <div v-else-if="error" class="pv-state error">{{ error }}</div>

            <iframe v-else-if="isPdf" class="pv-frame" :src="rawUrl" :title="filename"></iframe>
            <pre v-else class="pv-text">{{ text }}</pre>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import { store } from '../store.js'
import { documentDownloadUrl, documentRawUrl, fetchDocumentText } from '../api/client.js'

const loading = ref(false)
const error = ref('')
const text = ref('')

const filename = computed(() => store.preview?.filename ?? '')
const ext = computed(() => {
  const m = /\.([^.]+)$/.exec(filename.value || '')
  return m ? m[1].toLowerCase() : ''
})
const isPdf = computed(() => ext.value === 'pdf')
const downloadUrl = computed(() => (store.preview ? documentDownloadUrl(store.preview.id) : '#'))
const rawUrl = computed(() => (store.preview ? documentRawUrl(store.preview.id) : ''))

// 미리보기가 열릴 때(혹은 대상이 바뀔 때) 텍스트 문서면 본문을 가져온다.
watch(
  () => store.preview?.id,
  async (id) => {
    error.value = ''
    text.value = ''
    if (id == null || isPdf.value) return
    loading.value = true
    try {
      text.value = await fetchDocumentText(id)
    } catch (e) {
      error.value = e.message || '미리보기를 불러오지 못했습니다.'
    } finally {
      loading.value = false
    }
  },
  { immediate: true },
)

function onKey(e) {
  if (e.key === 'Escape' && store.preview) store.closePreview()
}
onMounted(() => window.addEventListener('keydown', onKey))
onUnmounted(() => window.removeEventListener('keydown', onKey))
</script>

<style scoped>
.pv-back {
  position: fixed;
  inset: 0;
  z-index: 8000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 28px;
  background: rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(2px);
}

.pv-modal {
  display: flex;
  flex-direction: column;
  width: min(880px, 100%);
  height: min(86vh, 920px);
  background: var(--surface);
  border: 1px solid var(--line-strong);
  border-radius: var(--radius);
  box-shadow: var(--shadow-md);
  overflow: hidden;
}

.pv-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-bottom: 1px solid var(--line);
  background: var(--surface-2);
  flex-shrink: 0;
}
.pv-ext {
  font-family: var(--font-mono);
  font-size: 0.6rem;
  letter-spacing: 0.04em;
  color: var(--accent);
  background: var(--accent-soft);
  border-radius: 5px;
  padding: 2px 6px;
  flex-shrink: 0;
}
.pv-name {
  font-size: 0.86rem;
  font-weight: 600;
  color: var(--ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}
.pv-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
.pv-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.76rem;
  font-weight: 600;
  text-decoration: none;
  color: var(--accent);
  background: var(--accent-soft);
  border: 1px solid color-mix(in srgb, var(--accent) 30%, transparent);
  border-radius: var(--radius-sm);
  padding: 6px 11px;
  transition: background 0.16s;
}
.pv-btn:hover { background: color-mix(in srgb, var(--accent) 18%, transparent); }
.pv-close {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--ink-faint);
  font-size: 0.9rem;
  padding: 6px 8px;
  border-radius: var(--radius-sm);
  transition: color 0.16s, background 0.16s;
}
.pv-close:hover { color: var(--ink); background: var(--surface); }

.pv-body {
  flex: 1;
  min-height: 0;
  overflow: auto;
  background: var(--paper);
}
.pv-body.pdf { overflow: hidden; }

.pv-frame {
  width: 100%;
  height: 100%;
  border: none;
}

.pv-text {
  margin: 0;
  padding: 22px clamp(18px, 4vw, 36px);
  font-family: var(--font-mono);
  font-size: 0.82rem;
  line-height: 1.7;
  color: var(--ink);
  white-space: pre-wrap;
  word-break: break-word;
}

.pv-state {
  padding: 40px;
  text-align: center;
  font-size: 0.86rem;
  color: var(--ink-soft);
}
.pv-state.error { color: var(--danger); }

.pv-fade-enter-active,
.pv-fade-leave-active { transition: opacity 0.18s ease; }
.pv-fade-enter-from,
.pv-fade-leave-to { opacity: 0; }
</style>
