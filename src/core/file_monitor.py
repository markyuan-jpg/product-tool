#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
File monitor for automatic product catalog processing.

Uses watchdog to monitor a folder for new files and processes them automatically.
"""
import os
import sys
import time
import threading
from pathlib import Path

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("watchdog not installed. Run: pip install watchdog")
    sys.exit(1)


# Supported file extensions
SUPPORTED_EXTENSIONS = {".xlsx", ".xls", ".pdf", ".docx", ".csv"}


class ProductFileHandler(FileSystemEventHandler):
    """Handler for product files."""
    
    def __init__(self, process_callback, process_dir=None):
        """
        Args:
            process_callback: Function to call with new file path
            process_dir: Directory to move processed files (optional)
        """
        super().__init__()
        self.process_callback = process_callback
        self.process_dir = process_dir or "processed"
        self.processed = set()  # Track recently processed files
        
        # Ensure processed directory exists
        os.makedirs(self.process_dir, exist_ok=True)
    
    def on_created(self, event):
        """Handle file creation."""
        if event.is_directory:
            return
        
        # Check file extension
        file_path = event.src_path
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext not in SUPPORTED_EXTENSIONS:
            return
        
        # Wait for file to be fully written
        time.sleep(1)
        
        # Avoid duplicate processing
        if file_path in self.processed:
            return
        self.processed.add(file_path)
        
        print(f"New file detected: {os.path.basename(file_path)}")
        
        # Process the file
        try:
            self.process_callback(file_path)
            
            # Move to processed folder
            if os.path.exists(file_path):
                new_path = os.path.join(
                    self.process_dir,
                    f"{int(time.time())}_{os.path.basename(file_path)}"
                )
                os.rename(file_path, new_path)
                print(f"Moved to: {new_path}")
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")


class FileMonitor:
    """Monitor a folder for new product files."""
    
    def __init__(self, watch_dir, process_callback, process_dir=None):
        """
        Args:
            watch_dir: Directory to monitor
            process_callback: Function to call with new file path
            process_dir: Directory for processed files
        """
        self.watch_dir = watch_dir
        self.process_callback = process_callback
        self.process_dir = process_dir
        
        # Create observer
        self.observer = Observer()
        self.handler = ProductFileHandler(
            process_callback,
            process_dir
        )
    
    def start(self):
        """Start monitoring."""
        print(f"Monitoring: {self.watch_dir}")
        print("Press Ctrl+C to stop")
        
        self.observer.schedule(self.handler, self.watch_dir, recursive=False)
        self.observer.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop monitoring."""
        print("\nStopping monitor...")
        self.observer.stop()
        self.observer.join()
        print("Monitor stopped")


def process_file(file_path: str):
    """
    Process a single product file.
    
    Args:
        file_path: Path to the file
    
    Returns:
        Result DataFrame or None
    """
    import pandas as pd
    from src.core.parser import parse_excel, parse_pdf, parse_docx, parse_csv
    from src.core.translator import ProductTranslator
    
    ext = os.path.splitext(file_path)[1].lower()
    
    print(f"Processing: {file_path}")
    
    try:
        # Parse based on file type
        if ext in [".xlsx", ".xls"]:
            df = parse_excel(file_path)
        elif ext == ".pdf":
            df = parse_pdf(file_path)
        elif ext == ".docx":
            df = parse_docx(file_path)
        elif ext == ".csv":
            df = parse_csv(file_path)
        else:
            print(f"Unsupported format: {ext}")
            return None
        
        if df is None or df.empty:
            print("No data extracted")
            return None
        
        print(f"Extracted {len(df)} products")
        
        # Translate
        translator = ProductTranslator()
        if translator.available:
            df = translator.translate_dataframe(df)
            print("Translated to English")
        
        return df
        
    except Exception as e:
        print(f"Error: {e}")
        return None


def monitor_folder(watch_dir: str, process_dir: str = None):
    """
    Start monitoring a folder.
    
    Args:
        watch_dir: Directory to monitor
        process_dir: Directory for processed files
    """
    if not os.path.isdir(watch_dir):
        print(f"Error: Directory not found: {watch_dir}")
        sys.exit(1)
    
    monitor = FileMonitor(watch_dir, process_file, process_dir)
    monitor.start()


# Standalone usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor folder for new files")
    parser.add_argument("directory", nargs="?", default=".", help="Directory to monitor")
    parser.add_argument("--processed", "-p", default="processed", help="Processed files directory")
    
    args = parser.parse_args()
    
    monitor_folder(args.directory, args.processed)