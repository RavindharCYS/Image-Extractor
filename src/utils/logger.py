"""
Logger Module

This module provides logging configuration and utilities for the application.
It sets up logging to both file and console with appropriate formatting and
handles uncaught exceptions.
"""

import os
import sys
import logging
import logging.handlers
import traceback
import platform
import tempfile
from datetime import datetime
from typing import Optional, Dict, Any, List, Union, TextIO

# Default log levels
DEFAULT_CONSOLE_LEVEL = logging.INFO
DEFAULT_FILE_LEVEL = logging.DEBUG

# Default log format
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_CONSOLE_FORMAT = "%(levelname)s: %(message)s"

# Global logger instance
logger = logging.getLogger(__name__)


def setup_logging(
    log_dir: Optional[str] = None,
    console_level: int = DEFAULT_CONSOLE_LEVEL,
    file_level: int = DEFAULT_FILE_LEVEL,
    log_format: str = DEFAULT_LOG_FORMAT,
    console_format: str = DEFAULT_CONSOLE_FORMAT,
    max_file_size: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    capture_warnings: bool = True
) -> logging.Logger:
    """
    Set up logging configuration for the application.
    
    Args:
        log_dir: Directory to store log files (default: system temp directory)
        console_level: Logging level for console output
        file_level: Logging level for file output
        log_format: Format string for log messages
        console_format: Format string for console messages
        max_file_size: Maximum size of log file before rotation (bytes)
        backup_count: Number of backup log files to keep
        capture_warnings: Whether to capture warnings with the logging system
        
    Returns:
        Root logger instance
    """
    # Get the root logger
    root_logger = logging.getLogger()
    
    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set the root logger level to DEBUG to allow all messages
    root_logger.setLevel(logging.DEBUG)
    
    # Create formatters
    file_formatter = logging.Formatter(log_format)
    console_formatter = logging.Formatter(console_format)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Create file handler if log directory is specified or use temp directory
    if log_dir is None:
        log_dir = os.path.join(tempfile.gettempdir(), "image_metadata_extractor", "logs")
    
    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Create log file path
    log_file = os.path.join(log_dir, "image_metadata_extractor.log")
    
    try:
        # Create rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(file_level)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        logger.info(f"Log file created at: {log_file}")
    except (IOError, PermissionError) as e:
        logger.error(f"Failed to create log file at {log_file}: {e}")
        # Try to create log file in user's home directory as fallback
        try:
            home_log_dir = os.path.join(os.path.expanduser("~"), ".image_metadata_extractor", "logs")
            os.makedirs(home_log_dir, exist_ok=True)
            home_log_file = os.path.join(home_log_dir, "image_metadata_extractor.log")
            
            file_handler = logging.handlers.RotatingFileHandler(
                home_log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(file_level)
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
            
            logger.info(f"Log file created at fallback location: {home_log_file}")
        except Exception as e2:
            logger.error(f"Failed to create log file at fallback location: {e2}")
    
    # Capture warnings from the warnings module
    if capture_warnings:
        logging.captureWarnings(True)
        logger.info("Capturing Python warnings in logs")
    
    # Log system information
    _log_system_info(root_logger)
    
    return root_logger


def setup_exception_logging(exit_on_exception: bool = False) -> None:
    """
    Set up global exception handler to log uncaught exceptions.
    
    Args:
        exit_on_exception: Whether to exit the application on uncaught exception
    """
    def exception_handler(exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions by logging them."""
        if issubclass(exc_type, KeyboardInterrupt):
            # Call the default handler for KeyboardInterrupt
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # Log the exception
        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        
        # Exit if requested
        if exit_on_exception:
            sys.exit(1)
    
    # Set the exception hook
    sys.excepthook = exception_handler
    logger.info("Global exception handler installed")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def set_log_level(level: Union[int, str], logger_name: Optional[str] = None) -> None:
    """
    Set the logging level for a logger.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        logger_name: Logger name (None for root logger)
    """
    # Convert string level to integer if needed
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    
    # Get the logger
    target_logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()
    
    # Set the level
    target_logger.setLevel(level)
    logger.info(f"Set log level to {logging.getLevelName(level)} for {'root' if logger_name is None else logger_name}")


class StringIOTarget:
    """A file-like object that writes to a string buffer."""
    
    def __init__(self):
        """Initialize the string buffer."""
        self.buffer = []
    
    def write(self, msg):
        """Write a message to the buffer."""
        self.buffer.append(msg)
    
    def flush(self):
        """Flush the buffer (no-op)."""
        pass
    
    def getvalue(self):
        """Get the buffer contents as a string."""
        return "".join(self.buffer)


def create_memory_handler(capacity: int = 1000) -> logging.handlers.MemoryHandler:
    """
    Create a memory handler for buffering log messages in memory.
    
    Args:
        capacity: Maximum number of records to buffer
        
    Returns:
        MemoryHandler instance
    """
    # Create a string IO target
    string_io = StringIOTarget()
    
    # Create a stream handler that writes to the string IO
    target = logging.StreamHandler(string_io)
    target.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
    
    # Create memory handler
    memory_handler = logging.handlers.MemoryHandler(
        capacity=capacity,
        flushLevel=logging.ERROR,
        target=target
    )
    
    # Store the string IO in the handler for later retrieval
    memory_handler.string_io = string_io
    
    return memory_handler


def get_logs_from_memory_handler(handler: logging.handlers.MemoryHandler) -> str:
    """
    Get logs from a memory handler.
    
    Args:
        handler: MemoryHandler instance created with create_memory_handler
        
    Returns:
        String containing the logs
    """
    # Flush the handler to ensure all records are processed
    handler.flush()
    
    # Get the logs from the string IO
    if hasattr(handler, 'string_io'):
        return handler.string_io.getvalue()
    
    return ""


def add_memory_handler_to_logger(logger_name: Optional[str] = None, capacity: int = 1000) -> logging.handlers.MemoryHandler:
    """
    Add a memory handler to a logger for capturing logs in memory.
    
    Args:
        logger_name: Logger name (None for root logger)
        capacity: Maximum number of records to buffer
        
    Returns:
        MemoryHandler instance
    """
    # Create memory handler
    handler = create_memory_handler(capacity)
    
    # Get the logger
    target_logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()
    
    # Add the handler
    target_logger.addHandler(handler)
    
    return handler


def remove_memory_handler(handler: logging.handlers.MemoryHandler, logger_name: Optional[str] = None) -> None:
    """
    Remove a memory handler from a logger.
    
    Args:
        handler: MemoryHandler instance to remove
        logger_name: Logger name (None for root logger)
    """
    # Get the logger
    target_logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()
    
    # Remove the handler
    target_logger.removeHandler(handler)


def log_to_file(message: str, level: int = logging.INFO, logger_name: Optional[str] = None) -> None:
    """
    Log a message to file only (not to console).
    
    Args:
        message: Message to log
        level: Logging level
        logger_name: Logger name (None for root logger)
    """
    # Get the logger
    target_logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()
    
    # Create a list of console handlers to temporarily disable
    console_handlers = [h for h in target_logger.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)]
    
    # Temporarily disable console handlers
    for handler in console_handlers:
        handler.setLevel(logging.CRITICAL + 1)  # Set to a level higher than CRITICAL
    
    # Log the message
    target_logger.log(level, message)
    
    # Restore console handler levels
    for handler in console_handlers:
        handler.setLevel(DEFAULT_CONSOLE_LEVEL)


def log_to_console(message: str, level: int = logging.INFO, logger_name: Optional[str] = None) -> None:
    """
    Log a message to console only (not to file).
    
    Args:
        message: Message to log
        level: Logging level
        logger_name: Logger name (None for root logger)
    """
    # Get the logger
    target_logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()
    
    # Create a list of file handlers to temporarily disable
    file_handlers = [h for h in target_logger.handlers if isinstance(h, logging.FileHandler)]
    
    # Temporarily disable file handlers
    for handler in file_handlers:
        handler.setLevel(logging.CRITICAL + 1)  # Set to a level higher than CRITICAL
    
    # Log the message
    target_logger.log(level, message)
    
    # Restore file handler levels
    for handler in file_handlers:
        handler.setLevel(DEFAULT_FILE_LEVEL)


def get_log_file_path() -> Optional[str]:
    """
    Get the path to the current log file.
    
    Returns:
        Path to the log file or None if not found
    """
    # Get the root logger
    root_logger = logging.getLogger()
    
    # Find file handlers
    for handler in root_logger.handlers:
        if isinstance(handler, logging.FileHandler):
            return handler.baseFilename
    
    return None


def archive_logs(archive_dir: Optional[str] = None) -> Optional[str]:
    """
    Archive current logs to a timestamped file.
    
    Args:
        archive_dir: Directory to store archived logs (default: same as log directory)
        
    Returns:
        Path to the archive file or None if archiving failed
    """
    # Get the current log file path
    log_file = get_log_file_path()
    if not log_file or not os.path.exists(log_file):
        logger.error("No log file found to archive")
        return None
    
    try:
        # Create archive directory if not specified
        if archive_dir is None:
            archive_dir = os.path.join(os.path.dirname(log_file), "archives")
        
        # Create archive directory if it doesn't exist
        os.makedirs(archive_dir, exist_ok=True)
        
        # Create archive filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_file = os.path.join(archive_dir, f"log_archive_{timestamp}.log")
        
        # Copy log file to archive
        import shutil
        shutil.copy2(log_file, archive_file)
        
        logger.info(f"Logs archived to: {archive_file}")
        return archive_file
        
    except Exception as e:
        logger.error(f"Failed to archive logs: {e}")
        return None


def clear_logs() -> bool:
    """
    Clear the current log file.
    
    Returns:
        True if successful, False otherwise
    """
    # Get the current log file path
    log_file = get_log_file_path()
    if not log_file:
        logger.error("No log file found to clear")
        return False
    
    try:
        # Get the root logger
        root_logger = logging.getLogger()
        
        # Find and close file handlers
        file_handlers = [h for h in root_logger.handlers if isinstance(h, logging.FileHandler)]
        for handler in file_handlers:
            handler.close()
            root_logger.removeHandler(handler)
        
        # Truncate the file
        with open(log_file, 'w') as f:
            pass
        
        # Re-add the file handlers
        setup_logging()
        
        logger.info("Log file cleared")
        return True
        
    except Exception as e:
        logger.error(f"Failed to clear logs: {e}")
        return False


def _log_system_info(root_logger: logging.Logger) -> None:
    """
    Log system information for debugging purposes.
    
    Args:
        root_logger: Root logger instance
    """
    try:
        # Get system information
        system_info = {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'python_implementation': platform.python_implementation(),
            'system': platform.system(),
            'processor': platform.processor(),
            'architecture': platform.architecture()[0],
            'node': platform.node(),
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Log system information
        root_logger.info(f"System: {system_info['system']} {system_info['platform']}")
        root_logger.info(f"Python: {system_info['python_implementation']} {system_info['python_version']} {system_info['architecture']}")
        root_logger.info(f"Processor: {system_info['processor']}")
        root_logger.info(f"Node: {system_info['node']}")
        root_logger.info(f"Time: {system_info['time']}")
        
        # Log environment variables if in debug mode
        if root_logger.level <= logging.DEBUG:
            env_vars = {key: value for key, value in os.environ.items() 
                       if not key.lower().startswith(('pass', 'secret', 'token', 'key'))}
            root_logger.debug(f"Environment variables: {env_vars}")
        
    except Exception as e:
        root_logger.error(f"Failed to log system information: {e}")


def create_gui_log_handler(text_widget) -> logging.Handler:
    """
    Create a handler that logs to a tkinter Text widget.
    
    Args:
        text_widget: Tkinter Text widget to log to
        
    Returns:
        Logging handler
    """
    class TextWidgetHandler(logging.Handler):
        """Handler that writes log messages to a tkinter Text widget."""
        
        def __init__(self, text_widget):
            """Initialize with the Text widget."""
            logging.Handler.__init__(self)
            self.text_widget = text_widget
            
            # Configure tag colors for different log levels
            self.text_widget.tag_configure('DEBUG', foreground='gray')
            self.text_widget.tag_configure('INFO', foreground='black')
            self.text_widget.tag_configure('WARNING', foreground='orange')
            self.text_widget.tag_configure('ERROR', foreground='red')
            self.text_widget.tag_configure('CRITICAL', foreground='red', background='yellow')
        
        def emit(self, record):
            """Add the log message to the Text widget."""
            msg = self.format(record)
            
            # Insert in the main thread to avoid tkinter threading issues
            def _insert():
                self.text_widget.insert('end', msg + '\n', record.levelname)
                self.text_widget.see('end')  # Scroll to the end
                
            # Use after() to schedule in the main thread
            self.text_widget.after(0, _insert)
    
    # Create and configure the handler
    handler = TextWidgetHandler(text_widget)
    handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    handler.setLevel(logging.INFO)
    
    return handler


def log_method_calls(logger_name: Optional[str] = None, level: int = logging.DEBUG):
    """
    Decorator to log method calls with arguments and return values.
    
    Args:
        logger_name: Logger name to use (defaults to the module name)
        level: Logging level for the messages
        
    Returns:
        Decorator function
    """
    def decorator(func):
        # Get the logger
        log = logging.getLogger(logger_name or func.__module__)
        
        def wrapper(*args, **kwargs):
            # Format arguments for logging
            args_str = ', '.join([repr(a) for a in args])
            kwargs_str = ', '.join([f"{k}={repr(v)}" for k, v in kwargs.items()])
            all_args = ', '.join(filter(None, [args_str, kwargs_str]))
            
            # Log method call
            log.log(level, f"Calling {func.__name__}({all_args})")
            
            try:
                # Call the function
                result = func(*args, **kwargs)
                
                # Log the result
                log.log(level, f"{func.__name__} returned {repr(result)}")
                
                return result
            except Exception as e:
                # Log the exception
                log.exception(f"{func.__name__} raised {type(e).__name__}: {str(e)}")
                raise
        
        return wrapper
    
    return decorator


def log_execution_time(logger_name: Optional[str] = None, level: int = logging.DEBUG):
    """
    Decorator to log the execution time of a function.
    
    Args:
        logger_name: Logger name to use (defaults to the module name)
        level: Logging level for the messages
        
    Returns:
        Decorator function
    """
    def decorator(func):
        # Get the logger
        log = logging.getLogger(logger_name or func.__module__)
        
        def wrapper(*args, **kwargs):
            import time
            
            # Record start time
            start_time = time.time()
            
            try:
                # Call the function
                result = func(*args, **kwargs)
                
                # Calculate execution time
                execution_time = time.time() - start_time
                
                # Log execution time
                log.log(level, f"{func.__name__} executed in {execution_time:.4f} seconds")
                
                return result
            except Exception as e:
                # Calculate execution time even if there's an exception
                execution_time = time.time() - start_time
                
                # Log execution time and exception
                log.log(level, f"{func.__name__} failed after {execution_time:.4f} seconds: {str(e)}")
                raise
        
        return wrapper
    
    return decorator


def get_all_loggers() -> Dict[str, logging.Logger]:
    """
    Get all loggers in the logging system.
    
    Returns:
        Dictionary mapping logger names to logger instances
    """
    return logging.root.manager.loggerDict


def get_log_contents(max_lines: Optional[int] = None) -> str:
    """
    Get the contents of the current log file.
    
    Args:
        max_lines: Maximum number of lines to return (None for all)
        
    Returns:
        String containing the log contents
    """
    log_file = get_log_file_path()
    if not log_file or not os.path.exists(log_file):
        return "No log file found"
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            if max_lines is None:
                return f.read()
            else:
                # Read the last max_lines lines
                lines = f.readlines()
                return ''.join(lines[-max_lines:])
    except Exception as e:
        return f"Error reading log file: {str(e)}"


def configure_logger_for_testing() -> logging.Logger:
    """
    Configure a logger specifically for testing purposes.
    
    Returns:
        Configured logger
    """
    # Create a logger
    test_logger = logging.getLogger('test')
    test_logger.setLevel(logging.DEBUG)
    
    # Remove any existing handlers
    for handler in test_logger.handlers[:]:
        test_logger.removeHandler(handler)
    
    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    
    # Add the handler to the logger
    test_logger.addHandler(console_handler)
    
    return test_logger


# Initialize the module
def initialize():
    """Initialize the logger module."""
    # Set up basic logging if not already configured
    if not logging.getLogger().handlers:
        setup_logging()
    
    # Set up exception logging
    setup_exception_logging()
    
    logger.debug("Logger module initialized")


# Initialize when imported
initialize()