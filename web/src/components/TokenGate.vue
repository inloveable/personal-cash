<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { KeyRound, Zap } from 'lucide-vue-next'

const emit = defineEmits<{ submit: [token: string] }>()
const token = ref('')
const inputRef = ref<HTMLInputElement | null>(null)

function submit() {
  const t = token.value.trim()
  if (t) emit('submit', t)
}

function quickFill() {
  token.value = 'dev-token'
  submit()
}

onMounted(() => {
  inputRef.value?.focus()
})
</script>

<template>
  <div class="flex min-h-screen items-center justify-center px-4">
    <div class="term-card-glow scanline w-full max-w-sm p-8 rise-in">
      <div class="term-label mb-2">// access_required</div>
      <h1 class="mb-1 font-mono text-xl font-bold text-neon-bright">
        $ auth --token<span class="blink text-neon">▌</span>
      </h1>
      <p class="mb-6 text-sm text-sub">输入访问令牌进入你的现金流终端。本地开发默认 dev-token。</p>

      <form class="flex gap-2" @submit.prevent="submit">
        <div class="flex flex-1 items-center gap-2 rounded-md border border-line bg-raise px-3 transition-colors focus-within:border-neon focus-within:shadow-glow">
          <KeyRound :size="15" class="shrink-0 text-mute" />
          <input
            ref="inputRef"
            v-model="token"
            type="text"
            autocomplete="off"
            spellcheck="false"
            placeholder="API_TOKEN"
            class="h-11 w-full border-none bg-transparent font-mono text-sm text-ink placeholder-mute outline-none"
          />
        </div>
        <button
          type="submit"
          :disabled="!token.trim()"
          class="cursor-pointer rounded-md border border-neon bg-neon px-4 font-medium text-void transition-all hover:bg-neon-bright disabled:cursor-not-allowed disabled:border-line disabled:bg-raise disabled:text-mute"
        >
          进入
        </button>
      </form>

      <button
        class="mt-3 flex cursor-pointer items-center gap-1 font-mono text-[11px] text-mute transition-colors hover:text-neon-bright"
        @click="quickFill"
      >
        <Zap :size="11" />
        本地开发？点我直接用 dev-token 进入
      </button>
    </div>
  </div>
</template>
