<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import {
  NButton,
  NInput,
  NInputNumber,
  NModal,
  NPopconfirm,
  NRadioButton,
  NRadioGroup,
  useMessage,
} from 'naive-ui'
import { Plus, Repeat, Trash2 } from 'lucide-vue-next'
import { api } from '../api/client'
import type { RecurringItem } from '../api/types'

const props = defineProps<{ show: boolean }>()
const emit = defineEmits<{ close: [] }>()

const message = useMessage()
const items = ref<RecurringItem[]>([])
const saving = ref(false)

const form = ref({
  name: '',
  amount: null as number | null,
  direction: 'income' as 'income' | 'expense',
  day_of_month: 10,
})

async function load() {
  const resp = await api.get<{ items: RecurringItem[] }>('/recurring')
  items.value = resp.data.items
}

async function add() {
  if (!form.value.name.trim() || !form.value.amount) {
    message.warning('请填写名称和金额')
    return
  }
  saving.value = true
  try {
    await api.post('/recurring', {
      name: form.value.name,
      amount: form.value.amount,
      direction: form.value.direction,
      category: form.value.direction === 'income' ? '工资' : '居住',
      day_of_month: form.value.day_of_month,
    })
    message.success('已添加，每月自动计入结余预测')
    form.value = { name: '', amount: null, direction: 'income', day_of_month: 10 }
    await load()
  } finally {
    saving.value = false
  }
}

async function remove(id: number) {
  await api.delete(`/recurring/${id}`)
  message.success('已删除')
  await load()
}

watch(
  () => props.show,
  async (v) => {
    if (v) await load()
  },
)

onMounted(async () => {
  if (props.show) await load()
})
</script>

<template>
  <n-modal :show="show" preset="card" title="$ recurring --fixed-income-expense" class="max-w-lg" :bordered="false" @update:show="(v: boolean) => !v && emit('close')">
    <div class="space-y-5">
      <p class="font-mono text-xs text-mute">
        每月固定发生的收支（工资、房租、话费…），自动纳入结余预测，无需每月重复记账。
      </p>

      <!-- 已有项 -->
      <div v-if="items.length" class="space-y-2">
        <div
          v-for="it in items"
          :key="it.id"
          class="flex items-center gap-3 rounded-md border border-line bg-raise/50 px-3 py-2.5"
        >
          <span
            class="rounded border px-1.5 py-0.5 font-mono text-[10px]"
            :class="
              it.direction === 'income'
                ? 'border-gain-dim bg-gain/10 text-gain'
                : 'border-neon-dim bg-neon/10 text-neon-bright'
            "
          >
            {{ it.direction === 'income' ? 'IN' : 'OUT' }}
          </span>
          <div class="flex-1">
            <span class="text-sm text-ink">{{ it.name }}</span>
            <span class="ml-2 font-mono text-[11px] text-mute">每月 {{ it.day_of_month }} 号</span>
          </div>
          <span class="num text-sm font-semibold" :class="it.direction === 'income' ? 'text-gain' : 'text-neon-bright'">
            {{ it.direction === 'income' ? '+' : '-' }}{{ it.amount.toLocaleString('zh-CN') }}
          </span>
          <n-popconfirm @positive-click="remove(it.id)">
            <template #trigger>
              <button class="cursor-pointer text-mute transition-colors hover:text-danger">
                <Trash2 :size="14" />
              </button>
            </template>
            删除这项固定收支？
          </n-popconfirm>
        </div>
      </div>
      <div v-else class="rounded-md border border-dashed border-line py-6 text-center font-mono text-xs text-mute">
        还没有固定收支项
      </div>

      <!-- 新增表单 -->
      <div class="space-y-3 border-t border-line pt-4">
        <div class="term-label">// add_new</div>
        <n-radio-group v-model:value="form.direction" size="small">
          <n-radio-button value="income">收入（如工资）</n-radio-button>
          <n-radio-button value="expense">支出（如房租）</n-radio-button>
        </n-radio-group>
        <div class="grid grid-cols-3 gap-2">
          <n-input v-model:value="form.name" placeholder="名称：工资" class="col-span-1" />
          <n-input-number v-model:value="form.amount" :min="0" :precision="2" :show-button="false" placeholder="金额（元）" class="col-span-1" />
          <n-input-number v-model:value="form.day_of_month" :min="1" :max="31" placeholder="几号" class="col-span-1" />
        </div>
        <n-button type="primary" size="small" block :loading="saving" @click="add">
          <template #icon><Plus :size="13" /></template>
          添加固定收支
        </n-button>
      </div>
    </div>
  </n-modal>
</template>
