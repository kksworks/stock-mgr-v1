<template>
  <section class="site-guide-page py-2 py-md-3">
    <div class="card border-0 shadow-sm">
      <div class="card-body p-3 p-md-4">
        <!-- 사이트 소개 섹션 -->
        <div class="site-intro-section mb-5">
          <div class="d-flex align-items-center gap-3 mb-3">
            <img src="/logo.png" alt="GrowMore Logo" class="site-intro-logo" />
          </div>
          <div class="intro-text-card p-3 p-md-4 rounded-3 bg-light border-0">
            <h2 class="h5 fw-bold mb-3 text-dark">GrowMore에 오신 것을 환영합니다</h2>
            <p class="text-secondary mb-0 lh-lg">
              <strong>GrowMore</strong>는 스마트한 투자 결정을 지원하는 주식 포트폴리오 관리 플랫폼입니다. <br class="d-none d-md-block" />
              실시간 시세 조회, 계좌 잔고 추적, 그리고 목표 비중에 맞춘 포트폴리오 재배정 기능을 통해 체계적인 자산 관리를 도와드립니다. 
              안정적이고 효율적인 투자 여정을 GrowMore와 함께 시작해 보세요.
            </p>
            
            <!-- 시스템 정보 섹션 -->
            <div v-if="siteVersion || siteBuildDate" class="mt-4 pt-3 border-top border-light">
              <div class="d-flex flex-wrap gap-3">
                <div class="system-info-item">
                  <span class="text-muted small fw-bold text-uppercase d-block mb-1" style="letter-spacing: 0.05em; font-size: 0.65rem;">System Version</span>
                  <div class="d-flex align-items-center gap-2">
                    <MaterialIcon name="commit" size="1.1rem" class="text-primary opacity-75" />
                    <span class="mono-text fw-bold text-dark" style="font-size: 0.95rem;">{{ siteVersion || '-' }}</span>
                  </div>
                </div>
                <div class="system-info-item ps-3 border-start border-light">
                  <span class="text-muted small fw-bold text-uppercase d-block mb-1" style="letter-spacing: 0.05em; font-size: 0.65rem;">Last Build Date</span>
                  <div class="d-flex align-items-center gap-2">
                    <MaterialIcon name="event_available" size="1.1rem" class="text-success opacity-75" />
                    <span class="text-secondary fw-medium" style="font-size: 0.9rem;">{{ siteBuildDate || '-' }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 게시판 제목 -->
        <div class="d-flex align-items-center justify-content-between flex-wrap gap-2 mb-3 border-bottom pb-2">
          <div class="d-flex align-items-center gap-2">
            <MaterialIcon name="announcement" class="text-primary" size="1.35rem" />
            <h1 class="h5 mb-0 fw-bold">공지사항 및 안내</h1>
          </div>
        </div>

        <!-- 게시판 -->
          <!-- 관리자용 작성 버튼 -->
          <div class="d-flex align-items-center justify-content-between flex-wrap gap-2 mb-3">
            <div></div>
            <div v-if="authStore.isAdmin" class="d-flex gap-2">
              <button
                v-if="!isBoardEditing"
                type="button"
                class="btn btn-sm btn-primary d-inline-flex align-items-center gap-1"
                @click="openNewPostEditor"
              >
                <MaterialIcon name="add" size="1rem" />
                새 게시물 작성
              </button>
            </div>
          </div>

          <!-- 게시물 작성/수정 에디터 -->
          <div v-if="isBoardEditing" class="card bg-light mb-3">
            <div class="card-body">
              <div class="d-flex align-items-center justify-content-between mb-3">
                <h3 class="h6 mb-0">새 게시물 작성</h3>
                <button
                  type="button"
                  class="btn-close"
                  @click="closeBoardEditor"
                  aria-label="Close"
                ></button>
              </div>

              <div class="mb-3">
                <label class="form-label fw-semibold">제목</label>
                <input
                  v-model="editingPost.title"
                  type="text"
                  class="form-control"
                  placeholder="게시물 제목을 입력하세요"
                />
              </div>

              <div class="mb-3">
                <label class="form-label fw-semibold">내용 (마크다운)</label>
                <textarea
                  v-model="editingPost.content"
                  class="form-control board-editor"
                  placeholder="게시물 내용을 마크다운 형식으로 작성하세요&#10;&#10;# 제목&#10;## 부제목&#10;&#10;**굵은 텍스트**, *기울인 텍스트*&#10;&#10;- 리스트&#10;- 리스트 항목"
                ></textarea>
              </div>

              <div class="mb-3 form-check">
                <input
                  v-model="editingPost.pinned"
                  type="checkbox"
                  class="form-check-input"
                  id="pinned-new"
                />
                <label class="form-check-label" for="pinned-new">
                  이 게시물을 상단에 고정합니다
                </label>
              </div>

              <div class="d-flex gap-2 justify-content-end">
                <button
                  type="button"
                  class="btn btn-sm btn-outline-secondary"
                  :disabled="savingPost"
                  @click="closeBoardEditor"
                >
                  취소
                </button>
                <button
                  type="button"
                  class="btn btn-sm btn-primary"
                  :disabled="savingPost || !editingPost.title || !editingPost.content"
                  @click="savePost"
                >
                  {{ savingPost ? '저장 중...' : '저장' }}
                </button>
              </div>
            </div>
          </div>

          <!-- 게시물 목록 -->
          <div v-if="boardLoading" class="d-flex align-items-center gap-2 text-muted">
            <span class="spinner-border spinner-border-sm text-primary" role="status" aria-hidden="true"></span>
            게시물을 불러오는 중입니다...
          </div>

          <div v-else-if="boardError" class="alert alert-danger mb-0" role="alert">
            {{ boardError }}
          </div>

          <div v-else-if="posts.length === 0" class="alert alert-info mb-0" role="alert">
            게시물이 없습니다.
          </div>

          <div v-else class="board-list">
            <!-- 게시물 항목 -->
            <div v-for="post in posts" :key="post.id" class="board-item card mb-2 cursor-pointer transition-all" @click="router.push(`/board/${post.id}`)">
              <div class="card-body p-3">
                <div class="d-flex align-items-start gap-2 mb-2">
                  <div v-if="post.pinned" class="badge bg-danger flex-shrink-0">
                    <MaterialIcon name="push_pin" size="0.8rem" />
                    고정
                  </div>
                  <h5 class="card-title mb-0 flex-grow-1">{{ post.title }}</h5>
                </div>
                <p class="card-text small text-muted mb-0">
                  {{ formatDate(post.created_at) }}
                </p>
              </div>
            </div>
          </div>

          <!-- 페이지네이션 -->
          <nav v-if="totalPages > 1" class="mt-4">
            <ul class="pagination pagination-sm justify-content-center mb-0">
              <li class="page-item" :class="{ disabled: currentPage === 1 }">
                <button
                  type="button"
                  class="page-link"
                  @click="loadPosts(1)"
                  :disabled="currentPage === 1"
                >
                  처음
                </button>
              </li>
              <li
                v-for="page in visiblePages"
                :key="page"
                class="page-item"
                :class="{ active: page === currentPage }"
              >
                <button
                  type="button"
                  class="page-link"
                  @click="loadPosts(page)"
                  :class="{ active: page === currentPage }"
                >
                  {{ page }}
                </button>
              </li>
              <li class="page-item" :class="{ disabled: currentPage === totalPages }">
                <button
                  type="button"
                  class="page-link"
                  @click="loadPosts(totalPages)"
                  :disabled="currentPage === totalPages"
                >
                  끝
                </button>
              </li>
            </ul>
          </nav>

          <div v-if="boardToastMessage" :class="['alert', 'py-2', 'small', 'mt-3', boardToastType === 'success' ? 'alert-success' : 'alert-danger']" role="alert">
            {{ boardToastMessage }}
          </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import MaterialIcon from '../components/MaterialIcon.vue'
import { boardApi, systemApi, getApiErrorMessage } from '../api'
import { authStore } from '../stores/auth'

const router = useRouter()

// 게시판 섹션
const boardLoading = ref(false)
const boardError = ref('')
const savingPost = ref(false)
const boardToastMessage = ref('')
const boardToastType = ref('success')
const posts = ref([])
const currentPage = ref(1)
const totalPages = ref(1)
const isBoardEditing = ref(false)
const editingPost = ref({ title: '', content: '', pinned: false })
const siteVersion = ref('')
const siteBuildDate = ref('')
let boardToastTimer = null

watch(boardToastMessage, (newVal) => {
  if (newVal) {
    if (boardToastTimer) clearTimeout(boardToastTimer)
    boardToastTimer = setTimeout(() => {
      boardToastMessage.value = ''
    }, 5000)
  }
})

marked.setOptions({
  breaks: true,
  gfm: true,
})

const visiblePages = computed(() => {
  const pages = []
  const maxPages = Math.min(5, totalPages.value)
  let startPage = Math.max(1, currentPage.value - Math.floor(maxPages / 2))
  const endPage = Math.min(totalPages.value, startPage + maxPages - 1)
  startPage = Math.max(1, endPage - maxPages + 1)

  for (let i = startPage; i <= endPage; i++) {
    pages.push(i)
  }
  return pages
})

// 게시판 함수
async function loadPosts(page = 1) {
  boardLoading.value = true
  boardError.value = ''
  try {
    const { data } = await boardApi.listPosts(page)
    posts.value = data.posts || []
    currentPage.value = data.page || 1
    totalPages.value = data.total_pages || 1
  } catch (error) {
    boardError.value = getApiErrorMessage(error, '게시물을 불러오지 못했습니다.')
  } finally {
    boardLoading.value = false
  }
}

function formatDate(dateString) {
  if (!dateString) return ''
  try {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now - date
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffDays === 0) {
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
      if (diffHours === 0) return '방금 전'
      return `${diffHours}시간 전`
    } else if (diffDays < 7) {
      return `${diffDays}일 전`
    }

    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    })
  } catch {
    return dateString
  }
}

