@echo off
echo ================================================
echo     Go Game AI - Automated Setup
echo ================================================
echo.

echo Step 1: Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed!
    echo Please install Python from python.org
    echo Then run this script again.
    pause
    exit /b 1
)
echo Python found!
echo.

echo Step 2: Installing Pygame...
pip install pygame
if errorlevel 1 (
    echo.
    echo Trying alternative installation method...
    python -m pip install pygame
)
echo.

echo Step 3: Verifying installation...
python -c "import pygame; print('Pygame version:', pygame.version.ver)"
if errorlevel 1 (
    echo ERROR: Pygame installation failed!
    pause
    exit /b 1
)
echo.

echo ================================================
echo     Setup Complete! 
echo ================================================
echo.
echo To run the game, type:
echo     python go_game_gui.py
echo.
echo Or double-click run_game.bat
echo.
pause
