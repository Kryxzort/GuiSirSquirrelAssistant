import os
import time
import queue
import logging
import threading
import multiprocessing
from typing import Optional, Dict, Any

# Global variables for async logging
_log_queue: Optional[queue.Queue] = None
_log_process: Optional[multiprocessing.Process] = None
_logging_enabled: bool = True
_async_enabled: bool = True

def set_logging_enabled(enabled: bool):
    """Enable or disable all logging (Do Not Log toggle)"""
    global _logging_enabled
    _logging_enabled = enabled

def is_logging_enabled() -> bool:
    """Check if logging is enabled"""
    return _logging_enabled

def set_async_enabled(enabled: bool):
    """Enable or disable async logging (fallback to synchronous)"""
    global _async_enabled
    _async_enabled = enabled

class NoMillisecondsFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        """Format time without milliseconds"""
        return time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(record.created))
    
    def format(self, record):
        """Format log record with dirty flag"""
        formatted = super().format(record)
        if hasattr(record, 'dirty') and record.dirty:
            formatted += " | DIRTY"
        return formatted

def _log_worker_process(log_queue: multiprocessing.Queue, log_filename: str):
    """Worker process that handles async log writing to file"""
    # Setup logging in the worker process
    handler = logging.FileHandler(log_filename)
    formatter = NoMillisecondsFormatter(
        fmt='%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%d/%m/%Y %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    worker_logger = logging.getLogger('async_log_worker')
    worker_logger.addHandler(handler)
    worker_logger.setLevel(logging.DEBUG)
    
    try:
        while True:
            try:
                # Get log record from queue (blocking)
                record_data = log_queue.get(timeout=1.0)
                
                # Check for shutdown signal
                if record_data is None:
                    break
                
                # Reconstruct LogRecord and write to file
                level, name, msg, funcName, lineno, dirty = record_data
                
                # Create a LogRecord manually
                record = logging.LogRecord(
                    name=name,
                    level=level,
                    pathname='',
                    lineno=lineno,
                    msg=msg,
                    args=(),
                    exc_info=None,
                    func=funcName
                )
                record.dirty = dirty
                
                # Log it using the worker logger
                worker_logger.handle(record)
                
            except queue.Empty:
                continue  # No messages, keep waiting
            except Exception as e:
                # Log worker errors to stderr (not the main log)
                print(f"Async logger worker error: {e}", flush=True)
                
    except KeyboardInterrupt:
        pass
    finally:
        # Cleanup
        handler.close()

def start_async_logging(log_filename: str):
    """Start async logging worker process"""
    global _log_queue, _log_process
    
    if _log_process is not None:
        return  # Already started
    
    # Create multiprocessing queue
    _log_queue = multiprocessing.Queue(maxsize=1000)
    
    # Start worker process
    _log_process = multiprocessing.Process(
        target=_log_worker_process,
        args=(_log_queue, log_filename),
        daemon=True
    )
    _log_process.start()

def stop_async_logging():
    """Stop async logging and cleanup worker process"""
    global _log_queue, _log_process
    
    if _log_process is not None:
        # Send shutdown signal
        _log_queue.put(None)
        _log_process.join(timeout=5.0)
        if _log_process.is_alive():
            _log_process.terminate()
        _log_process = None
    
    _log_queue = None

def async_log(level: int, name: str, msg: str, funcName: str, lineno: int, dirty: bool = False):
    """Queue log message for async processing. Returns True if queued, False if should use sync logging."""
    global _log_queue, _logging_enabled, _async_enabled
    
    # Fast exit if logging disabled
    if not _logging_enabled:
        return
    
    # If async disabled, fall back to synchronous logging
    if not _async_enabled or _log_queue is None:
        return False  # Signal caller to use sync logging
    
    try:
        # Non-blocking put (drop messages if queue full)
        _log_queue.put_nowait((level, name, msg, funcName, lineno, dirty))
        return True  # Successfully queued
    except queue.Full:
        # Queue full, drop this message or fall back to sync
        return False

class AsyncDirtyLogger(logging.Logger):
    
    def _log_async_or_sync(self, level, msg, args, dirty=False):
        """Try async logging first, fallback to sync if queue full or disabled"""
        # Fast exit if logging disabled
        if not _logging_enabled:
            return
        
        # Get caller info for logging
        import inspect
        frame = inspect.currentframe().f_back.f_back  # Go up 2 frames
        funcName = frame.f_code.co_name
        lineno = frame.f_lineno
        
        # Format message
        if args:
            msg = msg % args
        
        # Try async logging first
        if async_log(level, self.name, msg, funcName, lineno, dirty):
            return  # Successfully queued
        
        # Fall back to synchronous logging
        if self.isEnabledFor(level):
            record = self.makeRecord(self.name, level, '', lineno, msg, (), None, funcName)
            record.dirty = dirty
            self.handle(record)
    
    def debug(self, msg, *args, dirty=False, **kwargs):
        """Log debug message"""
        self._log_async_or_sync(logging.DEBUG, msg, args, dirty)
    
    def info(self, msg, *args, dirty=False, **kwargs):
        """Log info message"""
        self._log_async_or_sync(logging.INFO, msg, args, dirty)
    
    def warning(self, msg, *args, dirty=False, **kwargs):
        """Log warning message"""
        self._log_async_or_sync(logging.WARNING, msg, args, dirty)
    
    def error(self, msg, *args, dirty=False, **kwargs):
        """Log error message"""
        self._log_async_or_sync(logging.ERROR, msg, args, dirty)
    
    def critical(self, msg, *args, dirty=False, **kwargs):
        """Log critical message"""
        self._log_async_or_sync(logging.CRITICAL, msg, args, dirty)
    
    def exception(self, msg, *args, dirty=False, **kwargs):
        """Log exception message with full traceback"""
        # For exceptions, we MUST use synchronous logging to preserve traceback
        if self.isEnabledFor(logging.ERROR):
            import inspect
            frame = inspect.currentframe().f_back
            funcName = frame.f_code.co_name
            lineno = frame.f_lineno
            
            # Format message
            if args:
                msg = msg % args
            
            # Use synchronous logging with exc_info=True to capture traceback
            import sys
            record = self.makeRecord(self.name, logging.ERROR, '', lineno, msg, (), sys.exc_info(), funcName)
            record.dirty = dirty
            self.handle(record)