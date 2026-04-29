import logging
from logging.handlers import RotatingFileHandler
from openspade.utils.utility import TEMP_DIR

# 全局变量，跟踪已配置的日志器
_configured_loggers = set()


def get_logger(name: str = "openspade") -> logging.Logger:
    """
    获取 OpenSpade 日志记录器

    Args:
        name: 日志记录器名称，默认为 "openspade"

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # 创建日志目录
    log_dir = TEMP_DIR / "log"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / "openspade.log"
    
    # 格式化器
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 文件处理器：按大小旋转，保留 5 个备份文件
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    _configured_loggers.add(name)
    
    return logger


def _reset_logger_config():
    """重置日志配置（用于测试）"""
    global _configured_loggers
    for name in _configured_loggers:
        logger_obj = logging.getLogger(name)
        for handler in logger_obj.handlers[:]:
            handler.close()
            logger_obj.removeHandler(handler)
    _configured_loggers.clear()


# 默认的主日志记录器
logger = get_logger()
