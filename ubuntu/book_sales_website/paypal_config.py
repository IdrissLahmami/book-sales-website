# PayPal Integration Configuration

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# PayPal Configuration
PAYPAL_MODE = os.environ.get('PAYPAL_MODE', 'sandbox')  # sandbox or live
PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID', 'YOUR_SANDBOX_CLIENT_ID')
PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET', 'YOUR_SANDBOX_CLIENT_SECRET')

# Instructions for setting up PayPal Developer Account
"""
To set up PayPal integration:

1. Create a PayPal Developer Account:
   - Go to https://developer.paypal.com/ and sign up or log in
   - Navigate to the Dashboard

2. Create a Sandbox Account:
   - Go to Sandbox > Accounts
   - Create both Business (merchant) and Personal (customer) test accounts
   - Save the credentials for testing

3. Create a PayPal App:
   - Go to My Apps & Credentials
   - Click "Create App" under the REST API apps section
   - Name your app (e.g., "Book Sales Website")
   - Select "Merchant" as the app type
   - Click "Create App"
   - Copy the Client ID and Secret

4. Set Environment Variables:
   - Create a .env file in the project root
   - Add the following variables:
     PAYPAL_MODE=sandbox
     PAYPAL_CLIENT_ID=your_client_id
     PAYPAL_CLIENT_SECRET=your_client_secret

5. Test the Integration:
   - Use the sandbox accounts to test the payment flow
   - Verify that orders are created and payments are processed correctly
   - Check that download links are activated after successful payment
"""
