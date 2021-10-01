# Usage

After installation, the server will be launched on port 8000 by default.

The payment server has a built-in admin panel that can be reached at the URL `/admin` - you will need to authenticate
with the email and password provided when running the `setup.py` script. From here you can create new invoices or
payment requests

#### Invoices

The invoice are the high level payment object used by TuxPay. An invoice consists of a fiat amount, and an expiration
date. Until an invoice expires, any number of payment addresses can be created against it, payment addresses will be
watched until they expire, and any completed payment will mark the parent invoice as completed.

Upon creation in the admin panel, each invoice will provide a link that can be used to pay the invoice which can be
distributed to customers.

#### Payment

Payments are low level payment objects - each payment consists of a payment currency and a coin amount. When created
from an invoice, the payment amount in coin is inferred from the fiat amount of the invoice, and set to expire within a
short window (configurable; 15m by default). If a payment expires, a new address can be created against the invoice.
When payments are created from the API/Admin panel, a parent invoice object is created automatically and the payment is attached to it.