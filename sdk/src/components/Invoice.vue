<template>
  <div class="container is-max-desktop px-3 py-5 is-flex is-justify-content-center">
    <div class="card is-flex-grow-1">
      <div class="card-header">
        <div class="card-header-title pt-2 pb-1">TuxPay Invoice</div>
        <div class="is-justify-content-end" v-if="is_modal">
          <button @click="$emit('close')" class="button is-light is-fullheight">X</button>
        </div>
      </div>
      <div class="card-content">
        <div v-if="error">
          {{ error }}
        </div>
        <div v-else-if="invoice === null && payment === null">
          Loading
        </div>
        <div v-else-if="payment !== null && (payment.status === 'paid' || payment.status === 'confirmed')">
          <paid-interstitial :invoice="invoice"
                             :payment="payment"
                             :is_modal="is_modal"
                             :redirect="redirect"
                             v-on:close="$emit('close')"/>
        </div>
        <div v-else-if="payment !== null" class="px-2">
          <invoice-payment :invoice="invoice" :payment="payment"
                           v-on:payment="handle_payment"
                           v-on:back="payment = null"/>
        </div>
        <template v-else>
          <div v-if="invoice.status === 'pending'">
            <invoice-pending :invoice="invoice"
                             :payments="payments"
                             :coins="coins"
                             v-on:activate="activate_payment"
                             v-on:payment="payment_created"/>
          </div>
          <div v-else-if="invoice.status === 'expired'"
               class="alert alert-secondary">
            This Invoice has expired unpaid
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script>

import InvoicePending from "@/components/InvoicePending";
import InvoicePayment from "@/components/InvoicePayment";
import PaidInterstitial from "./PaidInterstitial";

export default {
  name: "invoice",
  components: {PaidInterstitial, InvoicePayment, InvoicePending},
  props: [
    'is_modal',
    "invoice",
    "payments",
    "payment",
    "coins",
    "redirect"
  ],
  data() {
    return {
      error: null
    }
  },
  computed: {},
  mounted() {
  },
  methods: {
    payment_created(payment) {
      this.payments.push(payment)
      this.activate_payment(payment.id)
    },
    activate_payment(payment_id) {
      for (let payment of this.payments) {
        if (payment.id === payment_id) {
          return this.$emit('payment', payment)
        }
      }
    },
    handle_payment(response) {
      this.payment.status = response.status
      this.payment.transactions = response.transactions
      if (['paid', 'confirmed'].includes(response.status)) {
        this.invoice.payment_date = new Date().getTime() / 1000
      }
      document.dispatchEvent(new CustomEvent('payment', {
        detail: {
          payment: Object.assign({}, this.payment),
          invoice: Object.assign({}, this.invoice)
        }
      }))
    }
  }
}
</script>
