# Test Invoice Email — Setup & Run

This document explains how to test invoice email sending locally.

Environment variables
- `SMTP_HOST` — SMTP host (default: `localhost`)
- `SMTP_PORT` — SMTP port (default: `25`)
- `SMTP_USER` — SMTP username (optional)
- `SMTP_PASSWORD` — SMTP password (optional)
- `SMTP_USE_TLS` — `true`/`false` (default `true`)
- `SMTP_FROM` — From address (default `no-reply@example.com`)
- `MERCHANT_EMAIL` — Merchant email to receive the merchant copy (required to test merchant email)
- `TEST_USER_EMAIL` — Email to use when creating a test order (optional)

Quick local SMTP for development
1. Run a local debug SMTP server (Python 3):

```bash
python -m smtpd -c DebuggingServer -n localhost:1025
```

2. Set environment variables (example PowerShell):

```powershell
$env:SMTP_HOST = 'localhost'
$env:SMTP_PORT = '1025'
$env:SMTP_USE_TLS = 'false'
$env:MERCHANT_EMAIL = 'merchant@example.com'
$env:TEST_USER_EMAIL = 'test-invoice@example.com'
```

Run the test-order script

From the `home/ubuntu/book_sales_website/scripts` folder run:

```bash
# activate your venv and set FLASK_APP if needed
python create_test_order_and_send.py --user-email test-invoice@example.com
```

Or use the Flask CLI to send invoices for an existing order ID:

```bash
flask send-invoice 123
```

Or call the debug HTTP endpoint (admin-only):

```bash
# enable endpoint in non-debug mode
$env:ENABLE_DEBUG_EMAIL_ENDPOINT = 'true'
curl -X POST http://127.0.0.1:5000/debug/send-invoice/123 -b cookiejar.txt
```

Check logs / SMTP server output for sent messages.