<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { NButton, NDrawer, NDrawerContent, NInput, NInputNumber, NRadioButton, NRadioGroup, useMessage } from 'naive-ui'
import { api } from '../api/client'
import type { Categories } from '../api/types'

const props = defineProps<{ show: boolean }>()
const emit = defineEmits<{ close: []; saved: [] }>()

const message = useMessage()
const direction = ref<'expense' | 'income'>('expense')
const amount = ref<number | null>(null)
const category = ref('餐饮')
const note = ref('')
const saving = ref(false)
const categories = ref<Categories>({ expense: [], income: [] })

const activeCategories = computed(() =>
  direction.value === 'expense' ? categories.value.expense : categories.value.income,
)

watch(
  () => props.show,
  async (v) => {
    if (!v) return
    if (!categories.value.expense.length) {
      const resp = await api.get<Categories>('/categories')
      categories.value = resp.data
    }
    category.value = direction.value === 'expense' ? '餐饮' : '工资'
  },
)

watch(direction, (d) => {
  category.value = d === 'expense' ? '餐饮' : '工资'
})

async function save() {
  if (!amount.value || amount.value <= 0) {
    message.warning('请输入金额')
    return
  }
  saving.value = true
  try {
    await api.post('/transactions', {
      amount: amount.value,
      direction: direction.value,
      category: category.value,
      note: note.value,
    })
    message.success('已记账')
    amount.value = null
    note.value = ''
    emit('saved')
    emit('close')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <n-drawer :show="show" placement="bottom" :height="480" @update:show="(v: boolean) => !v && emit('close')">
    <n-drawer-content body-content-class="bg-void" closable>
      <template #header>
        <span class="font-mono text-sm text-neon-bright">$ record --new</span>
      </template>

      <div class="mx-auto max-w-md space-y-5 pt-2">
        <n-radio-group v-model:value="direction" size="large" class="flex w-full">
          <n-radio-button value="expense" class="flex-1 text-center">支出</n-radio-button>
          <n-radio-button value="income" class="flex-1 text-center">收入</n-radio-button>
        </n-radio-group>

        <div>
          <div class="term-label mb-2">金额</div>
          <n-input-number
            v-model:value="amount"
            size="large"
            :show-button="false"
            :min="0"
            :precision="2"
            placeholder="0.00"
            class="w-full num text-2xl"
            autofocus
          >
            <template #prefix><span class="text-mute">¥</span></template>
          </n-input-number>
        </div>

        <div>
          <div class="term-label mb-2">分类</div>
          <div class="flex gap-2 overflow-x-auto pb-1">
            <button
              v-for="c in activeCategories"
              :key="c"
              class="shrink-0 cursor-pointer rounded-md border px-3.5 py-2 font-mono text-[13px] transition-all duration-150"
              :class="
                category === c
                  ? 'border-neon bg-raise text-neon-bright shadow-glow'
                  : 'border-line bg-panel text-sub hover:text-ink'
              "
              @click="category = c"
            >
              {{ c }}
            </button>
          </div>
        </div>

        <div>
          <div class="term-label mb-2">备注（可选）</div>
          <n-input v-model:value="note" placeholder="这钱花哪了 / 从哪来" size="large" maxlength="60" />
        </div>

        <n-button type="primary" size="large" block :loading="saving" @click="save">
          记一笔
        </n-button>
      </div>
    </n-drawer-content>
  </n-drawer>
</template>
