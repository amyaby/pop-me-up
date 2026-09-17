@echo off
setlocal
set "SRC=%~dp0app"
set "DST=%USERPROFILE%\popup-reminder\app"

if "%SRC:~0,2%"=="\\" goto :remote

:local
if exist "%SRC%\node_modules\electron\dist\electron.exe" goto :run_local
echo   ERROR: Electron not installed yet.
echo   From the repo folder, run:  cd app   then   npm install
goto :fail

:remote
robocopy "%SRC%" "%DST%" /E /XD node_modules /NFL /NDL /NJH /NJS /nc /ns /np >nul
if exist "%DST%\node_modules\electron\dist\electron.exe" goto :run_remote
echo   ERROR: Electron not installed yet.
echo   From the repo folder, run:  cd app   then   npm install
goto :fail

:run_local
start "" "%SRC%\node_modules\electron\dist\electron.exe" "%SRC%"
goto :end

:run_remote
start "" "%DST%\node_modules\electron\dist\electron.exe" "%DST%"
goto :end

:fail
echo.
pause

:end
endlocal