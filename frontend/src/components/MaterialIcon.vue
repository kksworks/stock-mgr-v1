<template>
  <span
    class="material-symbols-outlined ms-fin-icon"
    :class="iconClass"
    :style="iconStyle"
    aria-hidden="true"
  >{{ name }}</span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  /** Material Symbols 이름 (예: payments, trending_up) */
  name: { type: String, required: true },
  /** CSS font-size (예: 1.25rem, 2rem, 20px) */
  size: { type: String, default: '1.25rem' },
  /** 추가 클래스 */
  iconClass: { type: [String, Object, Array], default: '' },
  /** 채우기 여부 (Material Symbols FILL 변수) */
  fill: { type: Boolean, default: false },
  /** 굵기 (Material Symbols wght 변수: 100-700) */
  weight: { type: [Number, String], default: 400 },
})

const iconStyle = computed(() => ({
  fontSize: props.size,
  fontVariationSettings: `'FILL' ${props.fill ? 1 : 0}, 'wght' ${props.weight}, 'GRAD' 0, 'opsz' 24`
}))
</script>
