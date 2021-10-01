<template>
  <card-container title="Invoices">
    <n-link to="/invoices/create" tag="a" class="btn btn-primary">Create New</n-link>
    <hr>
    <table class="table table-bordered table-sm" v-if="invoices !== null">
      <thead>
      <tr>
        <th>Name</th>
        <th>Created</th>
        <th>Due</th>
        <th>Amount</th>
        <th>Status</th>
        <th></th>
      </tr>
      </thead>
      <tbody>
      <tr v-for="invoice in invoices"
          :class="{'table-success' : invoice.status === 'confirmed', 'table-danger' : invoice.status === 'expired'}">
        <td>
          {{ invoice.name }}
        </td>
        <td>
          {{ new Date(invoice.creation_date * 1000).toLocaleDateString() }}
        </td>
        <td>
          <template v-if="invoice.expiry_date">
            {{ new Date(invoice.expiry_date * 1000).toLocaleDateString() }}
          </template>
        </td>
        <td>${{ (invoice.amount_cents / 100).toLocaleString() }} {{ invoice.currency }}</td>
        <td>{{ invoice.status }}</td>
        <td>
          <n-link v-if="invoice.status !== 'pending'" class="btn btn-outline-primary btn-sm"
                  :to="`/invoices/${invoice.id}`">View
          </n-link>
          <a v-else class="btn btn-primary btn-sm"
             :href="`/payment?token=${invoice.token}`">Pay
          </a>
          <a class="btn btn-info btn-sm"
             :href="`/api/invoice/download?invoice_id=${invoice.id}`"
             target="_blank">PDF
          </a>
        </td>
      </tr>
      </tbody>
    </table>
  </card-container>
</template>

<script>
export default {
  name: "view-invoice",
  data() {
    return {invoices: null}
  },
  beforeMount() {
    this.$axios.get("/api/admin/invoice").then(resp => {
      this.invoices = resp.data
    })
  }
}
</script>

<style scoped>

</style>
