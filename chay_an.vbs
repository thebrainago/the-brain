' Chay CHAY_NEN.cmd o che do AN (khong hien cua so console).
' Dung cho muc Startup de THE BRAIN tu len sau moi lan dang nhap.
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
duong = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = duong
sh.Run """" & duong & "\CHAY_NEN.cmd""", 0, False
