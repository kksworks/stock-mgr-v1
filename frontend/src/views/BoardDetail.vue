<template>
  <div class="board-detail-container py-4">
    <div class="card border-0 shadow-sm max-width-container mx-auto">
      <div v-if="loading" class="card-body p-5 text-center">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-3 text-muted">게시물을 불러오는 중입니다...</p>
      </div>

      <div v-else-if="error" class="card-body p-5 text-center text-danger">
        <MaterialIcon name="error_outline" size="3rem" />
        <h2 class="h5 mt-3">{{ error }}</h2>
        <button class="btn btn-outline-primary mt-3" @click="router.push('/site-guide')">
          목록으로 돌아가기
        </button>
      </div>

      <div v-else-if="post" class="card-body p-4 p-md-5">
        <!-- 상단 내비게이션 -->
        <div class="d-flex align-items-center justify-content-between mb-4">
          <button class="btn btn-link text-decoration-none p-0 d-flex align-items-center gap-1" @click="router.push('/site-guide')">
            <MaterialIcon name="arrow_back" size="1.2rem" />
            <span>목록으로</span>
          </button>

          <div v-if="authStore.isAdmin" class="d-flex gap-2">
            <button class="btn btn-sm btn-outline-secondary d-flex align-items-center gap-1" @click="isEditing = true">
              <MaterialIcon name="edit" size="1rem" />
              수정
            </button>
            <button class="btn btn-sm btn-outline-danger d-flex align-items-center gap-1" @click="confirmDelete">
              <MaterialIcon name="delete" size="1rem" />
              삭제
            </button>
          </div>
        </div>

        <!-- 게시물 헤더 -->
        <header class="mb-4 pb-4 border-bottom">
          <div class="d-flex align-items-center gap-2 mb-2">
            <span v-if="post.pinned" class="badge bg-danger d-flex align-items-center gap-1">
              <MaterialIcon name="push_pin" size="0.8rem" />
              고정됨
            </span>
          </div>
          <h1 class="h3 fw-bold mb-3">{{ post.title }}</h1>
          <div class="d-flex flex-wrap align-items-center gap-3 text-muted small">
            <div class="d-flex align-items-center gap-1">
              <MaterialIcon name="person" size="1rem" />
              <span>{{ post.author_name || '관리자' }}</span>
            </div>
            <div class="d-flex align-items-center gap-1">
              <MaterialIcon name="schedule" size="1rem" />
              <span>{{ formatDate(post.created_at) }}</span>
            </div>
          </div>
        </header>

        <!-- 게시물 본문 (마크다운) -->
        <article class="post-content mb-5" v-html="renderedContent"></article>

        <!-- 하단 액션 (관리자 전용) -->
        <div v-if="authStore.isAdmin" class="mt-5 pt-4 border-top d-flex justify-content-center">
          <button 
            class="btn btn-outline-secondary d-flex align-items-center gap-2" 
            @click="handleTogglePin"
            :disabled="togglingPin"
          >
            <MaterialIcon :name="post.pinned ? 'push_pin' : 'push_pin'" :class="post.pinned ? 'text-primary' : 'text-muted'" size="1.2rem" />
            <span>{{ post.pinned ? '고정 해제' : '상단 고정' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 수정 모달/컴포넌트 (간단히 인라인 처리) -->
    <div v-if="isEditing" class="modal-backdrop-custom d-flex align-items-center justify-content-center p-3">
      <div class="card shadow-lg border-0 w-100 max-width-container">
        <div class="card-header bg-white border-0 p-4 pb-0">
          <h5 class="mb-0">게시물 수정</h5>
        </div>
        <div class="card-body p-4">
          <div class="mb-3">
            <label class="form-label fw-bold">제목</label>
            <input v-model="editingPost.title" type="text" class="form-control" />
          </div>
          <div class="mb-3">
            <label class="form-label fw-bold">내용 (마크다운)</label>
            <textarea v-model="editingPost.content" class="form-control editor-textarea" rows="12"></textarea>
          </div>
          <div class="form-check mb-4">
            <input v-model="editingPost.pinned" class="form-check-input" type="checkbox" id="edit-pinned" />
            <label class="form-check-label" for="edit-pinned">상단 고정</label>
          </div>
          <div class="d-flex justify-content-end gap-2">
            <button class="btn btn-outline-secondary" @click="isEditing = false">취소</button>
            <button class="btn btn-primary" :disabled="saving" @click="handleUpdate">
              {{ saving ? '저장 중...' : '저장하기' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import MaterialIcon from '../components/MaterialIcon.vue'
import { boardApi, getApiErrorMessage } from '../api'
import { authStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const postId = route.params.postId

const post = ref(null)
const loading = ref(true)
const error = ref('')
const isEditing = ref(false)
const saving = ref(false)
const togglingPin = ref(false)
const editingPost = ref({ title: '', content: '', pinned: false })

// 마크다운 렌더링
const renderedContent = computed(() => {
  if (!post.value || !post.value.content) return ''
  const rawHtml = marked.parse(post.value.content)
  return DOMPurify.sanitize(rawHtml)
})

marked.setOptions({
  breaks: true,
  gfm: true
})

async function fetchPost() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await boardApi.getPost(postId)
    post.value = data
    editingPost.value = { 
      title: data.title, 
      content: data.content, 
      pinned: data.pinned 
    }
  } catch (e) {
    error.value = getApiErrorMessage(e, '게시물을 불러오지 못했습니다.')
  } finally {
    loading.value = false
  }
}

async function handleUpdate() {
  if (!editingPost.value.title || !editingPost.value.content) return
  
  saving.value = true
  try {
    await boardApi.updatePost(postId, editingPost.value)
    isEditing.value = false
    await fetchPost()
  } catch (e) {
    alert(getApiErrorMessage(e, '수정에 실패했습니다.'))
  } finally {
    saving.value = false
  }
}

async function handleTogglePin() {
  togglingPin.value = true
  try {
    await boardApi.togglePin(postId)
    await fetchPost()
  } catch (e) {
    alert(getApiErrorMessage(e, '고정 상태 변경에 실패했습니다.'))
  } finally {
    togglingPin.value = false
  }
}

async function confirmDelete() {
  if (!confirm('정말로 이 게시물을 삭제하시겠습니까?')) return
  
  try {
    await boardApi.deletePost(postId)
    router.push('/site-guide')
  } catch (e) {
    alert(getApiErrorMessage(e, '삭제에 실패했습니다.'))
  }
}

function formatDate(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  fetchPost()
})
</script>

<style scoped>
.max-width-container {
  max-width: 800px;
}

.post-content :deep(h1), 
.post-content :deep(h2), 
.post-content :deep(h3) {
  margin-top: 2rem;
  margin-bottom: 1rem;
}

.post-content :deep(p) {
  line-height: 1.6;
  margin-bottom: 1.25rem;
}

.post-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  margin: 1.5rem 0;
}

.modal-backdrop-custom {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1050;
  backdrop-filter: blur(2px);
}

.editor-textarea {
  font-size: 0.9rem;
  line-height: 1.5;
}

.card {
  border-radius: 12px;
}
</style>
