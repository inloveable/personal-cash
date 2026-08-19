<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  NButton,
  NCheckbox,
  NDatePicker,
  NEmpty,
  NInput,
  NInputNumber,
  NModal,
  NPopconfirm,
  NProgress,
  NRadioGroup,
  NRadio,
  useMessage,
} from 'naive-ui'
import { ChevronDown, ChevronUp, Plus, Trash2 } from 'lucide-vue-next'
import { api } from '../api/client'
import type { Loan, ScheduleRow } from '../api/types'
import MoneyNum from '../components/MoneyNum.vue'

const message = useMessage()
const loans = ref<Loan[]>([])
const loading = ref(true)
const expanded = ref<number | null>(null)
const schedules = ref<Record<number, ScheduleRow[]>>({})
const showAdd = ref(false)
const saving = ref(false)

const form = ref({
  name: '',
  principal: null as number | null,
  annual_rate: 0,
  periods: 12,
  method: 'equal_payment' as string,
  exclude_principal: false,
  start_date: null as string | null,
})

const paidHint = computed(() => {
  if (!form.value.start_date) return ''
  const [y, m] = form.value.start_date.split('-').map(Number)
  const now = new Date()
  const diff = (now.getFullYear() - y) * 12 + (now.getMonth() + 1 - m)
  if (diff <= 0) return ''
  const paid = Math.min(diff, form.value.periods ?? 0)
  return `存量贷款：已还 ${paid} 期将自动标记为已还，预测只算剩余期次`
})

async function load() {
  loading.value = true
  try {
    const resp = await api.get<{ items: Loan[] }>('/loans')
    loans.value = resp.data.items
  } finally {
    loading.value = false
  }
}

async function toggle(id: number) {
  if (expanded.value === id) {
    expanded.value = null
    return
  }
  expanded.value = id
  if (!schedules.value[id]) {
    const resp = await api.get<{ schedule: ScheduleRow[] }>(`/loans/${id}/schedule`)
    schedules.value[id] = resp.data.schedule
  }
}

async function create() {
  if (!form.value.name.trim() || !form.value.principal) {
    message.warning('请填写名称和本金')
    return
  }
  saving.value = true
  try {
    await api.post('/loans', {
      name: form.value.name,
      principal: form.value.principal,
      annual_rate: form.value.annual_rate ?? 0,
      periods: form.value.periods,
      method: form.value.method,
      exclude_principal: form.value.method === 'interest_only' ? form.value.exclude_principal : false,
      start_date: form.value.start_date ?? undefined,
    })
    message.success('贷款已创建，摊还表已生成')
    showAdd.value = false
    form.value = { name: '', principal: null, annual_rate: 0, periods: 12, method: 'equal_payment', exclude_principal: false, start_date: null }
    await load()
  } finally {
    saving.value = false
  }
}

