import os, time, sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except Exception:
    print('Playwright not installed. Run: pip install playwright')
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]
SANDBOX_EMAIL = os.environ.get('SANDBOX_EMAIL', 'John.Doe997@personal.example.com')
SANDBOX_PASSWORD = os.environ.get('SANDBOX_PASSWORD', 'Access#001')
LOGIN_URL = os.environ.get('LOCAL_LOGIN_PAYPAL_URL', 'http://127.0.0.1:5000/login/paypal')

print('Using login URL:', LOGIN_URL)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    try:
        page.goto(LOGIN_URL)
        time.sleep(2)

        # Try to detect common PayPal login iframe or direct form
        # If PayPal shows a login form directly, fill it; otherwise try to find iframe then fill inside it.
        def try_fill_selectors(selectors, value):
            for sel in selectors:
                try:
                    el = page.query_selector(sel)
                    if el:
                        el.fill(value)
                        return True
                except Exception:
                    continue
            return False

        email_selectors = ['input#email', 'input[type=email]', 'input[name=email]', 'input[name=login_email]']
        pwd_selectors = ['input#password', 'input[type=password]', 'input[name=password]']

        filled = try_fill_selectors(email_selectors, SANDBOX_EMAIL)
        time.sleep(0.5)
        filled_pwd = try_fill_selectors(pwd_selectors, SANDBOX_PASSWORD)

        # Click login or continue buttons
        possible_btns = ["button#btnLogin", "button[type=submit]", "input[type=submit]", "button:has-text('Log In')", "button:has-text('Log in')", "button:has-text('Next')", "button:has-text('Continue')"]
        clicked = False
        for b in possible_btns:
            try:
                btn = page.query_selector(b)
                if btn:
                    btn.click()
                    clicked = True
                    break
            except Exception:
                continue

        print('Filled email:', filled, 'Filled pwd:', filled_pwd, 'Clicked submit:', clicked)
        print('Waiting for user to complete 2FA or approval if prompted. Browser will stay open.')
        input('Press Enter in terminal to close browser and finish...')

    except Exception as e:
        print('Automation error:', e)
    finally:
        browser.close()

print('Done')
