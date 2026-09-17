@echo off
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
del "%STARTUP%\ReminderBubble.vbs" 2>nul
echo   Auto-start removed. Bubble will no longer appear on boot.
pause
