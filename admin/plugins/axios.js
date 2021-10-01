export default function ({$axios, redirect, app}) {
  $axios.onRequest(config => {
    if (app.store.state.token && app.store.getters.authenticated) {
      config.headers.Authorization = `Bearer ${app.store.state.token}`
    }
  });
  $axios.onError(error => {
    if (error) {
      if (error.response) {
        if (error.response.status === 401) {
          if (app.store.getters.authenticated) {
            app.store.commit('clearToken')
            app.$toast.error("Please log in to continue", {duration: 3000});
          }
        } else if (error.response.status === 504) {
          app.$toast.error("Could not reach server. Please refresh the page or try again later", {duration: 5000});
        } else if (error.response.status === 404) {
          app.$toast.error("Error: Not Found", {duration: 5000});
        } else {
          if (error.response.data instanceof Blob) {
            error.response.data.text().then(resp => {
              try {
                let r = JSON.parse(resp)
                app.$toast.error("Error: " + r.error, {duration: 5000});
              } catch (e) {
                app.$toast.error("Error: Unknown response", {duration: 5000});
              }
            })
          } else {
            app.$toast.error("Error: " + error.response.data.error, {duration: 5000});
          }
        }
      } else {
        app.$toast.error("Error: No response from server", {duration: 5000});
      }
    }
  });
  $axios.onResponse(resp => {
    if (resp && resp.data) {
      if ("warning" in resp.data) {
        app.$toast.info(resp.data.warning, {duration: 3000});
      }
      if ("warnings" in resp.data) {
        app.$toast.info(resp.data.warnings, {duration: 3000});
      }
    }
  })
}
