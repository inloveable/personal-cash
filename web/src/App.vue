<script setup lang="ts">
import { computed, h, onMounted, ref } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'
import {
  NConfigProvider,
  NDialogProvider,
  NMessageProvider,
  darkTheme,
  type GlobalThemeOverrides,
} from 'naive-ui'
import { LayoutDashboard, ArrowLeftRight, Landmark, TrendingUp, Terminal } from 'lucide-vue-next'
import { getToken, setToken, setUnauthorizedHandler, setErrorHandler } from './api/client'
import TokenGate from './components/TokenGate.vue'

const route = useRoute()
const router = useRouter()
const authed = ref(!!getToken())

const globalError = ref('')
let errorTimer: ReturnType<typeof setTimeout> | null = null

setUnauthorizedHandler(() => {
  authed.value = false
})

setErrorHandler((msg) => {
  globalError.value = msg
  if (errorTimer) clearTimeout(errorTimer)
  errorTimer = setTimeout(() => (globalError.value = ''), 4000)
})

function onTokenSubmit(token: string) {
  setToken(token)
  authed.value = true
}

const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#22C55E',
    primaryColorHover: '#4ADE80',
    primaryColorPressed: '#16A34A',
    primaryColorSuppl: '#22C55E',
    bodyColor: '#050A07',
    cardColor: '#0A120C',
    modalColor: '#0A120C',
    popoverColor: '#101C12',
    borderColor: '#1C2E20',
    textColorBase: '#E7F5EC',
    fontFamilyMono: '"JetBrains Mono", ui-monospace, monospace',
    borderRadius: '8px',
  },
  Card: { borderColor: '#1C2E20' },
  Input: { color: '#0A120C', borderColor: '#1C2E20' },
  DataTable: { thColor: '#0A120C', tdColor: '#050A07', borderColor: '#1C2E20' },
}

const tabs = [
  { name: 'dashboard', label: '仪表盘', icon: LayoutDashboard, path: '/' },
  { name: 'transactions', label: '流水', icon: ArrowLeftRight, path: '/transactions' },
  { name: 'loans', label: '贷款', icon: Landmark, path: '/loans' },
  { name: 'forecast', label: '结余预测', icon: TrendingUp, path: '/forecast' },
]

const activeTab = computed(() => route.name)

onMounted(() => {
  document.title = 'LEDGER://现金流终端'
})
</script>

<template>
  <n-config-provider :theme="darkTheme" :theme-overrides="themeOverrides">
    <n-message-provider>
      <n-dialog-provider>
        <TokenGate v-if="!authed" @submit="onTokenSubmit" />

        <div v-else class="mx-auto min-h-full w-full max-w-[1200px] px-4 pb-24 md:pb-10 md:px-6">
          <!-- 顶栏 -->
          <header class="flex items-center justify-between border-b border-line py-4">
            <div class="flex items-center gap-2.5">
              <div class="flex h-8 w-8 items-center justify-center rounded-md border border-neon-dim bg-panel shadow-glow">
                <Terminal :size="16" class="text-neon" />
              </div>
              <div>
                <div class="font-mono text-sm font-bold tracking-wider text-neon-bright">
                  LEDGER<span class="text-mute">://</span>现金流终端
                </div>
                <div class="term-label hidden sm:block">personal cashflow terminal · v0.1</div>
              </div>
            </div>

            <!-- 桌面端导航 -->
            <nav class="hidden md:flex items-center gap-1">
              <button
                v-for="t in tabs"
                :key="t.name"
                class="flex cursor-pointer items-center gap-1.5 rounded-md px-3.5 py-2 font-mono text-[13px] transition-all duration-200"
                :class="
                  activeTab === t.name
                    ? 'bg-raise text-neon-bright shadow-glow border border-neon-dim'
                    : 'text-sub hover:text-ink hover:bg-panel border border-transparent'
                "
                @click="router.push(t.path)"
              >
                <component :is="t.icon" :size="14" />
                {{ t.label }}
              </button>
            </nav>

            <div class="hidden md:flex items-center gap-2 font-mono text-[11px] text-mute">
              <span class="inline-block h-1.5 w-1.5 rounded-full bg-neon shadow-glow" />
              ONLINE
            </div>
          </header>

          <!-- 主内容 -->
          <main class="pt-5">
            <RouterView v-slot="{ Component }">
              <component :is="Component" :key="route.fullPath" />
            </RouterView>
          </main>
        </div>

        <!-- 全局错误提示 -->
        <div
          v-if="globalError"
          class="fixed left-1/2 top-4 z-50 -translate-x-1/2 rounded-md border border-danger/50 bg-danger/15 px-4 py-2 font-mono text-xs text-danger backdrop-blur-md"
        >
          {{ globalError }}
        </div>

        <!-- 移动端底部 Tab -->
        <nav
          v-if="authed"
          class="fixed bottom-0 left-0 right-0 z-40 flex border-t border-line bg-panel/95 backdrop-blur-md md:hidden"
          style="padding-bottom: env(safe-area-inset-bottom)"
        >
          <button
            v-for="t in tabs"
            :key="t.name"
            class="flex flex-1 cursor-pointer flex-col items-center gap-1 py-2.5 transition-colors duration-200"
            :class="activeTab === t.name ? 'text-neon-bright' : 'text-mute'"
            @click="router.push(t.path)"
          >
            <component :is="t.icon" :size="19" :stroke-width="activeTab === t.name ? 2.4 : 1.8" />
            <span class="text-[10px] font-medium">{{ t.label }}</span>
          </button>
        </nav>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>
