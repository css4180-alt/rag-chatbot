<template>
  <Teleport to="body">
    <div v-if="visible" class="t-back">
      <div :key="`spot-${curr}`" class="t-spotlight" :style="spotlightStyle" />
      <div :key="`bubble-${curr}`" ref="bubbleEl" class="t-bubble" :class="`side-${step.side}`" :style="bubbleStyle">
        <div class="t-badge">{{ curr + 1 }} / {{ STEPS.length }}</div>
        <p class="t-title">{{ step.title }}</p>
        <p class="t-text">{{ step.text }}</p>
        <div class="t-footer">
          <button class="t-skip" @click="finish">건너뛰기</button>
          <div class="t-dots">
            <span v-for="(_, i) in STEPS" :key="i" class="t-dot" :class="{ active: i === curr }" />
          </div>
          <button class="t-next" @click="advance">
            {{ curr < STEPS.length - 1 ? '다음 →' : '완료 ✓' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { store } from '../store.js'

const STEPS = [
  {
    target: 'tutorial-samples',
    side: 'top',  // 말풍선을 타겟 바로 위에 두고 아래로 향하는 화살표로 가리킴
    title: '샘플 문서 내려받기',
    text: '클릭하면 준비된 샘플 문서를 내려받을 수 있습니다. 업로드하면 바로 질문을 시작할 수 있어요.',
  },
  {
    target: 'tutorial-global-doc',
    side: 'left',
    title: '전역 문서 추가',
    text: '여기에 추가한 문서는 모든 대화에서 참조됩니다. PDF · Markdown · TXT를 지원합니다.',
  },
  {
    target: 'tutorial-session-doc',
    side: 'left',
    title: '대화 문서 추가',
    text: '여기에 추가한 문서는 현재 대화에서만 참조됩니다. 주제별로 문서를 구분할 수 있어요.',
  },
  {
    target: 'tutorial-input',
    side: 'top',
    title: '질문하기',
    text: '문서를 업로드했다면 이 입력창에 궁금한 점을 입력해보세요!',
  },
]

const PAD = 7        // 스포트라이트 여백 (px)
const BUBBLE_W = 260 // 말풍선 너비 (px)
const GAP = 20       // 스포트라이트 ↔ 말풍선 간격 (px)

const visible = ref(false)
const curr = ref(0)
const spotRect = ref(null)
const bubbleEl = ref(null)
const bubbleH = ref(168) // 실제 말풍선 높이(측정 전 기본값)

const step = computed(() => STEPS[curr.value])

async function updateRect() {
  const el = document.getElementById(STEPS[curr.value].target)
  spotRect.value = el ? el.getBoundingClientRect() : null
  // 말풍선 실제 높이를 측정해 타겟과의 간격을 정확히 맞춘다.
  await nextTick()
  if (bubbleEl.value) bubbleH.value = bubbleEl.value.offsetHeight
}

const spotlightStyle = computed(() => {
  const r = spotRect.value
  if (!r) return { opacity: 0 }
  return {
    top:    `${r.top  - PAD}px`,
    left:   `${r.left - PAD}px`,
    width:  `${r.width  + PAD * 2}px`,
    height: `${r.height + PAD * 2}px`,
  }
})

const bubbleStyle = computed(() => {
  const r = spotRect.value
  if (!r) return {}

  const sl = r.left - PAD
  const st = r.top  - PAD
  const sw = r.width  + PAD * 2
  const sh = r.height + PAD * 2

  let left, top

  switch (step.value.side) {
    case 'right':
      left = sl + sw + GAP
      top  = st + sh / 2 - bubbleH.value / 2
      break
    case 'left':
      left = sl - GAP - BUBBLE_W
      top  = st + sh / 2 - bubbleH.value / 2
      break
    case 'top':
      left = sl + sw / 2 - BUBBLE_W / 2
      top  = st - GAP - bubbleH.value
      break
    default:
      left = sl + sw / 2 - BUBBLE_W / 2
      top  = st + sh + GAP
  }

  // 화면 밖으로 나가지 않도록 보정
  const clampedLeft = Math.max(12, Math.min(left, window.innerWidth  - BUBBLE_W - 12))
  const clampedTop  = Math.max(12, Math.min(top,  window.innerHeight - 220))

  const style = { left: `${clampedLeft}px`, top: `${clampedTop}px`, width: `${BUBBLE_W}px` }

  // top/bottom 말풍선이 좌우로 밀렸을 때 아래/위 화살표가 타겟 중앙을 가리키도록 보정
  if (step.value.side === 'top' || step.value.side === 'bottom') {
    const spotCenterX = sl + sw / 2
    const arrowLeft = Math.max(16, Math.min(spotCenterX - clampedLeft, BUBBLE_W - 16))
    style['--arrow-left'] = `${arrowLeft}px`
  }

  return style
})

async function advance() {
  if (curr.value < STEPS.length - 1) {
    const nextIdx = curr.value + 1
    const el = document.getElementById(STEPS[nextIdx].target)
    // curr과 spotRect을 같은 틱에 동시에 업데이트 → Vue가 한 번에 렌더링해 깜빡임 없음
    spotRect.value = el ? el.getBoundingClientRect() : null
    curr.value = nextIdx
    await nextTick()
    if (bubbleEl.value) bubbleH.value = bubbleEl.value.offsetHeight
  } else {
    finish()
  }
}

function finish() {
  visible.value = false
}

function onResize() { updateRect() }

onMounted(async () => {
  window.addEventListener('resize', onResize)
  // 세션 복원(새로고침)이 아닌 실제 로그인 직후에만 튜토리얼을 표시한다.
  if (store.freshLogin) {
    await new Promise(r => setTimeout(r, 450))
    curr.value = 0
    visible.value = true
    await nextTick()
    updateRect()
  }
})

onUnmounted(() => window.removeEventListener('resize', onResize))
</script>

<style scoped>
.t-back {
  position: fixed;
  inset: 0;
  z-index: 9000;
  cursor: default;
}

/* 스포트라이트: box-shadow로 배경을 어둡게, 하이라이트 링 추가 */
.t-spotlight {
  position: absolute;
  border-radius: 9px;
  box-shadow:
    0 0 0 9999px rgba(0, 0, 0, 0.68),
    0 0 0 2px var(--accent);
  pointer-events: none;
  z-index: 1;
}

/* 말풍선 */
.t-bubble {
  position: absolute;
  z-index: 2;
  width: 260px;
  background: var(--surface);
  border: 1px solid var(--line-strong);
  border-radius: var(--radius);
  padding: 16px 18px 13px;
  box-shadow: var(--shadow-md);
  cursor: default;
  animation: t-back-in 0.22s ease both;
}

/* 말풍선 화살표 공통 */
.t-bubble::before,
.t-bubble::after {
  content: '';
  position: absolute;
  width: 0;
  height: 0;
}

/* side-right: 말풍선이 오른쪽, 화살표는 왼쪽 중앙 */
.t-bubble.side-right::before {
  top: 50%; right: 100%;
  transform: translateY(-50%);
  border: 9px solid transparent;
  border-right-color: var(--line-strong);
}
.t-bubble.side-right::after {
  top: 50%; right: calc(100% - 1px);
  transform: translateY(calc(-50% + 1px));
  border: 8px solid transparent;
  border-right-color: var(--surface);
}

/* side-left: 말풍선이 왼쪽, 화살표는 오른쪽 중앙 */
.t-bubble.side-left::before {
  top: 50%; left: 100%;
  transform: translateY(-50%);
  border: 9px solid transparent;
  border-left-color: var(--line-strong);
}
.t-bubble.side-left::after {
  top: 50%; left: calc(100% - 1px);
  transform: translateY(calc(-50% + 1px));
  border: 8px solid transparent;
  border-left-color: var(--surface);
}

/* side-top: 말풍선이 위쪽, 화살표는 아래쪽 */
.t-bubble.side-top::before {
  top: 100%; left: var(--arrow-left, 50%);
  transform: translateX(-50%);
  border: 9px solid transparent;
  border-top-color: var(--line-strong);
}
.t-bubble.side-top::after {
  top: calc(100% - 1px); left: var(--arrow-left, 50%);
  transform: translateX(-50%);
  border: 8px solid transparent;
  border-top-color: var(--surface);
}

.t-badge {
  font-family: var(--font-mono);
  font-size: 0.62rem;
  letter-spacing: 0.08em;
  color: var(--accent);
  margin-bottom: 6px;
}

.t-title {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--ink);
  margin-bottom: 7px;
  line-height: 1.3;
}

.t-text {
  font-size: 0.8rem;
  color: var(--ink-soft);
  line-height: 1.6;
  margin-bottom: 14px;
}

.t-footer {
  display: flex;
  align-items: center;
  gap: 8px;
}

.t-skip {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  color: var(--ink-faint);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  transition: color 0.15s;
}
.t-skip:hover { color: var(--ink-soft); }

.t-dots {
  display: flex;
  gap: 4px;
  flex: 1;
  justify-content: center;
}
.t-dot {
  width: 5px;
  height: 5px;
  border-radius: 99px;
  background: var(--line-strong);
  transition: background 0.2s, width 0.2s;
}
.t-dot.active {
  width: 14px;
  background: var(--accent);
}

.t-next {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--accent-ink);
  background: var(--accent);
  border: none;
  border-radius: var(--radius-sm);
  padding: 7px 13px;
  cursor: pointer;
  transition: background 0.16s, transform 0.08s;
}
.t-next:hover { background: var(--accent-strong); }
.t-next:active { transform: scale(0.97); }

@keyframes t-back-in {
  from { opacity: 0; transform: scale(0.97); }
  to   { opacity: 1; transform: scale(1); }
}
</style>
