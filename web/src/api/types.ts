export interface Transaction {
  id: number
  amount: number
  direction: 'income' | 'expense'
  category: string
  date: string
  note: string
  source: string
}

export interface RecurringItem {
  id: number
  name: string
  amount: number
  direction: 'income' | 'expense'
  category: string
  day_of_month: number
  start_month: string
  end_month: string | null
  active: boolean
}

export interface Loan {
  id: number
  name: string
  principal: number
  annual_rate: number
  periods: number
  method: string
  exclude_principal: boolean
  start_date: string
  status: string
  monthly_payment: number
  remaining_principal: number
  paid_periods: number
  total_interest: number
}

export interface ScheduleRow {
  period_no: number
  due_month: string
  principal: number
  interest: number
  payment: number
  remaining: number
}

export interface MonthForecast {
  month: string
  income: number
  recurring_expense: number
  loan_payment: number
  expense: number
  net: number
  cumulative: number
}

export interface Forecast {
  months: MonthForecast[]
  yearly_net: Record<string, number>
  min_cumulative: number
  first_negative_month: string | null
}

export interface SimulateResult {
  virtual_monthly_payment: number
  conclusion: string
  base: Forecast
  simulated: Forecast
}

export interface Dashboard {
  month: string
  income: number
  expense: number
  recurring_expense: number
  loan_payment: number
  net: number
  cumulative: number
  initial_balance: number
  yearly_net: Record<string, number>
  first_negative_month: string | null
  min_cumulative: number
  active_loan_count: number
  next6: { month: string; net: number; cumulative: number }[]
}

export interface Categories {
  expense: string[]
  income: string[]
}
