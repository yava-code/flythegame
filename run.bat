@echo off
cd /d "%~dp0"
set FLY_DATA=%CD%\fly-data
if not exist ".venv\Scripts\python.exe" (
  echo create .venv with python 3.11 first
  exit /b 1
)
".venv\Scripts\python.exe" -m flygame %*
