<template>
  <div class="wallet">
    <header class="head">
      <h1>账户</h1>
      <p class="sub">共享余额 · 每次会话咨询 ¥{{ feeText }} · 下列为本产品流水</p>
    </header>

    <div class="narrow">
      <section class="card">
        <div class="card-top">
          <span class="label">余额</span>
          <button type="button" class="ghost" :disabled="loading" @click="refresh">刷新</button>
        </div>
        <p class="balance">¥{{ balanceText }}</p>
        <p v-if="loadError" class="error">{{ loadError }}</p>
      </section>

      <section class="card">
        <h2>充值</h2>
        <div v-if="channels.length" class="channels">
          <button
            v-for="c in channels"
            :key="c.id"
            type="button"
            class="channel"
            :class="{ on: channel === c.id, alipay: c.id === 'alipay', wechat: c.id === 'wechat' }"
            @click="channel = c.id"
          >
            <span class="channel-name">{{ c.label || channelLabel(c.id) }}</span>
          </button>
        </div>
        <div class="presets">
          <button
            v-for="a in presets"
            :key="a"
            type="button"
            class="preset"
            :class="{ on: amount === a }"
            @click="amount = a"
          >
            ¥{{ a }}
          </button>
        </div>
        <div class="amount-row">
          <label class="amount-field">
            <span>¥</span>
            <input v-model.number="amount" type="number" min="1" step="1" />
          </label>
          <button type="button" class="primary" :disabled="busy" @click="onRecharge">
            {{ busy ? '下单中…' : '去充值' }}
          </button>
        </div>
      </section>
    </div>

    <section class="card wide">
      <div class="tabs">
        <button type="button" :class="{ on: tab === 'orders' }" @click="tab = 'orders'">充值订单</button>
        <button type="button" :class="{ on: tab === 'tx' }" @click="tab = 'tx'">交易流水</button>
      </div>
      <div v-if="tab === 'orders'" class="table-wrap">
        <table v-if="orders.length">
          <thead>
            <tr>
              <th>时间</th>
              <th>金额</th>
              <th>状态</th>
              <th>渠道</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="o in orders" :key="o.order_id">
              <td>{{ formatTime(o.created_at || o.paid_at) }}</td>
              <td>¥{{ Number(o.amount || 0).toFixed(2) }}</td>
              <td>{{ statusLabel(o.status) }}</td>
              <td>{{ channelLabel(o.channel || o.payment_channel) }}</td>
            </tr>
          </tbody>
        </table>
        <p v-else class="empty">暂无充值订单</p>
        <div v-if="orderTotal > orders.length" class="more">
          <button type="button" class="ghost" :disabled="orderBusy" @click="loadMoreOrders">加载更多</button>
        </div>
      </div>
      <div v-else class="table-wrap">
        <table v-if="txs.length">
          <thead>
            <tr>
              <th>时间</th>
              <th>类型</th>
              <th>标题</th>
              <th>金额</th>
              <th>余额</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in txs" :key="t.tx_id">
              <td>{{ formatTime(t.created_at) }}</td>
              <td>{{ typeLabel(t.type) }}</td>
              <td class="title-cell" :title="t.title || ''">{{ t.title || '—' }}</td>
              <td>¥{{ Number(t.amount || 0).toFixed(2) }}</td>
              <td>¥{{ Number(t.balance_after || 0).toFixed(2) }}</td>
            </tr>
          </tbody>
        </table>
        <p v-else class="empty">暂无流水</p>
        <div v-if="txTotal > txs.length" class="more">
          <button type="button" class="ghost" :disabled="txBusy" @click="loadMoreTx">加载更多</button>
        </div>
      </div>
    </section>

    <PayQrModal
      :open="payOpen"
      :title="payTitle"
      :hint="payHint"
      :pay-url="payUrl"
      @close="payOpen = false"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import PayQrModal from '@/components/PayQrModal.vue'
import {
  createRecharge,
  devPay,
  fetchBalance,
  fetchPayChannels,
  fetchPresets,
  fetchRechargeOrders,
  fetchSessionFee,
  fetchTransactions,
  getRecharge
} from '@/api/wallet'
import { confirmDialog, toast } from '@/utils/toast'

const balance = ref(0)
const sessionFee = ref(0.1)
const loadError = ref('')
const loading = ref(false)
const busy = ref(false)
const amount = ref(50)
const presets = ref([])
const channels = ref([])
const channel = ref('')
const tab = ref('orders')
const orders = ref([])
const orderPage = ref(1)
const orderTotal = ref(0)
const orderBusy = ref(false)
const txs = ref([])
const txPage = ref(1)
const txTotal = ref(0)
const txBusy = ref(false)

