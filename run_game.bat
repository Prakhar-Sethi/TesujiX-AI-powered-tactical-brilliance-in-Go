@echo off
echo Starting Go Game AI...
echo.
python go_game_gui.py
if errorlevel 1 (
    echo.
    echo ERROR: Failed to run the game!
    echo Make sure you ran setup.bat first.
    echo.
    pause
)
