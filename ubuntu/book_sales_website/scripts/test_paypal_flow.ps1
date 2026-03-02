$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession

# Login as sample user
$login = Invoke-WebRequest -Uri 'http://127.0.0.1:5000/login' -Method Post -Body @{email='testuser@example.com'; password='password123'} -WebSession $session -UseBasicParsing

# Trigger create-payment
$null = Invoke-WebRequest -Uri 'http://127.0.0.1:5000/cart/add/5' -Method Post -WebSession $session -UseBasicParsing -ErrorAction SilentlyContinue
$resp = Invoke-WebRequest -Uri 'http://127.0.0.1:5000/create-payment' -Method Post -WebSession $session -ContentType 'application/json' -Body '{}' -UseBasicParsing -ErrorAction Stop

Write-Output 'CREATE-PAYMENT RESPONSE:'
Write-Output $resp.Content

Write-Output '--- PAYPAL LOG TAIL ---'
Get-Content -Path 'home/ubuntu/book_sales_website/debug_paypal.log' -Tail 200 -Encoding UTF8