async function remove(id: number) {
  await api.delete(`/loans/${id}`)
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
      <span class="term-label">// active_loans: {{ loans.length }}</span>
      <n-button type="primary" size="small" @click="showAdd = true">
        <template #icon><Plus :size="14" /></template>
        新增贷款
      </n-button>
    </div>

    <div v-if="!loading && !loans.length" class="pt-20">
      <n-empty description="没有贷款，无债一身轻" />
    </div>

    <section
      v-for="(l, i) in loans"
      :key="l.id"
      class="term-card rise-in overflow-hidden"
      :style="{ animationDelay: `${i * 0.06}s` }"
    >
      <div class="p-4 md:p-5">
        <div class="flex items-start justify-between gap-3">
          <div>
            <div class="mb-1 flex items-center gap-2">
              <span class="font-mono text-base font-bold text-ink">{{ l.name }}</span>
              <span class="rounded border border-line bg-raise px-1.5 py-0.5 font-mono text-[10px] text-sub">
                {{ ({ equal_payment: '等额本息', equal_principal: '等额本金', interest_only: '先息后本' } as Record<string, string>)[l.method] ?? l.method }} · {{ l.annual_rate }}%
              </span>
              <span v-if="l.exclude_principal" class="rounded border border-neon-dim bg-neon/10 px-1.5 py-0.5 font-mono text-[10px] text-neon-bright">
                本金滚续
              </span>
            </div>
            <div class="font-mono text-[11px] text-mute">
              本金 {{ l.principal.toLocaleString('zh-CN') }} · 已还 {{ l.paid_periods }}/{{ l.periods }} 期 · 总利息
              {{ l.total_interest.toLocaleString('zh-CN') }}
            </div>
          </div>
          <div class="text-right">
            <div class="term-label">月供</div>
            <MoneyNum :value="-l.monthly_payment" size="lg" sign="none" class="text-amber" />
          </div>
        </div>

        <div class="mt-4 flex items-center gap-3">
          <n-progress
            type="line"
            :percentage="Math.round((l.paid_periods / l.periods) * 100)"
            :height="6"
            :border-radius="3"
            color="#22C55E"
            rail-color="#101C12"
            :show-indicator="false"
            class="flex-1"
          />
          <span class="font-mono text-[11px] text-sub">
            剩 {{ l.remaining_principal.toLocaleString('zh-CN') }}
          </span>
        </div>
      </div>

      <div class="flex items-center justify-between border-t border-line px-4 py-2">
        <button
          class="flex cursor-pointer items-center gap-1 font-mono text-xs text-sub hover:text-neon-bright"
          @click="toggle(l.id)"
        >
          <component :is="expanded === l.id ? ChevronUp : ChevronDown" :size="13" />
          摊还表
        </button>
        <n-popconfirm @positive-click="remove(l.id)">
          <template #trigger>
            <button class="flex cursor-pointer items-center gap-1 font-mono text-xs text-mute hover:text-danger">
              <Trash2 :size="12" /> 删除
            </button>
          </template>
          删除这笔贷款及其摊还表？
        </n-popconfirm>
      </div>

      <div v-if="expanded === l.id" class="max-h-72 overflow-y-auto border-t border-line">
        <table class="w-full font-mono text-xs">
          <thead class="sticky top-0 bg-raise">
            <tr class="text-left text-mute">
              <th class="px-4 py-2 font-normal">#</th>
              <th class="px-2 py-2 font-normal">月份</th>
              <th class="px-2 py-2 text-right font-normal">本金</th>
              <th class="px-2 py-2 text-right font-normal">利息</th>
              <th class="px-4 py-2 text-right font-normal">剩余</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="s in schedules[l.id] ?? []"
              :key="s.period_no"
              class="border-t border-line/40 text-sub hover:bg-raise/50"
            >
              <td class="px-4 py-1.5">{{ s.period_no }}</td>
              <td class="px-2 py-1.5">{{ s.due_month }}</td>
              <td class="px-2 py-1.5 text-right text-ink">{{ s.principal.toLocaleString('zh-CN') }}</td>
              <td class="px-2 py-1.5 text-right text-amber">{{ s.interest.toLocaleString('zh-CN') }}</td>
              <td class="px-4 py-1.5 text-right">{{ s.remaining.toLocaleString('zh-CN') }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- 新增贷款弹窗 -->
    <n-modal v-model:show="showAdd" preset="card" title="$ loan --new" class="max-w-md" :bordered="false">
      <div class="space-y-4">
        <div>
          <div class="term-label mb-1.5">名称</div>
          <n-input v-model:value="form.name" placeholder="车贷 / 手机分期 / 装修贷…" size="large" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <div class="term-label mb-1.5">本金（元）</div>
            <n-input-number v-model:value="form.principal" :min="0" :precision="2" :show-button="false" size="large" class="w-full" />
          </div>
          <div>
            <div class="term-label mb-1.5">期数（月）</div>
            <n-input-number v-model:value="form.periods" :min="1" :max="360" size="large" class="w-full" />
          </div>
        </div>
        <div>
          <div class="term-label mb-1.5">年利率 %（免息填 0）</div>
          <n-input-number v-model:value="form.annual_rate" :min="0" :max="36" :precision="2" :show-button="false" size="large" class="w-full" />
        </div>
        <div>
          <div class="term-label mb-1.5">首次还款月（存量贷款选过去的月份，默认当月）</div>
          <n-date-picker
            v-model:formatted-value="form.start_date"
            type="month"
            value-format="yyyy-MM-01"
            clearable
            size="large"
            class="w-full"
            placeholder="如 2026-03"
          />
          <p v-if="paidHint" class="mt-1.5 font-mono text-[11px] text-amber">{{ paidHint }}</p>
        </div>
        <div>
          <div class="term-label mb-1.5">还款方式</div>
          <n-radio-group v-model:value="form.method" size="large">
            <n-radio value="equal_payment">等额本息</n-radio>
            <n-radio value="equal_principal">等额本金</n-radio>
            <n-radio value="interest_only">先息后本</n-radio>
          </n-radio-group>
          <p v-if="form.method === 'interest_only'" class="mt-1.5 font-mono text-[11px] text-mute">
            每期只还利息，到期一次性还全部本金（消费贷常见）。
          </p>
          <n-checkbox v-if="form.method === 'interest_only'" v-model:checked="form.exclude_principal" class="mt-2">
            <span class="font-mono text-xs text-sub">本金不影响现金流（到期续贷，预测只计每月利息）</span>
          </n-checkbox>
        </div>
        <n-button type="primary" size="large" block :loading="saving" @click="create">创建并生成摊还表</n-button>
      </div>
    </n-modal>
  </div>
</template>
