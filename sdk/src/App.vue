<template>
  <div id="app">
    <div v-if="error">
      Error: {{ error }}
    </div>
    <invoice v-else-if="invoice_token || payment_uuid"
             :invoice="invoice"
             :payments="payments"
             :payment="payment"
             :coins="coins"
             :is_modal="is_modal"
             :redirect="redirect"
             v-on:payment="set_payment"
             v-on:close="close"
    />
    <template v-else>
      <div>Error: invoice/payment is undefined</div>
    </template>
  </div>
</template>

<script>
import Invoice from "@/components/Invoice";
import axios from "axios";

export default {
  name: 'App',
  props: ['payment_id', 'invoice_token', 'payment_uuid', 'is_modal', 'payment_details', 'redirect'],
  components: {Invoice},
  data() {
    return {invoice: null, payments: null, coins: null, payment: null}
  },
  methods: {
    set_payment(payment) {
      this.payment = payment
    },
    close() {
      this.$vm().unmount()
    }
  },
  created() {
    if (this.invoice_token) {
      axios.get("/api/invoice", {params: {token: this.invoice_token}}).then(resp => {
        this.invoice = resp.data.invoice
        this.coins = resp.data.coins
        this.payments = resp.data.payments
        if (['paid', 'confirmed'].includes(this.invoice.status)) {
          for (let payment of this.payments) {
            if (['paid', 'confirmed'].includes(payment.status)) {
              this.payment = payment
            }
          }
        }
      }, err => {
        this.error = "Could not load invoice"
      })
    } else if (this.payment_uuid) {
      axios.get('/api/payment', {params: {uuid: this.payment_uuid}}).then(resp => {
        this.invoice = resp.data.payment.invoice
        this.payment = resp.data.payment
      }, err => {
        this.error = "Could not load payment"
      })
    }
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;

  background-color: rgba(44, 62, 80, 0.5);

  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}
</style>
