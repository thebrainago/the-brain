$ErrorActionPreference = "SilentlyContinue"
$lab = "C:\Users\SV STORE\Downloads\Research SP500\lab"
$log = Join-Path $lab "reports\tiep_tuc.log"
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
$now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$msg = "tiep tuc"
Add-Type -TypeDefinition @"
using System; using System.Collections.Generic; using System.Runtime.InteropServices;
public static class TK {
  [StructLayout(LayoutKind.Explicit)] public struct INPUT_RECORD { [FieldOffset(0)] public ushort EventType; [FieldOffset(4)] public KEY_EVENT key; }
  [StructLayout(LayoutKind.Sequential)] public struct KEY_EVENT { public int bKeyDown; public ushort repeat; public ushort vk; public ushort scan; public char ch; public uint state; }
  [DllImport("kernel32.dll")] public static extern bool FreeConsole();
  [DllImport("kernel32.dll")] public static extern bool AttachConsole(uint pid);
  [DllImport("kernel32.dll")] public static extern IntPtr GetStdHandle(int n);
  [DllImport("kernel32.dll")] public static extern bool WriteConsoleInput(IntPtr h, INPUT_RECORD[] r, uint n, out uint w);
  static INPUT_RECORD ev(int down, ushort vk, char c) { var k=new KEY_EVENT(); k.bKeyDown=down; k.repeat=1; k.vk=vk; k.ch=c; var r=new INPUT_RECORD(); r.EventType=1; r.key=k; return r; }
  public static int Inject(uint pid, string text) {
    FreeConsole(); if (!AttachConsole(pid)) return 1;
    IntPtr h = GetStdHandle(-10);
    var list = new List<INPUT_RECORD>();
    foreach (char c in text.ToCharArray()) { ushort vk=(c>='a'&&c<='z')?(ushort)(c-32):(c==' ')?(ushort)0x20:(ushort)c; list.Add(ev(1,vk,c)); list.Add(ev(0,vk,c)); }
    // Ctrl+Enter (LEFT_CTRL_PRESSED=0x0008) - gui trong multiline TUI
    var dn=ev(1,13,'\r'); dn.key.state=0x0008; list.Add(dn);
    var up=ev(0,13,'\r'); up.key.state=0x0008; list.Add(up);
    INPUT_RECORD[] recs=list.ToArray(); uint w;
    bool ok=WriteConsoleInput(h, recs, (uint)recs.Length, out w);
    FreeConsole(); return ok?0:2;
  }
}
"@
$cx = Get-Process -Name codex -ErrorAction SilentlyContinue | Sort-Object StartTime -Descending | Select-Object -First 1
if (-not $cx) { Add-Content -LiteralPath $log -Value ($now+" SKIP: khong thay codex"); exit 0 }
$rc = [TK]::Inject([uint32]$cx.Id, $msg)
Add-Content -LiteralPath $log -Value ($now + (" SEND_CTRLENTER rc=" + $rc + " codex=" + $cx.Id))
