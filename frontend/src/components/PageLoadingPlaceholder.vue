<template>
  <div class="placeholder-wrap card border-0 shadow-sm">
    <div class="card-body">
      <div class="placeholder-title skeleton-line mb-3"></div>
      <template v-if="variant === 'table'">
        <div class="skeleton-line mb-2" style="height: 14px; width: 95%;"></div>
        <div v-for="i in rows" :key="`table-${i}`" class="skeleton-line mb-2"></div>
      </template>
      <template v-else-if="variant === 'cards'">
        <div class="row g-3">
          <div v-for="i in rows" :key="`card-${i}`" class="col-12 col-md-6">
            <div class="skeleton-box"></div>
          </div>
        </div>
      </template>
      <template v-else>
        <div v-for="i in rows" :key="`line-${i}`" class="skeleton-line mb-2"></div>
      </template>
    </div>
  </div>
</template>

<script setup>
defineProps({
  variant: { type: String, default: 'table' }, // table | cards | lines
  rows: { type: Number, default: 6 },
})
</script>

<style scoped>
.placeholder-title {
  width: 32%;
  height: 20px;
}

.skeleton-line,
.skeleton-box {
  position: relative;
  overflow: hidden;
  background: #e9ecef;
  border-radius: 8px;
}

.skeleton-line {
  height: 12px;
  width: 100%;
}

.skeleton-box {
  height: 74px;
}

.skeleton-line::after,
.skeleton-box::after {
  content: '';
  position: absolute;
  inset: 0;
  transform: translateX(-100%);
  background: linear-gradient(90deg, rgba(255, 255, 255, 0) 0%, rgba(255, 255, 255, 0.72) 50%, rgba(255, 255, 255, 0) 100%);
  animation: shimmer 1.2s infinite;
}

@keyframes shimmer {
  100% { transform: translateX(100%); }
}

:root[data-theme="dark"] .skeleton-line,
:root[data-theme="dark"] .skeleton-box {
  background: var(--ui-surface-soft, #1a253b);
}

:root[data-theme="dark"] .skeleton-line::after,
:root[data-theme="dark"] .skeleton-box::after {
  background: linear-gradient(90deg, rgba(255, 255, 255, 0) 0%, rgba(255, 255, 255, 0.05) 50%, rgba(255, 255, 255, 0) 100%);
}
</style>
