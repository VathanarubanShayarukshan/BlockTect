@echo off
setlocal

if "%~1"=="" (
  echo Drag a Scratch .sb3 file onto this batch file, or enter its path below.
  set /p "PROJECT=Project path: "
) else (
  set "PROJECT=%~1"
)

if not exist "%PROJECT%" (
  echo Project file not found: "%PROJECT%"
  pause
  exit /b 1
)

if "%~2"=="" (
  node "%~dp0compile-fullstack.js" "%PROJECT%"
) else (
  node "%~dp0compile-fullstack.js" "%PROJECT%" "%~2"
)
if errorlevel 1 (
  pause
  exit /b 1
)

endlocal