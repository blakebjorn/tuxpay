<template>
  <div class="container align-content-center">
    <card-container title="Authenticate">
      <div>
        <input-control v-model="email" label="Email" inline="1"/>
        <input-control v-model="password" label="Password" type='password' inline="1"/>
        <div class="form-check">
          <input class="form-check-input" type="checkbox" v-model="remember" id="remember">
          <label class="form-check-label" for="remember">
            Remember Me
          </label>
        </div>

        <loading-button :method="authenticate" text="Sign In" :disabled="!email || !password"/>
      </div>
    </card-container>
  </div>
</template>

<script>
export default {
  name: "Authenticate",
  data() {
    return {email: null, password: null, remember: false}
  },
  methods: {
    authenticate() {
      return this.$axios.post("/api/authenticate",
          {email: this.email, password: this.password, remember: this.remember}).then(resp => {
        this.$store.commit('setToken', {token: resp.data.token, remember: this.remember})
      }, err => {
        if (err.response.status === 401) {
          this.$toast.error("Invalid email or password", {duration: 3000})
        } else {
          this.$toast.error("Error submitting request", {duration: 3000})
        }
      })
    }
  }
}
</script>

<style scoped>

</style>
