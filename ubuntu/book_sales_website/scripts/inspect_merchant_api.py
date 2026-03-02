import os, sys, json
from dotenv import load_dotenv
import requests

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
CLIENT = os.environ.get('PAYPAL_CLIENT_ID')
SECRET = os.environ.get('PAYPAL_CLIENT_SECRET')
MODE = os.environ.get('PAYPAL_MODE','sandbox')

if not CLIENT or not SECRET:
    print('PAYPAL_CLIENT_ID/SECRET not set in .env')
    sys.exit(2)

base = 'https://api.sandbox.paypal.com' if MODE=='sandbox' else 'https://api.paypal.com'

auth = requests.auth.HTTPBasicAuth(CLIENT, SECRET)
resp = requests.post(base + '/v1/oauth2/token', auth=auth, data={'grant_type':'client_credentials'})
if resp.status_code != 200:
    print('Failed to obtain access token:', resp.status_code, resp.text)
    sys.exit(1)

token = resp.json().get('access_token')
print('Access token acquired (truncated):', token[:8]+'...')

headers = {'Authorization': f'Bearer {token}', 'Content-Type':'application/json'}

# 1) Get web experience profiles (may contain brand_name)
r = requests.get(base + '/v1/payment-experience/web-profiles', headers=headers)
print('\n=== Web Experience Profiles ===\n', r.status_code)
try:
    print(json.dumps(r.json(), indent=2))
except Exception:
    print(r.text)

# 2) Get basic app info if available via /v1/identity/oauth2/userinfo?schema=paypalv1.1 (requires user token) - skip

# 3) Print a note about merchant_id discovered from recent payments file
print('\nNote: You can also inspect a specific payment resource with inspect_payment.py to see payee/merchant_id.')
