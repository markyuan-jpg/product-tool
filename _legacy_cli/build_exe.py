#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Build script to package Product Catalog Generator as a single .exe file.

Usage:
    python build_exe.py

Requirements:
    pip install pyinstaller
    pip install pandas openpyxl pdfplumber PyMuPDF weasyprint python-docx argostranslate streamlit
"""
import os
import sys
import shutil


def check_dependencies():
    """Check if required packages are installed."""
    required = [
        "pyinstaller",
        "pandas",
        "openpyxl", 
        "pdfplumber",
        "PyMuPDF",
        "weasyprint",
        "python-docx",
        "streamlit",
        "pdf2image",
        "pytesseract",
    ]
    
    missing = []
    for pkg in required:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print("Missing packages. Install with:")
        print(f"  pip install {' '.join(missing)}")
        return False
    return True


def clean_build():
    """Clean previous build files."""
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            print(f"Cleaning {folder}/...")
            shutil.rmtree(folder)


def build_exe():
    """Build the .exe file."""
    import PyInstaller.__main__
    
    # Build arguments
    args = [
        "run.py",
        "--onefile",                    # Single executable
        "--console",                   # Show console window
        "--name=ProductCatalogGenerator",
        "--distpath=dist",
        "--workpath=build",
        "--specpath=build",
        
        # Include src folder
        "--add-data=src;src",
        
        # Hidden imports for optional packages
        "--hidden-import=pandas",
        "--hidden-import=openpyxl",
        "--hidden-import=pdfplumber",
        "--hidden-import=fitz",
        "--hidden-import=weasyprint",
        "--hidden-import=docx",
        "--hidden-import=streamlit",
        "--hidden-import=tqdm",
        "--hidden-import=argostranslate",
        "--hidden-import=argostranslate.package",
        "--hidden-import=argostranslate.translate",
        
        # Exclude unused modules to reduce size
        "--exclude-module=tkinter",
        "--exclude-module=matplotlib",
        "--exclude-module=numpy",
        "--exclude-module=IPython",
        "--exclude-module=jinja2",
        
        # Clean build
        "--clean",
    ]
    
    print("Building .exe with PyInstaller...")
    print("=" * 50)
    
    try:
        PyInstaller.__main__.run(args)
        print("=" * 50)
        print("Build complete!")
        
        # Find the exe
        exe_path = os.path.join("dist", "ProductCatalogGenerator.exe")
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"\nOutput: {exe_path}")
            print(f"Size: {size_mb:.1f} MB")
        else:
            print("\nWarning: .exe not found in dist/")
            
    except Exception as e:
        print(f"Build failed: {e}")
        return False
    
    return True


def main():
    """Main entry point."""
    print("=" * 50)
    print("Product Catalog Generator - Build Script")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("Error: Python 3.8+ required")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Clean previous build
    clean_build()
    
    # Build
    if build_exe():
        print("\n" + "=" * 50)
        print("SUCCESS!")
        print("=" * 50)
        print("\nTo run: ./dist/ProductCatalogGenerator.exe")
        print("\nNote: Translation model files must be in the same directory as the .exe")


if __name__ == "__main__":
    main()