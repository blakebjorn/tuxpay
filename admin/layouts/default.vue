<template>
  <div>
    <nav class="navbar navbar-expand-lg navbar-light bg-light">
      <div class="container-fluid">
        <a class="navbar-brand" href="#"><img src="~/static/logo-sm.jpg" alt="logo" height="30px"/>TuxPay</a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarSupportedContent"
                aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarSupportedContent">
          <ul class="navbar-nav me-auto mb-2 mb-lg-0">
            <li class="nav-item">
              <n-link to="/" class="nav-link" :class="{active : $route.path === '/'}">Home</n-link>
            </li>
            <li class="nav-item">
              <n-link to="/invoices" class="nav-link" :class="{active : $route.path === '/invoices'}">Invoices</n-link>
            </li>
            <li class="nav-item">
              <n-link to="/payments" class="nav-link" :class="{active : $route.path === '/payments'}">Payments</n-link>
            </li>
          </ul>
        </div>
      </div>
    </nav>

    <div class="py-3">
      <authenticate v-if="!authenticated"/>
      <Nuxt v-else/>
    </div>
  </div>
</template>

<style>

</style>
<script>
import Authenticate from "@/components/Authenticate";

export default {
  name: "default-layout",
  components: {Authenticate},
  computed:{
    authenticated(){
      return this.$store.state.token && this.$store.getters.authenticated
    }
  }
}
</script>
