<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { use } from 'echarts/core'
import { BarChart, LineChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'
import { NButton, NInputNumber, NSelect } from 'naive-ui'
import { FlaskConical, RotateCcw } from 'lucide-vue-next'
import { api } from '../api/client'
import type { Forecast, SimulateResult } from '../api/types'

use([LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const forecast = ref<Forecast | null>(null)
const simResult = ref<SimulateResult | null>(null)
const simulating = ref(false)

const simAmount = ref<number | null>(20000)
const simPeriods = ref<number | null>(12)
const simRate = ref<number | null>(0)

const chartOption = computed(() => {
  const base = simResult.value?.base ?? forecast.value
  if (!base) return {}
  const simulated = simResult.value?.simulated
  const months = base.months.map((m) => m.month)
  const negSet = new Set(
    base.months.filter((m) => m.cumulative < 0).map((m) => m.month),
  )

  // 中国习惯：红 = 赚（正结余），绿 = 亏（负结余）
  const series: any[] = [
    {
      name: '月结余',
      type: 'bar',
      data: base.months.map((m) => ({
        value: m.net,
        itemStyle: { color: m.net >= 0 ? '#F87171' : '#4ADE80', borderRadius: [3, 3, 0, 0] },
      })),
      barMaxWidth: 22,
    },
    {
      name: '累计结余',
      type: 'line',
      smooth: true,
      symbolSize: 5,
      lineStyle: { color: '#F87171', width: 2, shadowColor: 'rgba(248,113,113,0.5)', shadowBlur: 8 },
      itemStyle: { color: '#F87171' },
      data: base.months.map((m) => m.cumulative),
      markLine: {
        silent: true,
        symbol: 'none',
        lineStyle: { color: '#52705F', type: 'dashed', width: 1 },
        data: [{ yAxis: 0 }],
        label: { show: false },
      },
    },
  ]

  if (simulated) {
    series.push({
      name: '沙盘累计',
      type: 'line',
      smooth: true,
      symbol: 'none',
      lineStyle: { color: '#F59E0B', width: 2, type: 'dashed' },
      itemStyle: { color: '#F59E0B' },
      data: simulated.months.map((m) => m.cumulative),
    })
  }

  return {
    backgroundColor: 'transparent',
    animationDuration: 400,
    grid: { left: 8, right: 8, top: 36, bottom: 4, containLabel: true },
    legend: { textStyle: { color: '#8FAF9B', fontFamily: 'JetBrains Mono', fontSize: 11 }, top: 0 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#101C12',
      borderColor: '#1C2E20',
      textStyle: { color: '#E7F5EC', fontFamily: 'JetBrains Mono', fontSize: 12 },
      valueFormatter: (v: number) => `${v?.toLocaleString('zh-CN')} 元`,
    },
    xAxis: {
      type: 'category',
      data: months,
      axisLine: { lineStyle: { color: '#1C2E20' } },
      axisLabel: {
        color: (v: string) => (negSet.has(v) ? '#4ADE80' : '#52705F'),
        fontFamily: 'JetBrains Mono',
        fontSize: 10,
      },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'rgba(28,46,32,0.5)' } },
      axisLabel: {
        color: '#52705F',
        fontFamily: 'JetBrains Mono',
        fontSize: 10,
        formatter: (v: number) => (Math.abs(v) >= 10000 ? `${v / 10000}w` : `${v}`),
      },
    },
    series,
  }
})

async function load() {
  const resp = await api.get<Forecast>('/cashflow/forecast', { params: { months: 12 } })
  forecast.value = resp.data
}

async function runSimulate() {
  if (!simAmount.value || !simPeriods.value) return
  simulating.value = true
  try {
    const resp = await api.post<SimulateResult>('/cashflow/simulate', {
      amount: simAmount.value,
      periods: simPeriods.value,
      annual_rate: simRate.value ?? 0,
      months: 12,
    })
    simResult.value = resp.data
  } finally {
    simulating.value = false
  }
}

function resetSimulate() {
  simResult.value = null
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
    <!-- 沙盘输入条 -->
    <section class="term-card-glow rise-in p-4 md:p-5">
      <div class="term-label mb-3">// sandbox — 想买什么？试试会不会破产</div>
      <div class="flex flex-wrap items-end gap-3">
        <div class="w-36">
          <div class="mb-1 font-mono text-[11px] text-mute">价格（元）</div>
          <n-input-number v-model:value="simAmount" :min="0" :show-button="false" placeholder="20000" />
        </div>
        <div class="w-28">
          <div class="mb-1 font-mono text-[11px] text-mute">分期数</div>
          <n-input-number v-model:value="simPeriods" :min="1" :max="60" :show-button="false" placeholder="12" />
        </div>
        <div class="w-32">
          <div class="mb-1 font-mono text-[11px] text-mute">年利率 %</div>
          <n-input-number v-model:value="simRate" :min="0" :max="36" :precision="2" :show-button="false" placeholder="0" />
        </div>
        <n-button type="primary" :loading="simulating" @click="runSimulate">
          <template #icon><FlaskConical :size="14" /></template>
          试算
        </n-button>
        <n-button v-if="simResult" quaternary size="small" @click="resetSimulate">
          <template #icon><RotateCcw :size="13" /></template>
          还原
        </n-button>
      </div>
      <div
        v-if="simResult"
        class="mt-3 rounded border px-3 py-2.5 font-mono text-xs leading-relaxed"
        :class="
          simResult.simulated.first_negative_month
            ? 'border-neon-dim bg-neon/5 text-neon-bright'
            : 'border-gain-dim bg-gain/5 text-gain'
        "
      >
        {{ simResult.conclusion }}
      </div>
    </section>

    <!-- 图表 -->
    <section class="term-card rise-in p-4 md:p-5" style="animation-delay: 0.08s">
      <div class="term-label mb-2">// future_12_months</div>
      <v-chart v-if="forecast" :option="chartOption" autoresize class="h-72 w-full md:h-80" />
    </section>

    <!-- 年结余汇总 -->
    <section v-if="forecast" class="grid grid-cols-2 gap-3">
      <div
        v-for="(v, y) in forecast.yearly_net"
        :key="y"
        class="term-card rise-in p-4"
        style="animation-delay: 0.14s"
      >
        <div class="term-label mb-1">{{ y }} 年结余</div>
        <span class="num text-xl font-bold" :class="v >= 0 ? 'text-gain' : 'text-neon-bright'">
          {{ v >= 0 ? '+' : '' }}{{ v.toLocaleString('zh-CN') }}
        </span>
      </div>
    </section>

    <!-- 逐月明细 -->
    <section v-if="forecast" class="term-card rise-in overflow-hidden" style="animation-delay: 0.2s">
      <div class="border-b border-line px-4 py-3 term-label">// monthly_breakdown</div>
      <div class="overflow-x-auto">
        <table class="w-full min-w-[560px] font-mono text-xs">
          <thead>
            <tr class="text-left text-mute">
              <th class="px-4 py-2 font-normal">月份</th>
              <th class="px-2 py-2 text-right font-normal">收入</th>
              <th class="px-2 py-2 text-right font-normal">开销</th>
              <th class="px-2 py-2 text-right font-normal">月供</th>
              <th class="px-2 py-2 text-right font-normal">月结余</th>
              <th class="px-4 py-2 text-right font-normal">累计</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="m in forecast.months"
              :key="m.month"
              class="border-t border-line/40 hover:bg-raise/50 text-sub"
            >
              <td class="px-4 py-2 text-ink">{{ m.month }}</td>
              <td class="px-2 py-2 text-right">{{ m.income.toLocaleString('zh-CN') }}</td>
              <td class="px-2 py-2 text-right">{{ (m.expense + m.recurring_expense).toLocaleString('zh-CN') }}</td>
              <td class="px-2 py-2 text-right text-amber">{{ m.loan_payment.toLocaleString('zh-CN') }}</td>
              <td class="px-2 py-2 text-right" :class="m.net >= 0 ? 'text-gain' : 'text-neon-bright'">
                {{ m.net >= 0 ? '+' : '' }}{{ m.net.toLocaleString('zh-CN') }}
              </td>
              <td class="px-4 py-2 text-right" :class="m.cumulative >= 0 ? 'text-ink' : 'text-neon-bright'">
                {{ m.cumulative.toLocaleString('zh-CN') }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>
