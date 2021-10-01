<template>
  <div>
    <div class="text-center">
      <div>Invoice Paid
        {{ new Date(invoice.payment_date * 1000).toLocaleDateString() }}
        {{ new Date(invoice.payment_date * 1000).toLocaleTimeString() }}
      </div>

      <div class="is-justify-content-center mt-2">
        <checkmark style="max-height: 100px;"/>
      </div>

      <div>
        Payment Address: {{ payment.address }}
      </div>

      <template v-if="payment.status !== 'confirmed'">
        <hr class="my-2">
        <div>Waiting for blockchain confirmations</div>
      </template>

      <button v-if="is_modal" @click="$emit('close')" class="button is-primary mt-2">
        Close
      </button>
      <a v-else-if="redirect" class="button is-primary mt-2" :href="redirect">
        Continue
      </a>
    </div>
  </div>
</template>

<script>
import Checkmark from "./Checkmark";

export default {
  name: "paid-interstitial",
  components: {Checkmark},
  props: ['invoice', 'payment', 'is_modal', 'redirect']
}
</script>

<style scoped>

</style>