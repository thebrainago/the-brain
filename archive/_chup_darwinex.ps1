Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$out = "C:\Users\SV STORE\Downloads\Research SP500\lab\reports\screen.png"
$chrome = Get-Process chrome | Where-Object { $_.MainWindowTitle -like '*Darwinex*' } | Select-Object -First 1
if ($chrome) {
  $f = [System.Windows.Automation.AutomationElement]::FromHandle($chrome.MainWindowHandle)
  $wp = $f.GetCurrentPattern([System.Windows.Automation.WindowPattern]::Pattern)
  if ($wp) { $wp.SetWindowVisualState([System.Windows.Automation.WindowVisualState]::Maximized) }
}
Start-Sleep -Milliseconds 1200
$b = [System.Windows.Forms.SystemInformation]::VirtualScreen
$bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($b.Left, $b.Top, 0, 0, $bmp.Size)
$bmp.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
Write-Output "DA CHUP $out"
