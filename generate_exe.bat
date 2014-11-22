@echo off

rem For this to work we might need a file "__init__.py" in C:\Python27\Lib\site-packages\zope
rd /s /q montag-win

setup.py py2exe
if not %ERRORLEVEL%==0 goto error
xcopy /SEYI web2py dist\web2py
del /s dist\web2py\*.pyc 2>NUL
del /s /q dist\web2py\applications\montag\errors\*.* 2>NUL
del /s /q dist\web2py\applications\admin\errors\*.* 2>NUL
del /s dist\web2py\httpserver.* 2>NUL
del /s dist\web2py\parameters*.* 2>NUL
del /s dist\web2py\welcome.w2p 2>NUL

mkdir montag-win
copy scripts\start_montag.bat montag-win
copy scripts\montag.ico montag-win
move dist montag-win\

echo Build finished succesfully
goto end

:error
  echo There were errors
  
:end
