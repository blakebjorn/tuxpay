export const state = () => ({
    locale: 'en-US',
    token: localStorage.getItem('token') || sessionStorage.getItem('token') || null
});

function parseJwt(token) {
    try {
        return JSON.parse(atob(token.split('.')[1]));
    } catch (e) {
        return null;
    }
}

export const mutations = {
    setToken(state, payload) {
        if (payload.remember) {
            localStorage.setItem('token', payload.token)
        } else {
            sessionStorage.setItem('token', payload.token)
        }
        state.token = payload.token
    },
    clearToken(state) {
        localStorage.removeItem('token')
        sessionStorage.removeItem('token')
        state.token = null
    }
};

export const actions = {};

export const getters = {
    authenticated: state => {
        if (state.token !== null) {
            const dat = parseJwt(state.token)
            if (dat) {
                return (dat.exp * 1000) > new Date().getTime()
            }
        }
        return false
    },
};
