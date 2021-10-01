# Integration

Much of the information on this page will need to be supplemented with that found on
the [API documentation page](/redoc.html)

While not strictly necessary, there is a javascript SDK bundled with the payment server. The SDK is served via
the `/tuxpay.js` endpoint.

The general integration flow is similar to that of the Paypal pay button:

1. Server generates an invoice on the backend (or a raw payment if the payment coin is known)
2. Client includes the TuxPay JS SDK on their page and launches the payment modal using
   `TuxPay.render({arguments})` where `arguments` is an object containing (some of) the following data:
    - `payment_uuid` - the UUID of the payment object. Can also be passed in the query string under the key `uuid`
    - `invoice_token` - JWT token attached to the invoice object. Can also be present in the query string under the
      key `token`
    - `is_modal` - boolean, whether the payment window should be a dismissable modal
    - `redirect` - optional, URL to redirect to upon successful payment. Can also be passed to the query string.
3. The payment server hosts a blank HTML file containing the SDK at the path `/payment`, such that you can bounce
   customers directly to a payment interstitial using the link
   format `http://tuxpay.com/payment?token=XXXXXXX.YYYYYYY&redirect=cart_url`
4. Payment is verified by E-commerce backend/cart using admin API calls. If you aren't using an interstitial, you can
   subscribe to the 'payment' event listener in your cart,
   e.g. `document.addEventListener('payment', (evt => { CODE TO VERIFY TRANSACTION SERVER SIDE }))`
5. Client is notified of completed payment in the cart/checkout page.