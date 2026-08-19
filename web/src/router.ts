import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from './views/DashboardView.vue'
import TransactionsView from './views/TransactionsView.vue'
import LoansView from './views/LoansView.vue'
import ForecastView from './views/ForecastView.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'dashboard', component: DashboardView, meta: { title: '仪表盘' } },
    { path: '/transactions', name: 'transactions', component: TransactionsView, meta: { title: '流水' } },
    { path: '/loans', name: 'loans', component: LoansView, meta: { title: '贷款' } },
    { path: '/forecast', name: 'forecast', component: ForecastView, meta: { title: '结余预测' } },
  ],
})
