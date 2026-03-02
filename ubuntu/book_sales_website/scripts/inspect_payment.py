import os, sys, json
from dotenv import load_dotenv
import paypalrestsdk

if len(sys.argv) < 2:
    print('Usage: inspect_payment.py <PAYMENT_ID>')
    sys.exit(2)

payment_id = sys.argv[1]
# Load project .env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

paypalrestsdk.configure({
    'mode': os.environ.get('PAYPAL_MODE', 'sandbox'),
    'client_id': os.environ.get('PAYPAL_CLIENT_ID'),
    'client_secret': os.environ.get('PAYPAL_CLIENT_SECRET')
})

try:
    p = paypalrestsdk.Payment.find(payment_id)
    print(json.dumps(p.to_dict(), indent=2))
except Exception as e:
    print('ERROR', str(e))
    sys.exit(1)
