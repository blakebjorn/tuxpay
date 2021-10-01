<template>
  <div>
    <button class="button is-primary" @click="go_back" v-if="show_back">Back</button>
    <div class="text-center" v-if="payment_status === null || (payment_status || {}).status === 'pending'">
      <img :src="payment.qr_code" class="img-fluid" :alt="payment.address" style="max-width: 400px;"/>
      <div>
        {{ payment.amount_coin }} {{ payment.symbol }} @ {{ payment.address }}
      </div>
      <div v-if="remaining">
        Payment expires in:
        <span v-if="remaining.days">{{ remaining.days }} days, </span>
        <span v-if="remaining.hours">{{ remaining.hours }} hours, </span>
        <span v-if="remaining.minutes">{{ remaining.minutes }} minutes, </span>
        <span v-if="remaining.seconds">{{ Math.round(remaining.seconds) }} seconds.</span>
      </div>
      <div v-else-if="remaining === 0">
        This payment address has expired
        <span v-if="invoice !== null"> - please go back and generate a new payment address</span>
      </div>
    </div>
    <div v-else-if="payment_status !== null" class="text-center">
      <div class="alert alert-secondary" v-if="payment_status.status === 'expired' || remaining === 0">
        This payment has expired
        <span v-if="invoice !== null"> - please go back and generate a new payment address</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "invoice-payment",
  props: ['invoice', 'payment'],
  data() {
    return {
      payment_status: null,
      remaining: null,
      websocket: {open: false, socket: null, payment_id: null}
    }
  },
  computed: {
    show_back() {
      if (this.invoice !== null) {
        return !(this.payment_status && this.payment_status.status in ["paid", "confirmed"]);

      }
      return false
    },
    transactions() {
      if (this.payment_status === null) {
        return []
      }
      return this.payment_status.transactions
    },
  },
  watch: {
    payment: function (n, o) {
      if (!!o || n.id !== o.id) {
        this.start_websocket()
      }
    }
  },
  mounted() {
    this.start_websocket()
    setInterval(this.counter, 250)
  },
  beforeUnmount() {
    clearInterval(this.counter)
  },
  methods: {
    counter() {
      const now = new Date().getTime() / 1000
      if (this.payment.expiry_date) {
        let remaining = this.payment.expiry_date - now
        if (remaining > 0) {
          let out = {days: 0, hours: 0, minutes: 0, seconds: 0}
          out.days = Math.floor(remaining / (60 * 60 * 24))
          remaining -= out.days * (60 * 60 * 24)

          out.hours = Math.floor(remaining / (60 * 60))
          remaining -= out.hours * (60 * 60)

          out.minutes = Math.floor(remaining / 60)
          remaining -= out.minutes * 60

          out.seconds = remaining
          this.remaining = out
          return
        } else if (remaining <= 0) {
          this.remaining = 0
        }
      }
      this.remaining = null
    },
    message_handler(e) {
      const resp = JSON.parse(e.data)
      if ("status" in resp) {
        this.payment_status = resp;
        if (resp.status === 'paid' || resp.status === 'confirmed'){
          this.$emit('payment', resp)
        }
      }
    },
    go_back() {
      if (this.websocket.socket) {
        this.websocket.socket.close()
      }
      this.$emit('back')
    },
    start_websocket() {
      if (this.websocket.socket) {
        this.websocket.socket.close()
      }

      let ws = new WebSocket((location.protocol === "https:" ? "wss://" : "ws://")
          + location.host + "/api/payment");
      ws.onopen = () => {
        this.websocket.open = true
        ws.send(JSON.stringify({uuid: this.payment.uuid}))
      };
      ws.onmessage = this.message_handler
      ws.onclose = () => {
        this.websocket.open = false
      }
      this.websocket.socket = ws
    }
  }
}
</script>


<style scoped>

</style>
