@Echo Off
chcp 65001>nul

Echo ************
Echo ПО "Клиент DMconnect"
Echo ************

Set http_proxy=
Set https_proxy=

setlocal enabledelayedexpansion
Set count=0
for /f "tokens=*" %%i in ('where python.exe ^| findstr "Python3"') do (
  Set /a count+=1
  Set pythop_file=%%i
  if !count! GEQ 1 goto :break_loop1
)
:break_loop1
endlocal /b && Set pythop_file=%pythop_file%

if not defined pythop_file goto :next_loop
if "%pythop_file%"=="" goto :next_loop
if not exist "%pythop_file%" goto :next_loop
goto :python_found

:next_loop
Set search_dir=%LOCALAPPDATA%\Programs\Python
if exist "%search_dir%\" (
  setlocal enabledelayedexpansion
  Set count=0
  for /r "%search_dir%" %%a in (*.exe) do (
    for /f "tokens=*" %%i in ('Echo %%~fa ^| findstr "python.exe"') do (
      Set /a count+=1
      Set pythop_file=%%i
      if !count! GEQ 1 goto :break_loop2
    )
  )
) else (
  goto :no_python
)
:break_loop2
endlocal /b && Set pythop_file=%pythop_file%

if not defined pythop_file goto :no_python
if "%pythop_file%"=="" goto :no_python
if not exist "%pythop_file%" goto :no_python

:python_found
for %%a in ("%pythop_file%") do (
  Set "py=%%~dpa"
)

if "%py:~-1%"=="\" (
  if not "%py%"=="%py:~0,2%\" (
    Set "py=%py:~0,-1%"
  )
)

rem Echo Python 3 располагается в директории:
rem Echo %py%

rem Путь до Python 3
Set PATH=%py%;%PATH%

cd /D "%~dp0"

python .\main.py
:q
exit

:no_python
echo Python 3 не найден.
goto :q
