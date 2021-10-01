<template>
  <button class="btn pr-2" :class="`btn-`+color" @click="handler" :disabled="disabled || active">
        <span style="white-space: nowrap;">
            <span :style="{paddingLeft : (active ? `0px` : `8px`),
                   paddingRight : (active ? `0px` : `2px`)}">
              <template v-if="text">{{ text }}</template>
              <slot v-else name="content"/>
            </span>
            <span class="spinner"
                  :style="{visibility: (active? `visible` : `hidden`),
                          maxWidth: (active ? null : 0)}"
                  style="margin-bottom: -5px; margin-top:2px;"/>
        </span>
  </button>
</template>

<script>
export default {
  name: "LoadingButton",
  props: {
    text: null,
    color: {type: String, default: 'primary'},
    method: null,
    method_data: null,
    disabled: {type: Boolean, default: false},
  },
  data() {
    return {
      active: false
    }
  },
  methods: {
    handler() {
      if (this.method !== undefined && this.method !== null) {
        this.active = true;
        if (this.method_data !== null) {
          this.method(this.method_data).then(() => {
            this.active = false
          }, () => {
            this.active = false
          })
        } else {
          this.method().then(() => {
            this.active = false
          }, () => {
            this.active = false
          })
        }
      }
    }
  }
}
</script>

<style scoped>
.spinner {
  border: 5px solid #f3f3f3; /* Light grey */
  border-top: 5px solid #3498db; /* Blue */
  border-radius: 50%;
  width: 1.2em;
  height: 1.2em;
  padding: 0;
  display: inline-block;
  /*margin-left: auto;*/
  animation: spin 2s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>