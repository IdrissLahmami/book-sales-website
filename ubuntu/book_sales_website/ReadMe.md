
# Book Sales Website - Quick Start Guide

## 🚀 Quick Start (Easy Way)

### Option 1: Double-click to start
Simply **double-click** one of these files:
- `start_server.bat` (for Command Prompt)
- `start_server.ps1` (for PowerShell) - may need to right-click → "Run with PowerShell"

**Note:** In PowerShell terminal, use `.\start_server.ps1` (with dot-slash prefix)

### Option 2: Manual start (Recommended)
```powershell
cd "c:\Users\irl20\Downloads\Book Sales Website Development in Python\home\ubuntu\book_sales_website"
$env:FLASK_APP='app.py'
$env:FLASK_ENV='development'
C:/Python313/python.exe -m flask run
```

## 📚 Access the Website
Once started, open your browser to:
- **Main Site:** http://127.0.0.1:5000
- **Login Page:** http://127.0.0.1:5000/login
- **Admin Dashboard:** http://127.0.0.1:5000/admin/dashboard (after login)

## 👤 Admin Login
1. Go to: http://127.0.0.1:5000/login
2. Enter credentials:
   - **Email:** admin@example.com
   - **Password:** admin123
3. After login, access Admin Dashboard from the navigation bar

## 📤 Upload PDF Books
1. Login as admin
2. Go to Admin Dashboard: http://127.0.0.1:5000/admin/dashboard
3. Click **"Add New Book"** button
4. Fill in book details
5. Upload cover image (optional - will auto-generate from PDF if not provided)
6. Upload PDF file (required)
7. Click **"Add Book"**

**Note:** If you don't upload a cover image, the system automatically generates a thumbnail from the PDF's first page!

## 💳 PayPal Testing Setup

**📖 Full Guide:** See [PAYPAL_SETUP.md](PAYPAL_SETUP.md) for detailed step-by-step instructions

### Quick Setup (5 minutes):
1. **Create Developer Account:** https://developer.paypal.com/
2. **Create REST API App:** Dashboard > My Apps & Credentials > Create App
3. **Copy Credentials:** Client ID and Secret (from Sandbox tab)
4. **Configure .env file:**
   ```env
   PAYPAL_MODE=sandbox
   PAYPAL_CLIENT_ID=your_client_id_here
   PAYPAL_CLIENT_SECRET=your_secret_here
   ```
5. **Restart server** and test with sandbox accounts

### Testing Payments:
- PayPal auto-creates sandbox test accounts (Business + Personal)
- Find credentials: Developer Dashboard > Sandbox > Accounts
- Use **Personal (Buyer)** account to test payments
- Login details shown in "View/Edit Account" > "Account Credentials"

**📝 See [PAYPAL_SETUP.md](PAYPAL_SETUP.md) for complete instructions with screenshots**

## 🔄 Keep Server Always Running

### For Development:
Keep the terminal window open - the server will run as long as the window is open.

### For Always-On (Production):

**Option 1: Windows Task Scheduler (Recommended for Windows)**
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: "At startup" or "At log on"
4. Action: Start `start_server.bat`
5. The server will start automatically when Windows starts

**Option 2: Cloud Deployment (Best for 24/7 availability)**
Deploy to free hosting:
- **PythonAnywhere** (easiest for Flask)
- **Render.com** (free tier available)
- **Railway.app** (simple deployment)
- **Heroku** (with hobby tier)

## 🛑 Stop the Server
Press `Ctrl+C` in the terminal window

## ⚠️ Why Does the Server Stop?

The Flask development server auto-reloads when it detects file changes. Sometimes this causes crashes:

**Common Causes:**
1. **File Changes**: Creating/editing Python files triggers auto-reload which can interrupt the server
2. **Interrupted Reload**: If files are being edited during reload, import errors occur
3. **Terminal Closed**: Closing the terminal window stops the server

**Solutions:**
- **Quick Restart**: Run `C:/Python313/python.exe app.py` in the terminal
- **Disable Auto-Reload**: Set `app.config['DEBUG'] = False` in app.py (not recommended for development)
- **Keep Terminal Open**: Don't close the terminal window where server is running
- **Use Production Mode**: For 24/7 uptime, deploy to a cloud platform (see below)

## 📖 GitHub Repository
https://github.com/IdrissLahmami/book-sales-website
