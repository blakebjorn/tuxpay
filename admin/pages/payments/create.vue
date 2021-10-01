<template>
  <card-container title="Create Payment">
    <div class="row mb-3">
      <div>
        <div>Valuation Currency:</div>
        <input type="radio" v-model="is_fiat" :value="false"> Crypto
        <input type="radio" v-model="is_fiat" :value="true"> Fiat
      </div>

      <input-control class="col-sm-2" type="float" label="Amount ($)" v-model="payment.fiat_amount"
                     :disabled="!is_fiat"/>
      <input-control class="col-sm-2" type="float" label="Amount (coin)" v-model="payment.coin_amount"
                     :disabled="is_fiat"/>

      <input-control class="col-sm-2" type="select" label="Currency" v-model="payment.currency" v-if="currencies">
        <option :value="dollar" v-for="(conversion, dollar) in currencies">{{ dollar }}
          <span v-if="dollar !== 'USD'">({{ Math.round(conversion * 100) / 100 }} : 1)</span>
        </option>
      </input-control>

      <input-control class="col-sm-2" type="select" label="Currency" v-model="payment.symbol" v-if="coins">
        <option :value="coin.symbol" v-for="coin in coins">
          {{ coin.symbol }} - <span>{{ $currency(coin.fee_estimate) }} fees</span>
        </option>
      </input-control>
    </div>

    <div class="form-group mb-3">
      <label for="date-layout">Expiry Date</label>
      <div class="row" id="date-layout">
        <div class="col-sm-2"><input class="form-control" type="date" v-model="expiry_date"/></div>
        <div class="col-sm-2"><input class="form-control" type="time" v-model="expiry_time"/></div>
      </div>
    </div>

    <div class="row mb-3">
      <input-control class="col-lg-3" label="Invoice Name" v-model="payment.name"/>
    </div>

    <div class="row mb-3">
      <input-control class="col-lg-3" label="Customer Name" v-model="payment.customer_name"/>
      <input-control class="col-lg-3" label="Customer Email" v-model="payment.customer_email"/>
    </div>

    <div class="row">
      <input-control class="col-lg-6" type="textarea" label="Invoice Notes" v-model="payment.notes"/>
    </div>
    <div class="form-check">
      <label class="form-check-label" for="notes_html">
        HTML
      </label>
      <input class="form-check-input" type="checkbox" v-model="notes_is_html" id="notes_html">
    </div>


    <div class="row mt-3">
      <input-control class="col-lg-6" type="textarea" label="Invoice Contents" v-model="payment.contents"/>
    </div>
    <div class="form-check mb-3">
      <label class="form-check-label" for="contents_html">
        HTML
      </label>
      <input class="form-check-input" type="checkbox" v-model="contents_is_html" id="contents_html">
    </div>

    <template v-if="response === null">
      <loading-button :method="create"
                      :disabled="selected_coin === null ||
                      ((payment.fiat_amount || 0.0) <= 0.0 && (payment.coin_amount || 0.0) <= 0.0)"
                      text="Create"/>
    </template>
    <div v-else>
      <a :href="`/payment?uuid=${response.payment.uuid}`" class="btn btn-success" target="_blank">Pay Now</a>
    </div>
  </card-container>
</template>

<script>
export default {
  name: "create-partial-invoice",
  data() {
    return {
      is_fiat: false,
      payment: {
        amount: null,
        currency: 'USD',
        name: null,
        notes: null,
        contents: null
      },
      currencies: null,
      coins: null,
      expiry_date: null,
      expiry_time: "23:59",
      response: null,
      notes_is_html: false,
      contents_is_html: false
    }
  },
  beforeMount() {
    this.$axios.get("/api/coins").then(resp => {
      this.currencies = resp.data.currencies
      this.coins = resp.data.coins
    })
  },
  computed: {
    selected_coin() {
      if (!this.payment.symbol) {
        return null
      }
      for (let coin of this.coins) {
        if (coin.symbol === this.payment.symbol) {
          return coin
        }
      }
      return null
    },
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
      let pl = Object.assign({}, this.payment)
      if (this.is_fiat) {
        pl.amount_cents = pl.fiat_amount * 100
      } else {
        pl.amount_sats = pl.coin_amount * (10 ** this.selected_coin.decimals)
      }
      pl.expiry_date = (this.iso_expiry ? this.iso_expiry.getTime() / 1000 : null)
      delete pl.coin_amount
      delete pl.fiat_amount

      if (this.notes_is_html) {
        pl.notes_html = pl.notes.toString()
        delete pl.notes
      }
      if (this.contents_is_html) {
        pl.contents_html = pl.contents.toString()
        delete pl.contents
      }

      return this.$axios.post("/api/admin/payment", pl).then(resp => {
        this.$toast.success("Payment Created", {duration: 3000})
        this.response = resp.data
      })
    }
  }
}
</script>

<style scoped>

</style>
