<template>
  <div class="form-group">
    <template v-if="type === `layout`">
      <label :for="identifier">{{ label || `&nbsp;` }}</label>
      <div :id="identifier">
        <slot></slot>
      </div>
    </template>
    <template v-if="type === `select`">
      <label :for="identifier">{{ label || `&nbsp;` }}</label>
      <select :id="identifier" :name="name"
              :value="clean_value"
              :required="required !== undefined"
              :disabled="disabled"
              @input="callback($event)"
              class="form-control form-select custom-select">
        <slot/>
      </select>
    </template>
    <template v-else>
      <label :for="identifier">{{ label || `&nbsp;` }}</label>
      <textarea v-if="type === `textarea`"
                :name="name"
                :id="identifier"
                :rows="rows"
                class="form-control"
                :placeholder="placeholder"
                :value="clean_value"
                :required="required !== undefined"
                :disabled="disabled"
                @input="callback($event)"></textarea>
      <input v-else
             :type="([`float`, `int`].includes(type) ? `number` : type) || `text`"
             :name="name"
             :id="identifier"
             class="form-control"
             :class="{'form-check-input': type==='checkbox'}"
             :placeholder="placeholder"
             :value="clean_value"
             @input="callback($event)"
             :required="required !== undefined"
             :disabled="disabled"
             :maxlength="maxlength"
             :step="(type === `float` ? 0.01 : 1)"/>
    </template>
  </div>
</template>

<script>
export default {
  name: "InputControl",
  props: ['label', 'value', 'type', 'placeholder', 'required', 'inline', 'disabled', 'maxlength', 'rows'],
  data() {
    return {identifier: null}
  },
  computed: {
    name() {
      return (this.label || "").replace(/\s/g, "-").toLowerCase()
    },
    clean_value() {
      if (this.type === `date` && this.value && this.value.toString().includes("T")) {
        // coerce ISO date strings to HTML (truncate time component)
        return this.value.split("T")[0];
      }
      if (this.type === `check`) {
        return !!this.value
      }
      return this.value
    }
  },
  methods: {
    callback(event) {
      let value = (event.target ? event.target.value : event)
      if (this.type === `date`) {
        value = (event.target.valueAsDate !== null
          ? event.target.valueAsDate.toISOString().split("T")[0]
          : event.target.value)
      }
      this.$emit('input', value)
    }
  },
  beforeMount() {
    this.identifier = this.name + "-" + Math.random().toString(36).replace(/[^a-z]+/g, '');
  }

}
</script>
