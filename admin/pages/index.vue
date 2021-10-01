<template>
  <card-container title="TuxPay">
    <h3>Recent Invoices <span style="font-size: 12pt">(last 30 days)</span></h3>

    <table class="table text-center" v-if="summary">
      <thead>
      <tr>
        <th></th>
        <th class="table-primary">Created</th>
        <th class="table-success">Paid</th>
        <th class="table-secondary">Expired</th>
      </tr>
      </thead>
      <tbody>
      <tr>
        <th>#</th>
        <td class="table-primary">{{ summary.created.count }}</td>
        <td class="table-success">{{ summary.paid.count }}</td>
        <td class="table-secondary">{{ summary.expired.count }}</td>
      </tr>
      <tr>
        <th>$</th>
        <td class="table-primary">{{ $currency(summary.created.dollars) }}</td>
        <td class="table-success">{{ $currency(summary.paid.dollars) }}</td>
        <td class="table-secondary">{{ $currency(summary.expired.dollars) }}</td>
      </tr>
      </tbody>
    </table>

    <div v-if="summary && summary.open" class="mt-3">
      <h4>Open Invoices</h4>
      <table class="table table-striped table-hover">
        <thead>
        <tr>
          <th>#</th>
          <th>Created</th>
          <th>Expires</th>
          <th>Amount</th>
        </tr>
        </thead>
        <tbody>
        <nuxt-link tag="tr"
                   v-for="invoice in summary.open"
                   :key="invoice.id"
                   :to="`/invoices/${invoice.id}`"
                   style="cursor: pointer;"
        >
          <td>{{ invoice.id }}</td>
          <td>{{ $date_string(invoice.creation_date) }}</td>
          <td>{{ $date_string(invoice.expiry_date) }}</td>
          <td>{{ $currency(invoice.amount_cents / 100) }}</td>
        </nuxt-link>
        </tbody>
      </table>
    </div>

    <div v-if="summary && summary.expired.invoices" class="mt-3">
      <h4>Expired Invoices</h4>
      <table class="table table-striped">
        <thead>
        <tr>
          <th>#</th>
          <th>Created</th>
          <th>Expired</th>
          <th>Amount</th>
        </tr>
        </thead>
        <tbody>
        <nuxt-link tag="tr"
                   v-for="invoice in summary.expired.invoices"
                   :key="invoice.id"
                   :to="`/invoices/${invoice.id}`"
                   style="cursor: pointer;"
        >
          <td>{{ invoice.id }}</td>
          <td>{{ $date_string(invoice.creation_date) }}</td>
          <td>{{ $date_string(invoice.expiry_date) }}</td>
          <td>{{ $currency(invoice.amount_cents / 100) }}</td>
        </nuxt-link>
        </tbody>
      </table>
    </div>

  </card-container>
</template>

<script>
export default {
  name: "dashboard",
  data() {
    return {summary: null}
  },
  beforeMount() {
    this.$axios.get("/api/admin/dashboard").then(resp => {
      this.summary = resp.data
    })
  }
}
</script>

<style>

</style>
