<template>
  <div>
    <h5>Amount Owing: {{ $currency(invoice.amount_cents / 100) }} {{ invoice.currency }}</h5>
    <div v-if="invoice.expiry_date">Due:
      {{ new Date(invoice.expiry_date * 1000).toLocaleString() }}
    </div>
    <hr>
    <div class="is-flex is-justify-content-center is-flex-direction-row is-flex-wrap-wrap">
      <div class="p-1" v-for="coin in coins">
        <div class="card p-3 text-center"
             style="width: 160px; cursor: pointer"
             :class="{'has-background-primary' : payment_coin === coin.symbol}"
             @click="payment_coin = coin.symbol">
          <h4>{{ coin.symbol }}</h4>
          <div style="font-size: 10pt;">{{ coin.name }}</div>
          <div class="p-3 text-center">
            <div v-if="coin.symbol.startsWith('t')" class="testnet">
              TESTNET
            </div>
            <img :src="`data:image/svg+xml;base64,${coin.icon}`" :alt="coin.name"/>
          </div>

          <div style="font-size: 10pt" class="mt-1">
            <div>Next Block Fee:</div>
            <div>{{ $currency(coin.fee_estimate) }} USD</div>
            <div>{{ Math.round(coin.fee_rate) }} sat/byte</div>
          </div>
        </div>
      </div>
    </div>
    <hr>
    <div class="text-center">
      <button class="button is-info" @click="create_payment"
              :disabled="payment_coin === null">
        Pay Now
      </button>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
export default {
  name: "InvoicePending",
  props: ['invoice', 'coins', 'payments'],
  data() {
    return {payment_coin: null}
  },
  computed: {
    active_payments() {
      if (this.payments === null) {
        return []
      }
      return this.payments.filter(e => {
        return e.status !== 'expired'
      })
    }
  },
  methods: {
    create_payment() {
      for (let payment of this.active_payments) {
        if (payment.symbol === this.payment_coin) {
          let remaining = (new Date(payment.expiry_date * 1000).getTime() - new Date().getTime()) / 1000 / 60
          if (remaining >= 5) {
            return this.$emit('activate', payment.id)
          }
          console.log(remaining)
        }
      }
      axios.put("/api/invoice", {token: this.invoice.token, payment_coin: this.payment_coin}).then(
          resp => {
            this.$emit('payment', resp.data.payment)
          }
      )
    }
  }
}
</script>


<style scoped>
.testnet {
  position: absolute;
  text-align: center;
  width: 100%;
  font-weight: bold;
  font-size: 16pt;
  color: crimson;
  text-shadow: 0 0 6px white;
  top: 40%;
  left: 0;
}
</style>
