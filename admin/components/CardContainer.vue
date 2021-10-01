<template>
  <div :class="{container: container}">
    <div class="card">
      <div class="card-header">
        <h2>{{ title }}</h2>
      </div>
      <div class="card-body">
        <slot/>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "CardContainer",
  props: {'container': {default: true}, 'title': {default: ''}}
}
</script>

<style scoped>

</style>
