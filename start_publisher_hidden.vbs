Set shell = CreateObject("WScript.Shell")
shell.Run "cmd /c cd /d C:\LiquidityLabs\BTC_RESEARCH_DASHBOARD && py -3.12 publisher.py", 0, False
