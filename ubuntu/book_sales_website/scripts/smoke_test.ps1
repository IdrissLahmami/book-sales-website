Start-Sleep -Seconds 2
try {
    $wc = New-Object System.Net.WebClient
    $respHome = $wc.DownloadString('http://127.0.0.1:5000/')
    Write-Output 'HOME: OK'
    Write-Output $respHome.Substring(0,[math]::Min(400,$respHome.Length))
} catch {
    Write-Output 'HOME: no response'
}
try {
    $wc = New-Object System.Net.WebClient
    $respAdmin = $wc.DownloadString('http://127.0.0.1:5000/admin/users')
    Write-Output 'ADMIN: OK'
    Write-Output $respAdmin.Substring(0,[math]::Min(400,$respAdmin.Length))
} catch {
    Write-Output 'ADMIN: no response'
}
Write-Output '--- FLASK LOG ---'
Get-Content -Path 'home/ubuntu/book_sales_website/debug_flask.log' -Tail 80 -Encoding UTF8
