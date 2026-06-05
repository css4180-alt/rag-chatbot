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
        <input
          v-if="editingId === s.id"
          ref="editInput"
          v-model="editText"
          class="conv-edit"
          @click.stop
          @keydown.enter.prevent="onEnter($event, s)"
          @keydown.esc.prevent="cancelRename"
          @blur="commitRename(s)"
        />
        <span v-else class="conv-title" @dblclick.stop="startRename(s)">{{ s.title || '새 대화' }}</span>
        <span class="conv-time">{{ relTime(s.last_message_at) }}</span>
        <span class="conv-actions">
          <button class="conv-edit-btn" title="제목 수정" @click.stop="startRename(s)">✎</button>
          <button class="conv-del" title="대화 삭제" @click.stop="confirmDelete(s)">✕</button>
        </span>
      </li>
    </ul>
    <div v-else class="conv-empty">
      <p>아직 대화가 없습니다.</p>
      <p class="muted">질문을 보내면 대화가 저장됩니다.</p>
    </div>

    <!-- 샘플 문서 (하단 고정) -->
    <div class="samples-drawer">
      <button id="tutorial-samples" class="samples-toggle" @click="showSamples = !showSamples">
        <span>샘플 문서 내려받기</span>
        <span class="samples-chevron" :class="{ open: showSamples }">▾</span>
      </button>
      <ul v-if="showSamples" class="samples-list">
        <li v-for="s in samples" :key="s.file">
          <a class="sample-item" :href="`/samples/${s.file}`" :download="s.file">
            <span class="sample-dl" aria-hidden="true">↓</span>
            <span class="sample-text">
              <span class="sample-name">{{ s.name }}</span>
              <small class="sample-desc">{{ s.desc }}</small>
            </span>
            <span class="sample-ext">{{ s.ext }}</span>
          </a>
        </li>
      </ul>
    </div>
  </aside>
</template>

<script setup>
import { nextTick, ref } from 'vue'
import { store } from '../store.js'

const editingId = ref(null)
const editText = ref('')
const editInput = ref(null)

const showSamples = ref(false)
const samples = [
  { file: '루미나 X100 카메라 설명서.txt', name: '루미나 X100 카메라 설명서', desc: '미러리스 카메라 매뉴얼', ext: 'TXT' },
  { file: '오빗모빌리티 서비스 안내.md',   name: '오빗모빌리티 서비스 안내', desc: '전동 스쿠터 공유 서비스', ext: 'MD'  },
  { file: '스텔라뱅크 FAQ.md',             name: '스텔라뱅크 FAQ',           desc: '인터넷전문은행 안내',    ext: 'MD'  },
  { file: '가든카페 운영 핸드북.pdf',       name: '가든카페 운영 핸드북',     desc: '카페 운영 가이드',       ext: 'PDF' },
]

async function startRename(s) {
  editingId.value = s.id
  editText.value = s.title || ''
  await nextTick()
  // v-for 안의 ref 는 배열로 모일 수 있어 첫 요소를 집어 포커스/전체선택.
  const el = Array.isArray(editInput.value) ? editInput.value[0] : editInput.value
  el?.focus()
  el?.select()
}

function cancelRename() {
  editingId.value = null
  editText.value = ''
}

// 한글 등 IME 조합 중에 눌린 Enter 는 글자 확정용이므로 저장하지 않는다.
// (그대로 저장하면 조합 중이던 마지막 글자가 빠진 채로 저장된다.)
function onEnter(e, s) {
  if (e.isComposing || e.keyCode === 229) return
  commitRename(s)
}

async function commitRename(s) {
  if (editingId.value !== s.id) return
  const next = editText.value.trim()
  editingId.value = null
  // 비었거나 변동 없으면 무시.
  if (!next || next === (s.title || '')) return
  try {
    await store.renameSession(s.id, next)
  } catch (e) {
    alert(e.message || '제목 수정에 실패했습니다.')
  }
}

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
  width: 245px;
  min-width: 245px;
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
  grid-template-areas: 'title actions' 'time actions';
  align-items: center;
  gap: 0 6px;
  padding: 9px 10px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  border: 1px solid transparent;
  transition: background 0.14s, border-color 0.14s;
}
.conv-item:hover { background: var(--surface-2); }
.conv-item:hover .conv-actions { opacity: 1; }
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
.conv-actions {
  grid-area: actions;
  display: inline-flex;
  align-items: center;
  gap: 2px;
  opacity: 0;
  transition: opacity 0.14s;
}
.conv-item.active .conv-actions { opacity: 1; }
.conv-edit-btn,
.conv-del {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--ink-faint);
  font-size: 0.72rem;
  padding: 4px;
  border-radius: 5px;
  transition: color 0.14s, background 0.14s;
}
.conv-edit-btn:hover { color: var(--accent); background: var(--surface); }
.conv-del:hover { color: var(--danger); background: var(--surface); }

.conv-edit {
  grid-area: title;
  width: 100%;
  font-size: 0.84rem;
  font-weight: 600;
  color: var(--ink);
  background: var(--paper);
  border: 1px solid var(--accent);
  border-radius: 5px;
  padding: 2px 6px;
  outline: none;
}
.conv-edit:focus { box-shadow: 0 0 0 2px var(--accent-soft); }

.conv-empty {
  margin-top: 12px;
  padding: 0 4px;
  font-size: 0.8rem;
  color: var(--ink-soft);
}
.conv-empty .muted { color: var(--ink-faint); font-size: 0.74rem; margin-top: 4px; }

/* 샘플 문서 드로어 */
.samples-drawer {
  margin-top: auto;
  padding-top: 10px;
  border-top: 1px solid var(--line);
}
.samples-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 8px 6px;
  background: none;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-family: var(--font-mono);
  font-size: 0.66rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--ink-faint);
  transition: background 0.14s, color 0.14s;
}
.samples-toggle:hover { background: var(--surface-2); color: var(--ink-soft); }
.samples-chevron { transition: transform 0.2s; }
.samples-chevron.open { transform: rotate(180deg); }

.samples-list {
  list-style: none;
  margin: 6px 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.sample-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 8px;
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  background: var(--paper);
  text-decoration: none;
  color: var(--ink);
  transition: border-color 0.16s, background 0.16s;
}
.sample-item:hover { border-color: var(--accent); background: var(--accent-soft); }
.sample-dl {
  flex-shrink: 0;
  display: grid;
  place-items: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 0.75rem;
  font-weight: 700;
}
.sample-text {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
  flex: 1;
}
.sample-name {
  font-size: 0.76rem;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.sample-desc {
  font-size: 0.64rem;
  color: var(--ink-faint);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.sample-ext {
  flex-shrink: 0;
  font-family: var(--font-mono);
  font-size: 0.56rem;
  letter-spacing: 0.04em;
  color: var(--ink-faint);
  border: 1px solid var(--line-strong);
  border-radius: 4px;
  padding: 1px 4px;
}
</style>
