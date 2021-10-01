<template>
  <card-container title="Payments">
    <n-link to="/payments/create" tag="a" class="btn btn-primary">Create New</n-link>
    <hr>
    <table v-if="payments !== null"
           class="table table-sm table-bordered">
      <thead>
      <tr>
        <th>Created</th>
        <th>Expires</th>
        <th>Coin</th>
        <th>Invoiced</th>
        <th>Paid</th>
        <th>Address</th>
      </tr>
      </thead>

      <tbody>
      <tr v-for="payment in payments"
          :class="{'table-success': payment.paid_amount_sats && payment.paid_amount_sats >= payment.amount_sats}"
      >
        <td>
          {{ new Date(payment.creation_date * 1000).toLocaleDateString() }}
          {{ new Date(payment.creation_date * 1000).toLocaleTimeString() }}
        </td>
        <td>
          {{ new Date(payment.expiry_date * 1000).toLocaleDateString() }}
          {{ new Date(payment.expiry_date * 1000).toLocaleTimeString() }}
        </td>
        <td>{{ payment.symbol }}</td>
        <td>{{ payment.amount_coin }}</td>
        <td><span v-if="payment.paid_amount_coin">{{ payment.amount_coin }}</span></td>
        <td>{{ payment.address }}</td>
      </tr>
      </tbody>
    </table>
  </card-container>
</template>

<script>
export default {
  name: "view-payments",
  data() {
    return {payments: null}
  },
  beforeMount() {
    this.$axios.get("/api/admin/payments").then(resp => {
      this.payments = resp.data
    })
  }
}
</script>

<style scoped>

</style>
