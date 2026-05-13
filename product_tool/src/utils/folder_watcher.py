# -*- coding: utf-8 -*-
"""
文件夹监听器 - 文件变化自动处理
依赖: pip install watchdog
"""
import os
import time
import logging
from pathlib import Path
from typing import Callable, Optional

# Watchdog (可选)
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class FileHandler(FileSystemEventHandler):
    """文件事件处理器"""
    
    def __init__(self, callback: Callable[[str], None] = None, 
                 extensions: tuple = ('.xlsx', '.xls', '.docx'),
                 debounce: float = 1.0):
        """
        Args:
            callback: 文件变化时的回调函数 (filepath) -> None
            extensions: 监听的扩展名 (tuple)
            debounce: 去重等待时间(秒)
        """
        self.callback = callback
        self.extensions = extensions
        self.debounce = debounce
        self.last_handled = {}  # filepath -> last_handle_time
    
    def is_valid_file(self, path: str) -> bool:
        """检查是否为有效文件"""
        return any(path.lower().endswith(ext) for ext in self.extensions)
    
    def should_handle(self, path: str) -> bool:
        """检查是否应该处理 (去重)"""
        now = time.time()
        last = self.last_handled.get(path, 0)
        if now - last < self.debounce:
            return False
        self.last_handled[path] = now
        return True
    
    def on_created(self, event):
        """文件创建"""
        if event.is_directory:
            return
        if self.is_valid_file(event.src_path):
            logging.info(f'[Created] {event.src_path}')
            if self.should_handle(event.src_path) and self.callback:
                self.callback(event.src_path)
    
    def on_modified(self, event):
        """文件修改"""
        if event.is_directory:
            return
        if self.is_valid_file(event.src_path):
            logging.info(f'[Modified] {event.src_path}')
            if self.should_handle(event.src_path) and self.callback:
                self.callback(event.src_path)


class FolderWatcher:
    """文件夹监听器"""
    
    def __init__(self, watch_path: str, 
                 callback: Callable[[str], None] = None,
                 extensions: tuple = ('.xlsx', '.xls', '.docx'),
                 debounce: float = 1.0):
        """
        Args:
            watch_path: 监听路径
            callback: 处理回调 (filepath) -> None
            extensions: 监听扩展名
            debounce: 去重时间
        """
        self.watch_path = watch_path
        self.callback = callback
        self.extensions = extensions
        self.debounce = debounce
        
        self.observer = None
        self.handler = None
    
    def start(self):
        """启动监听"""
        if not WATCHDOG_AVAILABLE:
            raise ImportError("watchdog not installed: pip install watchdog")
        
        self.handler = FileHandler(
            callback=self.callback,
            extensions=self.extensions,
            debounce=self.debounce
        )
        self.observer = Observer()
        self.observer.schedule(self.handler, self.watch_path, recursive=False)
        self.observer.start()
        logging.info(f'Started watching: {self.watch_path}')
    
    def stop(self):
        """停止监听"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logging.info('Stopped watching')
    
    def run(self, duration: float = None):
        """
        运行监听
        
        Args:
            duration: 监听时长(秒), None为无限
        """
        self.start()
        try:
            if duration:
                time.sleep(duration)
            else:
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()


def watch_and_parse(watch_path: str, output_path: str, extensions: tuple = ('.xlsx',)):
    """
    监听并自动解析
    
    Args:
        watch_path: 监听文件夹
        output_path: 输出文件夹
        extensions: 文件类型
    """
    from src.core import parse_excel
    
    def handle_file(filepath: str):
        logging.info(f'Processing: {filepath}')
        try:
            df = parse_excel(filepath)
            if df:
                out_file = os.path.join(
                    output_path,
                    os.path.basename(filepath).replace('.xlsx', '.csv')
                )
                df.to_csv(out_file, index=False, encoding='utf-8-sig')
                logging.info(f'Saved: {out_file}')
        except Exception as e:
            logging.error(f'Error: {e}')
    
    os.makedirs(output_path, exist_ok=True)
    
    watcher = FolderWatcher(
        watch_path=watch_path,
        callback=handle_file,
        extensions=extensions
    )
    
    print(f'Watching: {watch_path}')
    print(f'Output: {output_path}')
    print('Press Ctrl+C to stop')
    
    watcher.run()


# ============ CLI ============

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        # watch <folder> [output]
        watch_path = sys.argv[1]
        output_path = sys.argv[2] if len(sys.argv) > 2 else 'output'
        watch_and_parse(watch_path, output_path)
    else:
        # 演示
        print("FolderWatcher - 文件夹监听器")
        print("Usage: python folder_watcher.py <watch_folder> [output_folder]")
        print("Required: pip install watchdog")