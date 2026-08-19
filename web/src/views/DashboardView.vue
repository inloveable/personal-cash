<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { NInputNumber, useMessage } from 'naive-ui'
import { ArrowDownToLine, ArrowUpFromLine, Landmark, PiggyBank, Wallet } from 'lucide-vue-next'
import { api } from '../api/client'
import type { Dashboard } from '../api/types'
import MoneyNum from '../components/MoneyNum.vue'

const message = useMessage()
const data = ref<Dashboard | null>(null)
const editingBalance = ref(false)
const balanceInput = ref<number | null>(null)

const stats = computed(() => {
  if (!data.value) return []
  return [
    { label: '本月收入', value: data.value.income, icon: ArrowDownToLine, cls: 'text-gain' },
    { label: '日常开销', value: -data.value.expense - data.value.recurring_expense, icon: ArrowUpFromLine, cls: 'text-neon-bright' },
    { label: '贷款月供', value: -data.value.loan_payment, icon: Landmark, cls: 'text-amber' },
    { label: '月结余', value: data.value.net, icon: PiggyBank, cls: data.value.net >= 0 ? 'text-gain' : 'text-neon-bright' },
  ]
})

const yearlyNet = computed(() => {
  if (!data.value) return { year: '', value: 0 }
  const year = data.value.month.slice(0, 4)
  return { year, value: data.value.yearly_net[year] ?? 0 }
})

const maxAbsNet = computed(() =>
  Math.max(1, ...(data.value?.next6.map((m) => Math.abs(m.net)) ?? [1])),
)

async function load() {
  const resp = await api.get<Dashboard>('/dashboard')
  data.value = resp.data
}

async function saveBalance() {
  if (balanceInput.value == null) return
  await api.put('/settings/balance', { initial_balance: balanceInput.value })
  message.success('期初余额已更新')
  editingBalance.value = false
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
  <div v-if="data" class="space-y-4">
    <!-- 年结余焦点卡 -->
    <section class="term-card-glow scanline rise-in p-6 md:p-8">
      <div class="term-label mb-1">// projected_annual_surplus</div>
      <div class="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div class="mb-2 flex items-center gap-2 text-sm text-sub">
            <Wallet :size="15" class="text-neon" />
            预计 {{ yearlyNet.year }} 年结余
          </div>
          <MoneyNum :value="yearlyNet.value" size="xl" sign="always" suffix="CNY" />
        </div>
        <div class="text-right font-mono text-xs text-mute">
          <div>累计结余 <span class="text-sub">{{ data.cumulative.toLocaleString('zh-CN') }}</span></div>
          <div class="mt-1">
            期初余额
            <button
              class="cursor-pointer text-neon underline decoration-dotted underline-offset-4 hover:text-neon-bright"
              @click="editingBalance = !editingBalance; balanceInput = data.initial_balance"
            >{{ data.initial_balance.toLocaleString('zh-CN') }}</button>
          </div>
          <div v-if="editingBalance" class="mt-2 flex items-center gap-2">
            <n-input-number v-model:value="balanceInput" size="small" :show-button="false" class="w-32" />
            <button class="cursor-pointer font-mono text-xs text-neon hover:text-neon-bright" @click="saveBalance">[保存]</button>
          </div>
        </div>
      </div>
      <div v-if="data.first_negative_month" class="mt-4 rounded border border-amber/40 bg-amber/10 px-3 py-2 font-mono text-xs text-amber">
        ⚠ {{ data.first_negative_month }} 累计结余将转负，最低 {{ data.min_cumulative.toLocaleString('zh-CN') }} 元
      </div>
    </section>

    <!-- 四指标 -->
    <section class="grid grid-cols-2 gap-3 lg:grid-cols-4">
      <div
        v-for="(s, i) in stats"
        :key="s.label"
        class="term-card rise-in p-4 transition-transform duration-200 hover:-translate-y-0.5 hover:shadow-glow"
        :style="{ animationDelay: `${0.06 * (i + 1)}s` }"
      >
        <div class="mb-2 flex items-center justify-between">
          <span class="term-label">{{ s.label }}</span>
          <component :is="s.icon" :size="15" :class="s.cls" />
        </div>
        <MoneyNum :value="s.value" size="lg" sign="always" />
      </div>
    </section>

    <!-- 未来 6 月趋势 -->
    <section class="term-card rise-in p-5" style="animation-delay: 0.32s">
      <div class="term-label mb-4">// next_6_months_net</div>
      <div class="flex items-end gap-2 sm:gap-3">
        <div v-for="m in data.next6" :key="m.month" class="flex flex-1 flex-col items-center gap-2">
          <span class="num text-[10px] sm:text-xs" :class="m.net >= 0 ? 'text-gain' : 'text-neon-bright'">
            {{ (m.net / 1000).toFixed(1) }}k
          </span>
          <div class="flex h-24 w-full items-end justify-center">
            <div
              class="w-full max-w-10 rounded-t-sm transition-all duration-500"
              :class="m.net >= 0 ? 'bg-gradient-to-t from-gain-dim to-gain' : 'bg-gradient-to-t from-neon-dim to-neon-bright shadow-glow'"
              :style="{ height: `${Math.max(6, (Math.abs(m.net) / maxAbsNet) * 100)}%` }"
            />
          </div>
          <span class="font-mono text-[10px] text-mute">{{ m.month.slice(2) }}</span>
        </div>
      </div>
    </section>

    <p class="pt-1 text-center font-mono text-[11px] text-mute">
      salary = daily_expense + loan_payment + surplus<span class="blink text-neon">▌</span>
    </p>
  </div>

  <div v-else class="flex h-64 items-center justify-center">
    <span class="font-mono text-sm text-mute">loading<span class="blink text-neon">▌</span></span>
  </div>
</template>
