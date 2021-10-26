# -*- coding: utf-8 -*-
"""
Description: 注解实现单例

@author: WangLeAi

@date: 2021/3/3
"""


def Singleton(cls):
    _instance = {}

    def _singleton(*args, **kargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kargs)
        return _instance[cls]

    _singleton.__doc__ = cls.__doc__
    return _singleton
