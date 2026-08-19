<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    value: number
    sign?: 'auto' | 'none' | 'always'
    size?: 'sm' | 'md' | 'lg' | 'xl'
    suffix?: string
  }>(),
  { sign: 'auto', size: 'md', suffix: '' },
)

const formatted = computed(() => {
  const abs = Math.abs(props.value)
  const str = abs.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  if (props.value < 0) return `-${str}`
  if (props.sign === 'always' && props.value > 0) return `+${str}`
  return str
})

// 中国习惯：红 = 赚（正），绿 = 亏（负）
const colorClass = computed(() => {
  if (props.sign === 'none') return 'text-ink'
  if (props.value > 0) return 'text-gain'
  if (props.value < 0) return 'text-neon-bright'
  return 'text-sub'
})

const sizeClass = computed(
  () =>
    ({
      sm: 'text-sm',
      md: 'text-lg',
      lg: 'text-2xl',
      xl: 'text-4xl md:text-5xl',
    })[props.size],
)
</script>

<template>
  <span class="num font-semibold tracking-tight" :class="[colorClass, sizeClass]">
    {{ formatted }}<span v-if="suffix" class="ml-1 text-[0.55em] font-normal text-mute">{{ suffix }}</span>
  </span>
</template>
