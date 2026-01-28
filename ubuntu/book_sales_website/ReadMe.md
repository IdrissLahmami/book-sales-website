
# Book Sales Website - Quick Start Guide

## 🚀 Quick Start (Easy Way)

### Option 1: Double-click to start
Simply **double-click** one of these files:
- `start_server.bat` (for Command Prompt)
- `start_server.ps1` (for PowerShell)

### Option 2: Manual start
```powershell
cd "c:\Users\irl20\Downloads\Book Sales Website Development in Python\home\ubuntu\book_sales_website"
$env:FLASK_APP='app.py'
$env:FLASK_ENV='development'
C:/Python313/python.exe -m flask run
```

## 📚 Access the Website
Once started, open your browser to:
- **Main Site:** http://127.0.0.1:5000
- **Admin Dashboard:** http://127.0.0.1:5000/admin/dashboard

## 👤 Admin Login
- **Email:** admin@example.com
- **Password:** admin123

## 📤 Upload PDF Books
1. Login as admin
2. Go to Admin Dashboard: http://127.0.0.1:5000/admin/dashboard
3. Click **"Add New Book"** button
4. Fill in book details
5. Upload cover image (optional)
6. Upload PDF file (required)
7. Click **"Add Book"**

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

## 📖 GitHub Repository
https://github.com/IdrissLahmami/book-sales-website