function openNewPostEditor() {
  isBoardEditing.value = true
  editingPost.value = { title: '', content: '', pinned: false }
  boardToastMessage.value = ''
}

function closeBoardEditor() {
  isBoardEditing.value = false
  editingPost.value = { title: '', content: '', pinned: false }
}

async function savePost() {
  savingPost.value = true
  try {
    const payload = {
      title: editingPost.value.title,
      content: editingPost.value.content,
      pinned: editingPost.value.pinned,
    }

    await boardApi.createPost(payload)
    boardToastType.value = 'success'
    boardToastMessage.value = '게시물이 작성되었습니다.'

    closeBoardEditor()
    await loadPosts(1)
  } catch (error) {
    boardToastType.value = 'danger'
    boardToastMessage.value = getApiErrorMessage(error, '게시물 저장에 실패했습니다.')
  } finally {
    savingPost.value = false
  }
}

async function loadSiteInfo() {
  try {
    const { data } = await systemApi.getSiteGuide()
    siteVersion.value = data.version || ''
    siteBuildDate.value = data.build_date || ''
  } catch (e) {
    console.warn('Failed to load site info:', e)
  }
}

onMounted(() => {
  loadPosts(1)
  loadSiteInfo()
})
</script>

<style scoped>
.site-intro-section {
  border-bottom: 0px;
}

.site-intro-logo {
  height: 2.25rem;
  width: auto;
}

.intro-text-card {
  font-size: 1rem;
  background-color: var(--ui-surface-soft) !important;
  color: var(--ui-text) !important;
}

[data-theme='dark'] .intro-text-card h2 {
  color: white !important;
}

.mono-text {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

.system-info-item {
  min-width: 120px;
}

.site-guide-page {
  max-width: 880px;
  margin: 0 auto;
}

.board-editor {
  min-height: 280px;
  font-size: 0.95rem;
  line-height: 1.5;
}

.board-item {
  cursor: pointer;
}

.board-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.board-item.transition-all {
  transition: all 0.2s ease;
}

.min-width-0 {
  min-width: 0;
}
</style>
