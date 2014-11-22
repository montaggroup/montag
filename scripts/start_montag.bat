@echo off
echo ^ _  _   _____ __ 
echo ^| ^|^| ^| ^| ____/_ ^|
echo ^| ^|^| ^|_^| ^|__  ^| ^|
echo ^|__   _^|___ \ ^| ^|
echo    ^| ^|  ___) ^|^| ^|
echo    ^|_^| ^|____/ ^|_^|
cd dist
montag-services start
echo .
echo Montag is now running - Press any key to shutdown
pause > NUL
montag-services stop