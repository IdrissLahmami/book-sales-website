import os
import re
import time
import sys
from pathlib import Path

# Use Playwright to automate PayPal sandbox approval
try:
    from playwright.sync_api import sync_playwright
except Exception as e:
    print('Playwright not installed. Install with: pip install playwright')
    sys.exit(2)

# Config
ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / 'debug_paypal.log'
# Sandbox buyer credentials (created by create_john_doe_user.py)
SANDBOX_EMAIL = os.environ.get('SANDBOX_EMAIL', 'John.Doe997@personal.example.com')
SANDBOX_PASSWORD = os.environ.get('SANDBOX_PASSWORD', 'test123')

# Extract latest approval URL from debug_paypal.log
if not LOG_PATH.exists():
    print('Log file not found:', LOG_PATH)
    sys.exit(1)

with open(LOG_PATH, 'r', encoding='utf-8', errors='ignore') as f:
    data = f.read()

m = re.findall(r"approval_url': '([^']+)'", data)
if not m:
    print('No approval_url found in log')
    sys.exit(1)

approval_url = m[-1]
print('Found approval URL:', approval_url)

# Automation flow
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    try:
        page.goto(approval_url)
        time.sleep(2)

        # Attempt to fill login form
        # Try several common selectors
        email_selectors = ['input#email', 'input[type=email]', 'input[name=email]', 'input[name=login_email]']
        pwd_selectors = ['input#password', 'input[type=password]', 'input[name=password]']
        login_btn_selectors = ["button#btnLogin", "button[name=login]", "button[type=submit]", "input[type=submit]", "button:has-text('Log In')", "button:has-text('Log in')"]

        filled = False
        for sel in email_selectors:
            try:
                el = page.query_selector(sel)
                if el:
                    el.fill(SANDBOX_EMAIL)
                    filled = True
                    break
            except Exception:
                continue
        for sel in pwd_selectors:
            try:
                el = page.query_selector(sel)
                if el:
                    el.fill(SANDBOX_PASSWORD)
                    break
            except Exception:
                continue

        # Click login
        clicked = False
        for sel in login_btn_selectors:
            try:
                btn = page.query_selector(sel)
                if btn:
                    btn.click()
                    clicked = True
                    break
            except Exception:
                continue

        # Wait for post-login
        time.sleep(4)

        # Try to click Approve/Pay/Continue buttons
        approve_texts = ['Approve', 'Pay Now', 'Continue', 'Agree & Continue', 'Agree and Continue', 'Confirm', 'Pay with PayPal']
        clicked_approve = False
        for t in approve_texts:
            try:
                btn = page.query_selector(f"button:has-text('{t}')")
                if btn:
                    btn.click()
                    clicked_approve = True
                    print('Clicked approve button with text:', t)
                    break
            except Exception:
                continue

        if not clicked_approve:
            # fallback: click any input[type=submit]
            try:
                s = page.query_selector('input[type=submit]')
                if s:
                    s.click()
                    print('Clicked fallback submit')
                    clicked_approve = True
            except Exception:
                pass

        if clicked_approve:
            print('Approval attempted, waiting for redirect...')
            time.sleep(6)
            print('Done — check server logs for execute-payment entries.')
        else:
            print('Could not find approve button; manual approval may be required.')

    except Exception as e:
        print('Automation error:', e)
    finally:
        # Keep browser open for manual inspection; wait for user to press Enter to close
        print('Automation finished. The browser will remain open for manual inspection.')
        try:
            input('Press Enter to close the browser and exit...')
        except Exception:
            # If input is not available, sleep briefly then close
            time.sleep(60)
        browser.close()

print('Automation script finished')
