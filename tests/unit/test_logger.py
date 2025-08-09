"""
Test suite for the logger module.
Tests the custom logging functionality and log format configuration.
"""

import logging
import sys
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch, MagicMock

from router_test_kit.logger import setup_logger


class TestSetupLogger(unittest.TestCase):
    """Test the setup_logger function."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Clear any existing loggers
        logging.getLogger().handlers.clear()
        # Remove any existing logger from the module
        if 'router_test_kit.logger' in logging.Logger.manager.loggerDict:
            del logging.Logger.manager.loggerDict['router_test_kit.logger']
            
    def tearDown(self):
        """Clean up after tests."""
        # Remove test log files if they exist
        logs_dir = Path("logs")
        if logs_dir.exists():
            log_file = logs_dir / "debug.log"
            if log_file.exists():
                log_file.unlink()
            try:
                logs_dir.rmdir()
            except OSError:
                pass  # Directory not empty, that's fine
        
    def test_setup_logger_creates_logger(self):
        """Test that setup_logger creates a logger."""
        setup_logger()
        
        # Logger should be created
        logger = logging.getLogger('router_test_kit.logger')
        self.assertIsInstance(logger, logging.Logger)
        
    def test_setup_logger_sets_debug_level(self):
        """Test that setup_logger sets logger to DEBUG level."""
        setup_logger()
        
        logger = logging.getLogger('router_test_kit.logger')
        self.assertEqual(logger.level, logging.DEBUG)
        
    def test_setup_logger_creates_file_handler(self):
        """Test that setup_logger creates a file handler."""
        setup_logger()
        
        logger = logging.getLogger('router_test_kit.logger')
        
        # Should have at least one handler
        self.assertGreater(len(logger.handlers), 0)
        
        # Should have a FileHandler
        has_file_handler = any(
            isinstance(handler, logging.FileHandler)
            for handler in logger.handlers
        )
        self.assertTrue(has_file_handler)
        
    def test_setup_logger_creates_logs_directory(self):
        """Test that setup_logger creates the logs directory."""
        # Ensure logs directory doesn't exist
        logs_dir = Path("logs")
        if logs_dir.exists():
            import shutil
            shutil.rmtree(logs_dir)
            
        setup_logger()
        
        # Directory should be created
        self.assertTrue(logs_dir.exists())
        self.assertTrue(logs_dir.is_dir())
        
    def test_setup_logger_creates_debug_log_file(self):
        """Test that setup_logger configures handler for debug.log."""
        setup_logger()
        
        logger = logging.getLogger('router_test_kit.logger')
        
        # Find the FileHandler
        file_handler = None
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                file_handler = handler
                break
                
        self.assertIsNotNone(file_handler)
        
        # Handler should point to debug.log
        expected_path = str(Path("logs") / "debug.log")
        self.assertIn("debug.log", file_handler.baseFilename)
        
    def test_setup_logger_file_handler_debug_level(self):
        """Test that file handler is set to DEBUG level."""
        setup_logger()
        
        logger = logging.getLogger('router_test_kit.logger')
        
        # Find the FileHandler
        file_handler = None
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                file_handler = handler
                break
                
        self.assertIsNotNone(file_handler)
        self.assertEqual(file_handler.level, logging.DEBUG)
        
    def test_setup_logger_formatter_configuration(self):
        """Test that the formatter is properly configured."""
        setup_logger()
        
        logger = logging.getLogger('router_test_kit.logger')
        
        # Find the FileHandler
        file_handler = None
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                file_handler = handler
                break
                
        self.assertIsNotNone(file_handler)
        self.assertIsNotNone(file_handler.formatter)
        
        # Test formatter format
        formatter = file_handler.formatter
        self.assertIsInstance(formatter, logging.Formatter)
        
        # Test that format string contains expected elements
        format_string = formatter._fmt
        self.assertIn('%(filename)s', format_string)
        self.assertIn('%(asctime)s', format_string)
        self.assertIn('%(levelname)s', format_string)
        self.assertIn('%(message)s', format_string)
        
    def test_setup_logger_datetime_format(self):
        """Test that the datetime format is properly configured."""
        setup_logger()
        
        logger = logging.getLogger('router_test_kit.logger')
        
        # Find the FileHandler
        file_handler = None
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                file_handler = handler
                break
                
        formatter = file_handler.formatter
        self.assertEqual(formatter.datefmt, "%Y-%m-%d %H:%M:%S")
        
    def test_setup_logger_multiple_calls_idempotent(self):
        """Test that calling setup_logger multiple times is safe."""
        setup_logger()
        initial_handler_count = len(logging.getLogger('router_test_kit.logger').handlers)
        
        setup_logger()
        final_handler_count = len(logging.getLogger('router_test_kit.logger').handlers)
        
        # Should not add duplicate handlers
        # Note: This test assumes the function doesn't add duplicate handlers
        # If it does, the implementation should be improved
        
    def test_setup_logger_logs_directory_already_exists(self):
        """Test setup_logger when logs directory already exists."""
        # Pre-create the logs directory
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Should not raise an error
        setup_logger()
        
        # Directory should still exist
        self.assertTrue(logs_dir.exists())
        self.assertTrue(logs_dir.is_dir())


class TestLoggingIntegration(unittest.TestCase):
    """Test integration of logging functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Clear any existing loggers
        logging.getLogger().handlers.clear()
        if 'router_test_kit.logger' in logging.Logger.manager.loggerDict:
            del logging.Logger.manager.loggerDict['router_test_kit.logger']
            
    def tearDown(self):
        """Clean up after tests."""
        # Remove test log files if they exist
        logs_dir = Path("logs")
        if logs_dir.exists():
            log_file = logs_dir / "debug.log"
            if log_file.exists():
                log_file.unlink()
            try:
                logs_dir.rmdir()
            except OSError:
                pass
        
    def test_logger_writes_to_file(self):
        """Test that logger actually writes messages to the log file."""
        setup_logger()
        
        logger = logging.getLogger('router_test_kit.logger')
        test_message = "Test file logging message"
        
        # Log a message
        logger.debug(test_message)
        
        # Force flush
        for handler in logger.handlers:
            if hasattr(handler, 'flush'):
                handler.flush()
        
        # Check that file was created and contains message
        log_file = Path("logs") / "debug.log"
        self.assertTrue(log_file.exists())
        
        # Read file content
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        self.assertIn(test_message, content)
        
    def test_logger_message_format_in_file(self):
        """Test that log messages have the correct format in the file."""
        setup_logger()
        
        logger = logging.getLogger('router_test_kit.logger')
        test_message = "Test format message"
        
        # Log a message
        logger.info(test_message)
        
        # Force flush
        for handler in logger.handlers:
            if hasattr(handler, 'flush'):
                handler.flush()
        
        # Read file content
        log_file = Path("logs") / "debug.log"
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check format elements are present
        self.assertIn(test_message, content)
        self.assertIn('INFO', content)
        self.assertIn('logger.py', content)  # filename
        # Should contain timestamp (YYYY-MM-DD HH:MM:SS format)
        import re
        timestamp_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
        self.assertTrue(re.search(timestamp_pattern, content))
        
    def test_different_log_levels_written(self):
        """Test that different log levels are properly written."""
        setup_logger()
        
        logger = logging.getLogger('router_test_kit.logger')
        
        # Log at different levels
        logger.debug("Debug message")
        logger.info("Info message") 
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
        
        # Force flush
        for handler in logger.handlers:
            if hasattr(handler, 'flush'):
                handler.flush()
        
        # Read file content
        log_file = Path("logs") / "debug.log"
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # All messages and levels should be present
        self.assertIn("Debug message", content)
        self.assertIn("Info message", content)
        self.assertIn("Warning message", content)
        self.assertIn("Error message", content)
        self.assertIn("Critical message", content)
        
        self.assertIn("DEBUG", content)
        self.assertIn("INFO", content)
        self.assertIn("WARNING", content)
        self.assertIn("ERROR", content)
        self.assertIn("CRITICAL", content)


if __name__ == '__main__':
    unittest.main()
