import unittest
import os
import sys
import logging
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from openspade.logger import logger, get_logger, _reset_logger_config
from openspade.utility import TEMP_DIR


class TestLogger(unittest.TestCase):
    """Test suite for openspade.logger module"""

    def setUp(self):
        """Set up test fixtures"""
        _reset_logger_config()
        self.log_dir = TEMP_DIR / "log"
        self.log_file = self.log_dir / "openspade.log"
        
        # 确保目录存在
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 清理现有的日志文件
        if self.log_file.exists():
            self.log_file.unlink()

    def tearDown(self):
        """Clean up after tests"""
        _reset_logger_config()

    def test_logger_initialization(self):
        """Test that logger is initialized correctly"""
        test_logger = get_logger("openspade")
        self.assertIsNotNone(test_logger)
        self.assertEqual(test_logger.name, "openspade")
        self.assertEqual(test_logger.level, logging.DEBUG)

    def test_log_dir_created(self):
        """Test that log directory is created when logger is used"""
        # 先删除目录
        if self.log_dir.exists():
            for f in self.log_dir.iterdir():
                f.unlink()
            self.log_dir.rmdir()
        
        test_logger = get_logger("test_logger")
        test_logger.info("Test message")
        self.assertTrue(self.log_dir.exists())
        self.assertTrue(self.log_dir.is_dir())

    def test_log_file_created(self):
        """Test that log file is created when messages are logged"""
        test_logger = get_logger("test_file_logger")
        test_message = "This is a test log message"
        test_logger.info(test_message)
        
        self.assertTrue(self.log_file.exists())
        
        # 检查日志文件内容
        with open(self.log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn(test_message, content)
            self.assertIn("INFO", content)

    def test_get_logger_custom_name(self):
        """Test get_logger with custom name"""
        custom_logger = get_logger("custom_logger")
        self.assertEqual(custom_logger.name, "custom_logger")
        
        # 测试自定义日志记录器
        test_msg = "Custom logger message"
        custom_logger.warning(test_msg)
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn(test_msg, content)
            self.assertIn("WARNING", content)

    def test_multiple_log_levels(self):
        """Test that different log levels are handled correctly"""
        test_logger = get_logger("multi_level_logger")
        test_logger.debug("Debug message")
        test_logger.info("Info message")
        test_logger.warning("Warning message")
        test_logger.error("Error message")
        test_logger.critical("Critical message")
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("Debug message", content)
            self.assertIn("Info message", content)
            self.assertIn("Warning message", content)
            self.assertIn("Error message", content)
            self.assertIn("Critical message", content)

    def test_same_logger_reused(self):
        """Test that calling get_logger with same name returns same instance"""
        logger1 = get_logger("reused_logger")
        logger2 = get_logger("reused_logger")
        self.assertIs(logger1, logger2)
        
        # 确认没有重复添加 handler
        self.assertEqual(len(logger1.handlers), 2)  # file + console

    def test_log_format_contains_timestamp(self):
        """Test that log entries contain timestamps"""
        test_logger = get_logger("timestamp_logger")
        test_msg = "Timestamp test message"
        test_logger.info(test_msg)
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # 检查是否包含类似 "2026-04-29" 的日期格式
            self.assertRegex(content, r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')


if __name__ == '__main__':
    unittest.main()
