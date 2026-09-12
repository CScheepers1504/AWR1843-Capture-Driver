@echo off
REM Windows wrapper so a take is one command from PowerShell or cmd:
REM     .\session metal "metal object at 3.4 m" -frames 3000
REM
REM pushd first, then invoke by RELATIVE path: wsl.exe translates the current
REM drvfs directory into the WSL namespace for us. Passing "%~dp0session.sh"
REM directly would hand bash a C:\... path, which it cannot resolve.
pushd "%~dp0"
wsl.exe -e bash ./session.sh %*
set "RC=%ERRORLEVEL%"
popd
exit /b %RC%
