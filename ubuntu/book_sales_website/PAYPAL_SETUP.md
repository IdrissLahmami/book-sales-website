# PayPal Sandbox Testing - Quick Setup Guide

## 🎯 Quick Links
- **PayPal Developer Dashboard:** https://developer.paypal.com/dashboard/
- **Sandbox Accounts:** https://developer.paypal.com/dashboard/accounts
- **My Apps & Credentials:** https://developer.paypal.com/dashboard/applications

## 📝 Step-by-Step Setup

### 1. Create Developer Account (5 minutes)
1. Visit https://developer.paypal.com/
2. Click "Log in to Dashboard"
3. Sign in with your personal PayPal account (or create one)

### 2. Get Sandbox Test Accounts (Auto-created)
PayPal automatically creates test accounts for you:

**Default Sandbox Accounts:**
- **Business Account** (Merchant) - receives payments
- **Personal Account** (Buyer) - makes payments

**To view credentials:**
1. Go to Sandbox > Accounts
2. Click the "..." menu next to an account
3. Select "View/Edit Account"
4. Click "Account Credentials" tab
5. Note the email and password

### 3. Create REST API App (2 minutes)
1. Go to "My Apps & Credentials"
2. Ensure you're on the **"Sandbox"** tab
3. Click "Create App"
4. App Name: `Book Sales Website`
5. Click "Create App"
6. **COPY THESE VALUES:**
   - Client ID: `AXXXXXxxxxxxx...`
   - Secret: (click "Show" to reveal)

### 4. Configure .env File
Create or edit `.env` in your project root:

```env
PAYPAL_MODE=sandbox
PAYPAL_CLIENT_ID=paste_your_client_id_here
PAYPAL_CLIENT_SECRET=paste_your_secret_here
SECRET_KEY=your-random-secret-key
DATABASE_URI=sqlite:///booksales.db
```

**Important:** Restart the Flask server after updating .env!

### 5. Test Payment Flow

**Testing Steps:**
1. Open website: http://127.0.0.1:5000
2. Browse books and add one to cart
3. Go to checkout
4. Click "Pay with PayPal"
5. **Log in with your SANDBOX BUYER account**
   - Email: (from Sandbox Accounts page)
   - Password: (from Sandbox Accounts page)
6. Approve the payment
7. You'll be redirected back to the order confirmation page
8. Check your account - the book should now be available for download!

## 💡 Common Issues & Solutions

### Issue: "Invalid credentials" error
**Solution:** 
- Make sure you copied the correct Client ID and Secret
- Ensure you're using credentials from the "Sandbox" tab, not "Live"
- Restart the Flask server after updating .env

### Issue: Can't log in to PayPal during checkout
**Solution:**
- Use the BUYER sandbox account credentials (Personal account)
- Don't use your real PayPal account
- Find credentials: Sandbox > Accounts > View/Edit Account > Account Credentials

### Issue: Payment not processing
**Solution:**
- Check that PAYPAL_MODE=sandbox in .env
- Ensure both Client ID and Secret are correct
- Check the terminal for error messages

## 🔍 How to Find Your Sandbox Credentials

1. **PayPal Developer Dashboard:** https://developer.paypal.com/dashboard/
2. Click **"Sandbox > Accounts"** in the left menu
3. You'll see a list of test accounts
4. Click the **"..."** button next to any account
5. Select **"View/Edit Account"**
6. Go to **"Account Credentials"** tab
7. You'll see:
   - **Email Address:** Use this as username
   - **Password:** Click "Show" to reveal
   - **Account Type:** Business or Personal

## 🎨 Default Sandbox Account Types

**Business Account (Merchant):**
- Receives payments
- Used for testing as the seller
- Email format: `sb-xxxxx@business.example.com`

**Personal Account (Buyer):**
- Makes payments
- Used for testing as the customer
- Email format: `sb-xxxxx@personal.example.com`

## 🚀 Ready to Test!

Once configured:
1. ✅ .env file has your credentials
2. ✅ Flask server restarted
3. ✅ Sandbox buyer credentials ready
4. ✅ Test book uploaded

**Start Testing:** Add a book to cart → Checkout → Pay with sandbox account!

## 📞 Need Help?

- **PayPal Developer Docs:** https://developer.paypal.com/docs/
- **PayPal Community:** https://www.paypal-community.com/
- **Sandbox Guide:** https://developer.paypal.com/tools/sandbox/

---

**Note:** Always use sandbox credentials for testing. Never use real PayPal accounts or real money during development!
