<template>
  <card-container title="Create Invoice">
    <div class="row mb-3">
      <input-control class="col-lg-2" type="float" label="Amount" v-model="invoice.amount"/>
      <input-control class="col-lg-2" type="select" label="Currency"
                     v-model="invoice.currency" v-if="currencies">
        <option :value="dollar" v-for="(conversion, dollar) in currencies">{{ dollar }}
          <span v-if="dollar !== 'USD'">({{ Math.round(conversion * 100) / 100 }} : 1)</span></option>
      </input-control>
    </div>

    <div class="form-group mb-3">
      <label for="date-layout">Expiry Date</label>
      <div class="row" id="date-layout">
        <div class="col-lg-2"><input class="form-control" type="date" v-model="expiry_date"/></div>
        <div class="col-lg-2"><input class="form-control" type="time" v-model="expiry_time"/></div>
      </div>
    </div>

    <div class="row mb-3">
      <input-control class="col-lg-3" label="Invoice Name" v-model="invoice.name"/>
    </div>

    <div class="row mb-3">
      <input-control class="col-lg-3" label="Customer Name" v-model="invoice.customer_name"/>
      <input-control class="col-lg-3" label="Customer Email" v-model="invoice.customer_email"/>
    </div>

    <div class="row">
      <input-control class="col-lg-6" type="textarea" label="Invoice Notes" v-model="invoice.notes"/>
    </div>
    <div class="form-check">
      <label class="form-check-label" for="notes_html">
        HTML
      </label>
      <input class="form-check-input" type="checkbox" v-model="notes_is_html" id="notes_html">
    </div>


    <div class="row mt-3">
      <input-control class="col-lg-6" type="textarea" label="Invoice Contents" v-model="invoice.contents"/>
    </div>
    <div class="form-check mb-3">
      <label class="form-check-label" for="contents_html">
        HTML
      </label>
      <input class="form-check-input" type="checkbox" v-model="contents_is_html" id="contents_html">
    </div>

    <template v-if="response === null">
      <loading-button :method="create"
                      :disabled="(invoice.amount || 0.0) <= 0.0 || iso_expiry < new Date()"
                      text="Create"/>
    </template>
    <template v-else>
      <div>
        <a class="btn btn-success" :href="`/payment?token=${response.invoice.token}`" target="_blank">Pay Now</a>
      </div>
    </template>
  </card-container>
</template>

<script>
export default {
  name: "create-partial-invoice",
  data() {
    return {
      invoice: {
        amount: null,
        currency: 'USD',
        name: null,
        notes: null,
        contents: null
      },
      currencies: null,
      expiry_date: null,
      expiry_time: "23:59",
      response: null,
      notes_is_html: false,
      contents_is_html: false,
    }
  },
  beforeMount() {
    this.$axios.get("/api/coins").then(resp => {
      this.currencies = resp.data.currencies
    })
  },
  computed: {
    iso_expiry() {
      if (this.expiry_date && this.expiry_time) {
        let seconds = parseInt(this.expiry_time.split(":")[0]) * 3600 * 1000
        seconds += parseInt(this.expiry_time.split(":")[1]) * 60 * 1000
        let ts = new Date(this.expiry_date).getTime() + seconds + (new Date().getTimezoneOffset() * 60 * 1000)
        return new Date(ts)
      }
    }
  },
  methods: {
    create() {
      let pl = Object.assign({}, this.invoice)
      pl.amount_cents = Math.round(parseFloat(this.invoice.amount) * 100)
      pl.expiry_date = (this.iso_expiry ? this.iso_expiry.getTime() / 1000 : null)
      if (this.notes_is_html) {
        pl.notes_html = pl.notes.toString()
        delete pl.notes
      }
      if (this.contents_is_html) {
        pl.contents_html = pl.contents.toString()
        delete pl.contents
      }
      return this.$axios.post("/api/admin/invoice", pl).then(resp => {
        this.$toast.success("Invoice Created", {duration: 3000})
        this.response = resp.data
      })
    }
  }
}
</script>

<style scoped>

</style>
