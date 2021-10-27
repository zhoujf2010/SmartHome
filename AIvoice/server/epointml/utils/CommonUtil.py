# -*- coding:utf-8 -*-
"""
Description: 常用工具类

@author: sy

@date: 2018/3/21
"""
from __future__ import print_function

import json
import mmap
import os
import shutil
import urllib
from urllib import parse
from urllib.parse import quote
from urllib.request import urlopen

import requests

from .PropertiesUtil import PropertiesUtil
from .logger import elog


class CommonUtil(object):

    def __init__(self):
        """
        初始化不用在意
        """
        self.paramcache = {}

    def init_logger(self):
        """
        该方法将在0.2.5被移除
        """
        e_log = elog()
        e_log.warn("init_logger function will be deprecated and will be removed in version 0.2.5")

    def setRootPath(self, path):
        """
        该方法将在0.2.5被移除

        Args:
            path(str): 根目录
        """
        e_log = elog()
        e_log.warn("init_logger function will be deprecated and will be removed in version 0.2.5")

    def getRootPath(self):
        """
        该方法将在0.2.5被移除
        """
        e_log = elog()
        e_log.warn("init_logger function will be deprecated and will be removed in version 0.2.5")

    def load_step_param(self, step_name):
        """
        读取阶段参数

        :param str step_name: 阶段名称
        :return: 参数字典
        :rtype: dict
        """
        if step_name in self.paramcache:
            return self.paramcache[step_name]
        params = {}
        # 读出packageinfo中默认值
        if os.path.exists("packageinfo.json"):
            with open('packageinfo.json', 'r', encoding='UTF-8') as file_object:
                txt = file_object.read()
            package_info = json.loads(txt)
            if step_name in package_info["steps"]:
                params_list = package_info["steps"][step_name]
                for item in params_list:
                    params[item["parameterName"]] = item["defaultValue"]
        # 读出config配置值
        filepath = "config/config.properties"
        params_list = PropertiesUtil().get_config_dict(file_path=filepath)
        if step_name in params_list:
            for item in params_list[step_name]:
                params[item] = params_list[step_name][item]

        # 计算关联配置
        for item in params:
            if params[item].startswith("{rel."):
                p_name, p_seg = params[item][5:][:-1].split('.')
                params[item] = self.load_step_param(p_name)[p_seg]

        self.paramcache[step_name] = params
        return params

    def installpackage(self, source):
        """
        安装系统需要的第三方包

        :param str source: 安装包仓库地址
        """
        e_log = elog()
        e_log.info("安装模块,仓库地址是：" + source)
        if "https" not in source:
            # 如果有端口号，去掉后面端口
            trust = str(parse.urlparse(source).netloc).split(":")[0]
            cmd = "pip install -r config/requirements.txt -i {0} --trusted-host {1} --timeout 180 --user".format(
                str(source), trust)
        else:
            cmd = "pip install -r config/requirements.txt -i {0} --timeout 180  --user".format(str(source))
        e_log.info("执行安装命令： " + cmd)
        os.system(cmd)
        e_log.info("安装模块完毕")

    def download_file(self, url, path):
        """
        下载文件

        :param str url: 文件地址
        :param str path: 文件路径
        """
        # 准备字典文件
        if os.path.exists(path):
            os.remove(path)
        # stream方式下载，不占用内存
        response = requests.get(url, stream=True, timeout=100000)
        with open(path, "wb") as code:
            shutil.copyfileobj(response.raw, code)

    def uploadModelResult(self, url, filepath):
        """
        上传模型结果

        :param str url: 服务器地址
        :param str filepath: 文件路径
        :return: 上传结果
        :rtype: str
        """
        # TODO 分片上传
        #         file = {'file': open(filepath, 'rb')}
        post_url = url  # + "?modelguid=" + modelguid + "&modelname=" + modelname + "&version=" + version
        depart = post_url.split('?')
        post_url = depart[0] + "?" + quote(depart[1]).replace("%3D", "=")
        #         r = requests.post(posturl, files=file)
        f = open(filepath, 'rb')
        mmapped_file_as_string = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

        # Do the request
        request = urllib.request.Request(post_url, mmapped_file_as_string)
        request.add_header("Content-Type", "application/zip")
        r = urllib.request.urlopen(request)

        # close everything
        mmapped_file_as_string.close()
        f.close()
        return r

    def downloadModelResult(self, url, filepath):
        """
        下载模型结果

        :param str url: 服务器地址
        :param str filepath: 文件路径
        :return: 上传结果
        :rtype: str
        """
        depart = url.split('?')
        down_url = depart[0] + "?" + quote(depart[1]).replace("%3D", "=").replace("%26", "&")
        self.download_file(down_url, filepath)

    def compress_file(self, src, output):
        """
        将文件压缩成zip包

        Parameters
        ----------
        src: str
            源文件路径
        output: str
            目标文件路径
        """
        shutil.make_archive(output, "zip", src)

    def extract_file(self, src, output):
        """
        将zip包解压

        Parameters
        ----------
        src: str
            解压源文件路径
        output: str
            解压目标位置
        """
        shutil.unpack_archive(src, output, format="zip")

    def init_dict(self, dicturl, dictpath):
        """
        初始化字典

        :param str dicturl: 字典下载地址
        :param str dictpath: 字典文件名
        """
        if os.path.exists(dictpath):
            return
        url = parse.quote(dicturl).replace("%3A", ":").replace("%3F", "?").replace("%3D", "=")
        print(url)
        f = urlopen(url)
        with open(dictpath, "wb") as code:
            code.write(f.read())

    def getDispSize(self, fsize):
        """
        计算出要显示的文件大小

        Args:
            fsize(float): 文件大小

        Returns:
            str: fsize-对应大小显示值
        """
        if fsize / 1024 < 1:
            return str(fsize) + "B"
        fsize = fsize / 1024
        if fsize / 1024 < 1:
            return str(round(fsize, 2)) + "KB"
        fsize = fsize / 1024
        if fsize / 1024 < 1:
            return str(round(fsize, 2)) + "MB"
        fsize = fsize / 1024
        if fsize / 1024 < 1:
            return str(round(fsize, 2)) + "GB"
        fsize = fsize / 1024
        if fsize / 1024 < 1:
            return str(round(fsize, 2)) + "TB"
        return fsize

    def getSpeed(self, fsize, tm):
        """
        计算速度，大小/时间，单位秒

        Args:
            fsize(float): 文件大小
            tm(float): 时间，单位秒

        Returns:
            str: speed-对应速度显示值
        """
        speed = fsize / tm
        return self.getDispSize(speed) + "/s"

    def sendRestReadySignal(self):
        """
        向AI平台通知已经准备好接口发布
        """
        print('\r---->reststarting', flush=True)

    def loadDataFromHDFS(self, hdfsurl, src, locpath):
        """
        从Hadoop HDFS中读数据作为语料, 只支持目录和文本文件

        Parameters
        ----------
        hdfsurl: str
            hdfs ip+端口 http://ip:port
        src: str
            hdfs上的文件目录
        locpath: str
            目标文件，hdfs文件中的数据写入这个文件
        """
        from hdfs.client import Client
        client = Client(str(hdfsurl))
        src = str(src)
        status = client.status(src)
        if status["type"] == "DIRECTORY":  # 如果是src是目录，读取目录中的文件
            with open(locpath, "w", encoding="utf-8") as f:
                for root, _, files in client.walk(hdfs_path=src):
                    for file in files:
                        fn = os.path.join(root, file)
                        if client.status(fn)["type"] == "FILE":
                            with client.read(fn, chunk_size=8096, encoding='utf-8') as reader:
                                for chunk in reader:
                                    f.write(chunk)
        elif status["type"] == "FILE":  # 如果src是文件， 读取该文件
            with open(locpath, "w", encoding="utf-8") as f:
                with client.read(src, chunk_size=8096, encoding='utf-8') as reader:
                    for chunk in reader:
                        f.write(chunk)

    def downloadModel(self, logger, url, zippath, tarpath=None):
        """
        下载模型并解压到指定路径，比commonUtil.downloadModelResult增加日志记录，和模型解压的功能.

        :param logger logger: logger实例
        :param str url: AI平台模型下载地址
        :param str zippath: 下载模型保存位置
        :param str/None tarpath: 下载模型解压位置，默认为None不做解压操作
        """
        import os
        import time
        logger.info("准备下载模型,url:" + url)
        t1 = time.time()
        self.downloadModelResult(url, zippath)
        fsize = os.path.getsize(zippath)
        usetime = time.time() - t1
        logger.info("下载模型完成,模型大小：%s，用时:%ds，速度:%s" % (
            commonUtil.getDispSize(fsize), usetime, commonUtil.getSpeed(fsize, usetime)))
        if tarpath is not None:
            commonUtil.extract_file(zippath, tarpath)

    def uploadModel(self, logger, modelname, modelpath, savemodelurl):
        """
        压缩模型，上传到AI平台, 比commonUtil.upoadModelResult增加压缩和日志记录功能。

        :param logger logger: logger实例
        :param str modelname: 模型名称
        :param str modelpath: 模型所在路径，打包整个模型目录
        :param str savemodelurl: AI平台模型上传接口地址
        """
        if savemodelurl:
            import os
            import time
            logger.info("准备压缩" + modelname)
            self.compress_file(modelpath, modelpath)
            if modelpath.endswith("/"):
                zipname = modelpath[:-1] + ".zip"
            else:
                zipname = modelpath + ".zip"
            logger.info("开始上传" + modelname + ",地址：" + savemodelurl + "?resultname=" + modelname)
            fsize = os.path.getsize(zipname)
            t2 = time.time()
            commonUtil.uploadModelResult(savemodelurl + "?resultname=" + modelname, zipname)
            os.remove(zipname)
            usetime = time.time() - t2
            logger.info("上传" + modelname + "完成,模型大小：%s，用时:%ds，速度:%s" % (commonUtil.getDispSize(fsize), usetime,
                                                                        commonUtil.getSpeed(fsize, usetime)))
        else:
            logger.info("取消上传" + modelname)

    @staticmethod
    def result_deal(sorted_dec, number=5):
        """
        拼接输出结果

        :param sorted_dec: 预测结果集
        :param number: 返回预测结果个数，默认为5
        :return: 结果集
        :rtype: dict
        """
        base = 0.
        number = min(number, len(sorted_dec))
        for i in range(number):
            if sorted_dec[i][1] > 0:
                base += sorted_dec[i][1]
        rst = []
        div = base if base != 0. else 1.
        for i in range(number):
            if sorted_dec[i][1] > 0:
                rst.append({"Classify": sorted_dec[i][0], "Probability": sorted_dec[i][1] / div})
        return rst


commonUtil = CommonUtil()
