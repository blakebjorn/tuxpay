<template>
  <card-container title="Invoice Details">
    <template v-if="invoice">


      <table class="table table-bordered">
        <thead>
        <tr>
          <th colspan="2"><h4>Invoice #{{ invoice.id }}</h4></th>
        </tr>
        </thead>
        <tbody>
        <tr>
          <th>Name</th>
          <td>{{ invoice.name }}</td>
        </tr>
        <tr>
          <th>Created</th>
          <td>{{ $date_string(invoice.creation_date) }}</td>
        </tr>
        <tr>
          <th>Amount</th>
          <td>{{ $currency(invoice.amount_cents / 100) }} {{ invoice.currency }}</td>
        </tr>
        <tr>
          <th>Status</th>
          <td>{{ invoice.status }}</td>
        </tr>
        <tr v-if="invoice.status === 'paid' || invoice.status === 'confirmed'">
          <th>Paid</th>
          <td>{{ $date_string(invoice.payment_date) }}</td>
        </tr>
        <tr v-else>
          <th>{{ (invoice.status === 'expired' ? 'Expired' : 'Expires') }}</th>
          <td>{{ $date_string(invoice.expiry_date) }}</td>
        </tr>
        </tbody>
      </table>

      <div v-if="invoice.notes" class="mt-3">
        <h5>Notes</h5>
        <div>{{ invoice.notes }}</div>
      </div>

      <div v-if="invoice.contents" class="mt-3">
        <h5>Contents</h5>
        <div>{{ invoice.contents }}</div>
      </div>

      <div v-if="payments" class="mt-3">
        <h5>Payments</h5>
        <table class="table table-sm">
          <thead>
          <tr>
            <th>Coin</th>
            <th>Amount</th>
            <th>Address</th>
            <th>Status</th>
            <th>Payment</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="payment in payments" :class="{
               'table-primary' : payment.paid_amount_sats > 0,
               'table-secondary' : payment.status === 'expired'
            }">
            <td>{{ payment.symbol }}</td>
            <td>{{ payment.amount_coin }}</td>
            <td>{{ payment.address }}</td>
            <td>{{ payment.status }}</td>
            <td>{{ payment.paid_amount_coin }} -
              {{ $date_string(payment.payment_date) }} {{ $time_string(payment.payment_date) }}</td>
          </tr>
          </tbody>
        </table>
      </div>
    </template>
  </card-container>
</template>

<script>
export default {
  name: "invoice-page",
  data() {
    return {invoice: null, payments: null}
  },
  beforeMount() {
    this.$axios.get(`/api/admin/invoice/${this.$route.params.id}`).then(resp => {
      this.invoice = resp.data.invoice
      this.payments = resp.data.payments
    })
  }
}
</script>

<style scoped>

</style>
