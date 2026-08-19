<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { NEmpty, NPopconfirm, useMessage } from 'naive-ui'
import { Plus, Repeat, Trash2, Bot, Hand } from 'lucide-vue-next'
import { api } from '../api/client'
import type { Transaction } from '../api/types'
import MoneyNum from '../components/MoneyNum.vue'
import AddTxDrawer from '../components/AddTxDrawer.vue'
import RecurringModal from '../components/RecurringModal.vue'

const message = useMessage()
const items = ref<Transaction[]>([])
const loading = ref(true)
const showAdd = ref(false)
const showRecurring = ref(false)

const grouped = computed(() => {
  const map = new Map<string, Transaction[]>()
  for (const t of items.value) {
    const m = t.date.slice(0, 7)
    if (!map.has(m)) map.set(m, [])
    map.get(m)!.push(t)
  }
  return [...map.entries()].map(([month, list]) => ({
    month,
    list,
    net: list.reduce((acc, t) => acc + (t.direction === 'income' ? t.amount : -t.amount), 0),
  }))
})

async function load() {
  loading.value = true
  try {
    const resp = await api.get<{ items: Transaction[] }>('/transactions', { params: { limit: 300 } })
    items.value = resp.data.items
  } finally {
    loading.value = false
  }
}

async function remove(id: number) {
  await api.delete(`/transactions/${id}`)
  message.success('已删除')
  await load()
}

onMounted(async () => {
  try {
    await load()
  } catch {
    /* 拦截器已处理 */
  }
})
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <span class="term-label">// transactions</span>
      <button
        class="flex cursor-pointer items-center gap-1.5 rounded-md border border-line bg-panel px-3 py-1.5 font-mono text-xs text-sub transition-colors hover:border-neon-dim hover:text-neon-bright"
        @click="showRecurring = true"
      >
        <Repeat :size="13" />
        固定收支（工资/房租）
      </button>
    </div>

    <div v-if="!loading && !items.length" class="pt-20">
      <n-empty description="还没有流水，点右下角记一笔" />
    </div>

    <section
      v-for="(g, gi) in grouped"
      :key="g.month"
      class="term-card rise-in overflow-hidden"
      :style="{ animationDelay: `${gi * 0.06}s` }"
    >
      <div class="flex items-center justify-between border-b border-line px-4 py-3">
        <span class="font-mono text-sm font-semibold text-ink">{{ g.month }}</span>
        <MoneyNum :value="g.net" size="sm" sign="always" />
      </div>
      <div
        v-for="t in g.list"
        :key="t.id"
        class="group flex items-center gap-3 border-b border-line/50 px-4 py-3 last:border-0 transition-colors hover:bg-raise/60"
      >
        <span
          class="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border font-mono text-[10px]"
          :class="
            t.direction === 'income'
              ? 'border-gain-dim bg-gain/10 text-gain'
              : 'border-neon-dim bg-neon/10 text-neon-bright'
          "
        >
          {{ t.direction === 'income' ? 'IN' : 'OUT' }}
        </span>
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-1.5 text-sm text-ink">
            {{ t.category }}
            <component :is="t.source === 'mcp' ? Bot : Hand" :size="12" class="text-mute" />
          </div>
          <div v-if="t.note" class="truncate text-xs text-mute">{{ t.note }}</div>
        </div>
        <span class="font-mono text-[11px] text-mute">{{ t.date.slice(5) }}</span>
        <MoneyNum :value="t.direction === 'income' ? t.amount : -t.amount" size="sm" sign="always" />
        <n-popconfirm @positive-click="remove(t.id)">
          <template #trigger>
            <button
              class="cursor-pointer text-mute opacity-0 transition-opacity hover:text-danger group-hover:opacity-100"
            >
              <Trash2 :size="14" />
            </button>
          </template>
          删除这条流水？
        </n-popconfirm>
      </div>
    </section>

    <!-- 记一笔 FAB -->
    <button
      class="fixed bottom-20 right-4 z-30 flex h-14 w-14 cursor-pointer items-center justify-center rounded-full border border-neon bg-neon text-void shadow-glow-lg transition-transform duration-200 hover:scale-105 active:scale-95 md:bottom-8 md:right-8"
      @click="showAdd = true"
    >
      <Plus :size="24" :stroke-width="2.5" />
    </button>

    <AddTxDrawer :show="showAdd" @close="showAdd = false" @saved="load" />
    <RecurringModal :show="showRecurring" @close="showRecurring = false" />
  </div>
</template>
