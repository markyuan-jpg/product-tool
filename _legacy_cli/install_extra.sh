#!/bin/bash
# Extra Dependencies Installer for product_tool
#
# Usage:
#     ./install_extra.sh
#
# Install this after activating the virtual environment:
#     source venv/bin/activate
#     ./install_extra.sh

echo "================================================"
echo "Installing Extra Dependencies"
echo "================================================"

echo ""
echo "[1/3] Installing pdfplumber..."
pip install pdfplumber

echo ""
echo "[2/3] Installing paddlepaddle..."
pip install paddlepaddle==2.6.1

echo ""
echo "[3/3] Installing paddleocr..."
pip install paddleocr==2.7.3

echo ""
echo "================================================"
echo "Installation Complete!"
echo "================================================"
echo ""
echo "Note: paddleocr may require extra dependencies."
echo "If installation fails, check your Python version compatibility."
echo ""