const payOpen = ref(false)
const payUrl = ref('')
const payTitle = ref('扫码支付')
const payHint = ref('请扫码完成支付')
const orderId = ref('')
let pollTimer = null

const balanceText = computed(() => Number(balance.value || 0).toFixed(2))
const feeText = computed(() => Number(sessionFee.value || 0).toFixed(2))

function channelLabel(id) {
  const map = { wechat: '微信', alipay: '支付宝', dev: '开发', admin: '人工' }
  return map[id] || id || '—'
}

function statusLabel(s) {
  const map = { pending: '待支付', paid: '已支付', failed: '失败', cancelled: '已取消' }
  return map[s] || s || '—'
}

function typeLabel(t) {
  const map = { recharge: '充值', consume: '消费', refund: '退费' }
  return map[t] || t || '—'
}

function formatTime(v) {
  if (!v) return '—'
  const d = new Date(v)
  if (Number.isNaN(d.getTime())) return String(v)
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

async function refresh() {
  loading.value = true
  loadError.value = ''
  try {
    const b = await fetchBalance()
    balance.value = Number(b.balance || 0)
  } catch (err) {
    loadError.value = err.message || '无法获取余额'
  } finally {
    loading.value = false
  }
  try {
    const f = await fetchSessionFee()
    if (f.amount != null) sessionFee.value = Number(f.amount)
  } catch { /* 保留默认 */ }
}

async function loadMeta() {
  try {
    const p = await fetchPresets()
    const items = (p.items || []).map((i) => Number(i.amount)).filter((n) => n > 0)
    presets.value = items
    if (items[0] && !amount.value) amount.value = items[0]
    else if (items[0]) amount.value = items[0]
  } catch { /* 保留默认 */ }
  try {
    const c = await fetchPayChannels()
    channels.value = c.items || []
    if (channels.value[0]?.id) channel.value = channels.value[0].id
  } catch { /* 无渠道时仍可尝试下单 */ }
}

async function loadOrders(reset = false) {
  if (reset) {
    orderPage.value = 1
    orders.value = []
  }
  orderBusy.value = true
  try {
    const r = await fetchRechargeOrders(orderPage.value, 20, 'or')
    const items = r.items || r.orders || []
    orders.value = reset ? items : orders.value.concat(items)
    orderTotal.value = Number(r.total || orders.value.length)
  } catch { /* toast 已由 http */ }
  finally {
    orderBusy.value = false
  }
}

async function loadMoreOrders() {
  orderPage.value += 1
  await loadOrders(false)
}

async function loadTx(reset = false) {
  if (reset) {
    txPage.value = 1
    txs.value = []
  }
  txBusy.value = true
  try {
    const r = await fetchTransactions(txPage.value, 20, 'or')
    const items = r.items || []
    txs.value = reset ? items : txs.value.concat(items)
    txTotal.value = Number(r.total || txs.value.length)
  } catch { /* toast */ }
  finally {
    txBusy.value = false
  }
}

async function loadMoreTx() {
  txPage.value += 1
  await loadTx(false)
}

function stopPoll() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function startPoll() {
  stopPoll()
  pollTimer = setInterval(async () => {
    if (!orderId.value) return
    try {
      const o = await getRecharge(orderId.value)
      if (o.status === 'paid') {
        toast('充值成功')
        payOpen.value = false
        payUrl.value = ''
        orderId.value = ''
        stopPoll()
        await refresh()
        await loadOrders(true)
        await loadTx(true)
      }
    } catch { /* ignore */ }
  }, 2500)
}

async function onRecharge() {
  const n = Math.floor(Number(amount.value))
  if (!Number.isFinite(n) || n < 1 || n > 4000) {
    toast('金额需在 1～4000 元之间')
    return
  }
  busy.value = true
  try {
    const order = await createRecharge(n, channel.value || undefined)
    orderId.value = order.order_id || ''
    const qr = order.code_url || order.pay_url || ''
    if (qr) {
      const isAlipay = order.channel === 'alipay'
      payTitle.value = isAlipay ? '支付宝支付' : '微信支付'
      payHint.value = isAlipay ? '请使用支付宝扫码完成支付' : '请使用微信扫码支付'
      payUrl.value = qr
      payOpen.value = true
      startPoll()
    } else if (order.dev_pay) {
      const ok = await confirmDialog({
        title: '开发入账',
        message: '未配置支付渠道，是否模拟支付成功？',
        confirmText: '确认入账'
      })
      if (ok) {
        await devPay(order.order_id)
        toast('入账成功')
        await refresh()
        await loadOrders(true)
        await loadTx(true)
      }
    } else {
      toast('未返回支付链接，请配置微信或支付宝')
    }
  } catch { /* toast */ }
  finally {
    busy.value = false
  }
}

watch(tab, (v) => {
  if (v === 'orders' && !orders.value.length) loadOrders(true)
  if (v === 'tx' && !txs.value.length) loadTx(true)
})

watch(payOpen, (open) => {
  if (!open) stopPoll()
})

onMounted(async () => {
  await Promise.all([refresh(), loadMeta(), loadOrders(true)])
})

onUnmounted(stopPoll)
</script>

<style scoped>
.wallet {
  height: 100%;
  overflow: auto;
  padding: 28px 24px 48px;
}
.head { margin-bottom: 20px; }
h1 {
  margin: 0;
  font-family: var(--serif);
  font-size: 32px;
}
.sub {
  margin: 6px 0 0;
  color: var(--text-3);
  font-size: 14px;
}
.narrow {
  max-width: 480px;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 18px;
}
.card {
  background: var(--surface);
  border-radius: 16px;
  padding: 18px 18px 16px;
  box-shadow: var(--shadow);
}
.card.wide { max-width: none; }
.card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.label, h2 {
  margin: 0 0 12px;
  font-size: 15px;
  color: var(--text-2);
  font-weight: 650;
}
.card-top .label { margin: 0; }
.balance {
  margin: 8px 0 0;
  font-family: var(--serif);
  font-size: 40px;
  line-height: 1.1;
}
.error { color: var(--danger); margin: 10px 0 0; font-size: 14px; }
.channels {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}
.channel {
  min-height: 72px;
  border-radius: 12px;
  border: 2px solid var(--line);
  background: var(--paper);
  font-weight: 650;
  font-size: 16px;
}
.channel.wechat.on {
  border-color: #07c160;
  background: rgba(7, 193, 96, 0.1);
  color: #07c160;
}
.channel.alipay.on {
  border-color: #1677ff;
  background: rgba(22, 119, 255, 0.1);
  color: #1677ff;
}
.channel.on:not(.wechat):not(.alipay) {
  border-color: var(--brass);
  background: rgba(166, 124, 61, 0.12);
  color: var(--brass);
}
.presets {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}
.preset {
  height: 48px;
  border: 0;
  border-radius: 12px;
  background: var(--paper-2);
  font-weight: 650;
  font-size: 16px;
}
.preset.on {
  background: rgba(166, 124, 61, 0.18);
  color: var(--brass);
  box-shadow: inset 0 0 0 2px var(--brass);
}
.amount-row {
  display: flex;
  gap: 10px;
}
.amount-field {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--paper-2);
  border-radius: 12px;
  padding: 0 12px;
  font-weight: 650;
}
.amount-field input {
  flex: 1;
  border: 0;
  background: transparent;
  padding: 12px 0;
  outline: none;
  min-width: 0;
  font-size: 16px;
}
.primary {
  border: 0;
  border-radius: 12px;
  padding: 0 20px;
  min-width: 96px;
  font-weight: 650;
  background: var(--brass);
  color: #1a140c;
}
.primary:hover:not(:disabled) { background: var(--brass-2); }
.primary:disabled, .ghost:disabled { opacity: 0.55; }
.ghost {
  border: 0;
  background: transparent;
  color: var(--teal);
  font-size: 14px;
  padding: 4px 0;
}
.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
  border-bottom: 1px solid var(--line);
}
.tabs button {
  border: 0;
  background: transparent;
  padding: 10px 12px;
  font-weight: 650;
  color: var(--text-3);
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
}
.tabs button.on {
  color: var(--brass);
  border-bottom-color: var(--brass);
}
.table-wrap { overflow: auto; }
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
th, td {
  text-align: left;
  padding: 10px 8px;
  border-bottom: 1px solid var(--line);
  white-space: nowrap;
}
th { color: var(--text-3); font-weight: 600; }
.title-cell {
  max-width: 280px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.empty {
  margin: 12px 0;
  color: var(--text-3);
  font-size: 14px;
}
.more { margin-top: 12px; }
@media (max-width: 720px) {
  .wallet { padding: 18px 14px 40px; }
  h1 { font-size: 26px; }
  .balance { font-size: 34px; }
}
</style>
