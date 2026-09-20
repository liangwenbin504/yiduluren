Dim shell
Set shell = CreateObject("WScript.Shell")
shell.CurrentDirectory = "E:\仪度六~1\YIDULU~1"
shell.Run "E:\仪度六~1\YIDULU~1\VENV~1\Scripts\python.exe train_r14_simple.py", 0, False
