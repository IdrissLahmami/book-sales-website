# Test Invoice Email — Setup & Run

This document explains how to test invoice email sending locally.

Environment variables
- `EMAIL_PROVIDER` - `auto`/`mcp`/`sendgrid`/`smtp` (default: `auto`)
- `SMTP_HOST` — SMTP host (default: `localhost`)
- `SMTP_PORT` — SMTP port (default: `25`)
- `SMTP_USER` — SMTP username (optional)
- `SMTP_PASSWORD` — SMTP password (optional)
- `SMTP_USE_TLS` — `true`/`false` (default `true`)
- `SMTP_FROM` — From address (default `no-reply@example.com`)
- `SENDGRID_API_KEY` — Optional SendGrid fallback in `auto` mode
- `MERCHANT_EMAIL` — Merchant email to receive the merchant copy (required to test merchant email)
- `TEST_USER_EMAIL` — Email to use when creating a test order (optional)
- `MCP_EMAIL_SERVER_COMMAND` — MCP server command (default: `npx`)
- `MCP_EMAIL_SERVER_ARGS` — MCP server args (default: `-y resend-mcp`)
- `MCP_EMAIL_TOOL_NAME` — Optional MCP tool name override (for example `send_email`)
- `RESEND_API_KEY` — Resend API key (required in stdio mode)
- `SENDER_EMAIL_ADDRESS` — Verified sender address for Resend (recommended)
- `RESEND_INVOICE_TEMPLATE_ID` — Published Resend template ID for invoice sends

Use resend/resend-mcp
1. Configure this app to use Resend MCP first:

```powershell
$env:EMAIL_PROVIDER = 'mcp'
$env:MCP_EMAIL_SERVER_COMMAND = 'npx'
$env:MCP_EMAIL_SERVER_ARGS = '-y resend-mcp'
$env:RESEND_API_KEY = 're_xxxxxxxxx'
$env:SENDER_EMAIL_ADDRESS = 'no-reply@your-verified-domain.com'
```

2. Optional: pin the exact tool name after inspecting server tools:

```powershell
$env:MCP_EMAIL_TOOL_NAME = 'send_email'
```

In `EMAIL_PROVIDER=auto`, transport order is: MCP -> SendGrid -> SMTP.

Create a professional template in Resend and use it for invoices
1. Generate or update the invoice template via script:

```powershell
$env:RESEND_API_KEY = 're_xxxxxxxxx'
$env:SENDER_EMAIL_ADDRESS = 'billing@your-verified-domain.com'
python scripts/create_resend_invoice_template.py
```

2. Copy the returned `template_id` and set:

```powershell
$env:RESEND_INVOICE_TEMPLATE_ID = 'tpl_xxxxxxxxx'
```

3. Run invoice flow. When `RESEND_INVOICE_TEMPLATE_ID` is present, invoice emails
	use the published Resend template first and fall back to existing transport if needed.

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