import os, sys, json
from dotenv import load_dotenv

# Ensure project .env is loaded
proj_root = os.path.join(os.path.dirname(__file__), '..')
load_dotenv(os.path.join(proj_root, '.env'))

# Add project root to sys.path so we can import paypal_helpers
sys.path.insert(0, proj_root)
from paypal_helpers import create_payment

items = [
    {"name": "Sample Book - Quick Test", "sku": "quick-1", "price": "10.00", "currency": "USD", "quantity": 1}
]

result = create_payment(items, 10.00, "http://127.0.0.1:5000/execute-payment", "http://127.0.0.1:5000/payment-cancelled")
print(json.dumps(result, indent=2))
