const createApp = require('vue').createApp
const App = require('./App.vue').default

require('@/assets/main.scss');

function RenderTux(data) {
    let params = (new URL(document.location)).searchParams;
    data = data || {}
    let app_data = {
        payment_uuid: data.payment_uuid || params.get("uuid"),
        invoice_token: data.invoice_token || params.get("token"),
        payment_details: data.payment_details,
        is_modal: data.is_modal || false,
        redirect: data.redirect || params.get("redirect"),
    }

    const app = createApp(App, app_data)

    app.mixin({
        methods: {
            $vm() {
                return app
            },
            $currency(value, locale = null, _default = null) {
                if (typeof value === 'string' && !isNaN(parseFloat(value))) {
                    value = parseFloat(value);
                }
                if (value === null || value === undefined) {
                    return _default;
                }
                const formatter = new Intl.NumberFormat(undefined, {
                    style: 'currency',
                    currency: 'USD',
                    currencyDisplay: 'narrowSymbol'

                    // These options are needed to round to whole numbers if that's what you want.
                    //minimumFractionDigits: 0, // (this suffices for whole numbers, but will print 2500.10 as $2,500.1)
                    //maximumFractionDigits: 0, // (causes 2500.99 to be printed as $2,501)
                });

                return formatter.format(value); /* $2,500.00 */
            }
        }
    })
    // app.use(VueAxios, axios)
    app.mount('#tuxpay')
}

if (process.env.NODE_ENV !== 'production') {
    RenderTux({})
}

function TuxPay() {
}

TuxPay.render = RenderTux
module.exports = TuxPay;