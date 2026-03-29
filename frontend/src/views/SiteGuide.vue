<template>
  <section class="site-guide-page py-2 py-md-3">
    <div class="card border-0 shadow-sm">
      <div class="card-body p-3 p-md-4">
        <!-- 페이지 제목 -->
        <div class="d-flex align-items-center justify-content-between flex-wrap gap-2 mb-3">
          <div class="d-flex align-items-center gap-2">
            <MaterialIcon name="announcement" class="text-primary" size="1.35rem" />
            <h1 class="h5 mb-0">게시판</h1>
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
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import MaterialIcon from '../components/MaterialIcon.vue'
import { boardApi, getApiErrorMessage } from '../api'
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

onMounted(() => {
  loadPosts(1)
})
</script>

<style scoped>
.site-guide-page {
  max-width: 880px;
  margin: 0 auto;
}

.board-editor {
  min-height: 280px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
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
