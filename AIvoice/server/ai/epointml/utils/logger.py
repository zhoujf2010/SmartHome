# -*- coding: utf-8 -*-
"""
Description: 日志类

@author: WangLeAi

@date: 2021/3/3
"""
import datetime
import json
import logging.config
import os

from .Singleton import Singleton


@Singleton
class elog(object):
    __current_log = None

    def __init__(self):
        """
        初始化
        """
        if self.__current_log is None:
            self.__current_log = self.__init_elog()

    @staticmethod
    def __init_elog():
        """
        __init_elog()
        初始化日志，日志统一写在根目录下的logs目录下面
        """
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)  # 创建路径

        log_file = datetime.datetime.now().strftime("%Y-%m-%d") + ".log"

        log_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "simple": {
                    'format': '%(asctime)s [%(name)s:%(lineno)d] [%(levelname)s]- %(message)s'
                },
                'standard': {
                    'format': '%(asctime)s [%(threadName)s:%(thread)d] [%(name)s:%(lineno)d] [%(levelname)s]- %(message)s'
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "standard",
                    "stream": "ext://sys.stdout"
                },

                "default": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "INFO",
                    "formatter": "standard",
                    "filename": os.path.join(log_dir, log_file),
                    'mode': 'w+',
                    "maxBytes": 1024 * 1024 * 5,  # 5 MB
                    "backupCount": 200,
                    "encoding": "utf8"
                },
            },
            "root": {
                'handlers': ['console', 'default'],
                'level': "DEBUG",
                'propagate': False
            }
        }

        # 如果有配置文件，则加载配置文件
        if os.path.exists('config/log.json'):
            with open('config/log.json', 'r', encoding='UTF-8') as file_object:
                txt = file_object.read()
            log_config = json.loads(txt)
            file_name = log_config["handlers"]["rolfile"]["filename"]
            file_name = datetime.datetime.now().strftime(file_name)
            log_config["handlers"]["rolfile"]["filename"] = file_name
        logging.config.dictConfig(log_config)
        # 设置flask日志级别为ERROR
        werk_log = logging.getLogger('werkzeug')
        werk_log.setLevel(logging.ERROR)
        return logging.getLogger(__name__)

    def debug(self, msg, *args, **kwargs):
        self.__current_log.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.__current_log.info(msg, *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        self.__current_log.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.__current_log.error(msg, *args, **kwargs)

