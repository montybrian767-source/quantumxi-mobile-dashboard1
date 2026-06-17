@echo off
title QuantumXI Investor Portal - Fixed Launcher
echo Starting QuantumXI Investor Portal...
echo.
echo Default login:
echo admin@quantumxi.local / admin123
echo.

if not exist "quantumxi_investor_portal.py" (
    echo ERROR: quantumxi_investor_portal.py not found.
    echo Put this launcher in the same folder as quantumxi_investor_portal.py
    pause
    exit /b
)

py -m pip install streamlit pandas
py -m streamlit run quantumxi_investor_portal.py

pause
