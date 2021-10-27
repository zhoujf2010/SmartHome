# -*- coding:utf-8 -*-
"""
Description: DB工具类

@author: WangLeAi

@date: 2018/9/18
"""
import importlib

from DBUtils.PooledDB import PooledDB

from .PropertiesUtil import prop
from .logger import elog


class DbPoolUtil(object):

    def __init__(self, config_file='config/jdbc.properties', jdbcurl='', url='', username='', password=''):
        """
        数据库连接初始化
        config_file, jdbcurl, (url, username, password) 三者只需一个即可.

        Args:
            config_file(str): 数据库连接配置文件地址，默认为"config/jdbc.properties"，推荐使用
            jdbcurl(str): 数据库连接jdbcurl, 默认用'★'分割, 默认为''
            url(str): 数据库连接url, 默认为''
            username(str): 数据库连接登陆名, 默认为''
            password(str): 数据库连接密码, 默认为''
        """
        self.e_log = elog()
        if jdbcurl != '':
            url, username, password = jdbcurl.split('★')
        if url == '':
            properties_dic = prop.get_config_dict(config_file)
            url = properties_dic["url"]
            username = properties_dic['username']
            password = properties_dic['password']
        if not url.startswith("jdbc"):
            raise Exception("配置的url存在问题，请确认！")
        if username == '_EMPTY_':
            username = ''
        if password == '_EMPTY_':
            password = ''
        parts = url.split(":", 2)
        self.__db_type = parts[1]
        if self.__db_type == "mysql":
            contents = parts[2].split("?", 1)[0].split("/")
            if ":" in contents[2]:
                ip, port = contents[2].split(":")
            else:
                ip = contents[2]
                port = 3306
            database = contents[3]
            config = {
                'host': ip,
                'port': int(port),
                'database': database,
                'user': username,
                'password': password,
                'charset': "utf8"
            }
            db_creator = importlib.import_module("pymysql")
            self.__pool = PooledDB(db_creator, maxcached=50, maxconnections=1000, maxusage=None, **config)
        elif self.__db_type == "oracle":
            contents = parts[2].split(":", 1)
            if contents[1].startswith("@//"):
                params = contents[1].lstrip("@//").split("/")
                if ":" in params[0]:
                    ip, port = params[0].split(":")
                else:
                    ip = params[0]
                    port = "1521"
                database = params[1]
            else:
                params = contents[1].lstrip("@").split(":")
                if len(params) == 2:
                    ip = params[0]
                    port = "1521"
                    database = params[1]
                else:
                    ip = params[0]
                    port = params[1]
                    database = params[2]
            config = {
                'user': username,
                'password': password,
                'dsn': "/".join([":".join([ip, port]), database]),
                'nencoding': "utf8"
            }
            db_creator = importlib.import_module("cx_Oracle")
            self.__pool = PooledDB(db_creator, maxcached=50, maxconnections=1000, maxusage=None, **config)
        elif self.__db_type == "sqlserver":
            contents = parts[2].split(";", 1)
            ip_port = contents[0].lstrip("//").split("\\")[0]
            if ":" in ip_port:
                ip, port = ip_port.split(":")
            else:
                ip = ip_port
                port = 1433
            database = contents[1].split(";")[0].split("=")[1]
            config = {
                'host': ip,
                'port': int(port),
                'database': database,
                'user': username,
                'password': password,
                'charset': "utf8"
            }
            db_creator = importlib.import_module("pymssql")
            self.__pool = PooledDB(db_creator, maxcached=50, maxconnections=1000, maxusage=None, **config)
        elif self.__db_type == "sqlite":
            config = {
                'database': parts[2]
            }
            db_creator = importlib.import_module("sqlite3")
            self.__pool = PooledDB(db_creator, maxcached=50, maxconnections=1000, maxusage=None, **config)
        elif self.__db_type == "phoenix":
            params = parts[2].split(":")
            if len(params) == 2:
                ip = params[0].split(",")[0]
                port = "8765"
            else:
                ip = params[0].split(",")[0]
                port = params[1]
                if params[2] == '/hbase-unsecure':
                    port = "8765"  # 强制写过来
            # 'autocommit': True配置一定要，否则插入删除语句执行无效

            config = {
                'url': 'http://{0}:{1}/'.format(ip, port),
                'user': username,
                'password': password,
                'autocommit': True
            }
            db_creator = importlib.import_module("phoenixdb")
            self.__pool = PooledDB(db_creator, maxcached=50, maxconnections=1000, maxusage=None, **config)
        elif self.__db_type == "postgresql":  # mpp库
            params = parts[2].lstrip('/').split("/")
            hosts = params[0].split(':')
            # 数据库连接参数
            config = {
                'database': params[1],
                'user': username,
                'password': password,
                'host': hosts[0],
                'port': hosts[1],
                'client_encoding': 'UTF8'
            }
            db_creator = importlib.import_module("psycopg2")
            self.__pool = PooledDB(db_creator, maxcached=50, maxconnections=1000, maxusage=None, **config)
        elif self.__db_type == "hive2":  # hive库, 开源版本
            params = parts[2].lstrip("/").split("/")
            hosts = params[0].split(":")
            config = {
                "database": params[1],
                "host": hosts[0],
                "port": hosts[1]
            }
            db_creator = importlib.import_module("pyhive.hive")
            self.__pool = PooledDB(db_creator, maxcached=50, maxconnections=1000, maxusage=None, **config)
        elif self.__db_type == "presto":  # 开源版presto
            params = parts[2].lstrip("/").split("/")
            hosts = params[0].split(":")
            config = {
                "host": hosts[0],
                "port": hosts[1],
                "catalog": params[1],
                "schema": params[2]
            }
            db_creator = importlib.import_module("pyhive.presto")
            self.__pool = PooledDB(db_creator, maxcached=50, maxconnections=1000, maxusage=None, **config)
        else:
            raise Exception("unsupported database type " + self.__db_type)
        # 增加一个db type参数
        self.dbtype = self.__db_type

    def execute_query(self, sql, dict_mark=False, args=()):
        """
        执行查询语句，获取结果

        Args:
            sql(str): sql语句，注意防注入
            dict_mark(bool): 是否以字典形式返回，默认为False
            args(list/tuple): 传入参数, 默认为(), 在某些sql中需设为None

        Returns:
            list: result-查询结果集，返回类型取决于数据库类型
        """
        result = []
        conn = self.__pool.connection()
        cur = conn.cursor()
        try:
            if dict_mark:
                cur.execute(sql, args)
                # name为description的第一个内容，表示为字段名
                fields = [desc[0] for desc in cur.description]
                rst = cur.fetchall()
                if rst:
                    result = [dict(zip(fields, row)) for row in rst]
            else:
                cur.execute(sql, args)
                result = cur.fetchall()
        except Exception as e:
            # 将异常信息抛出
            self.e_log.error(e, exc_info=True)
            raise Exception("异常信息: " + str(e))
        cur.close()
        conn.close()
        return result

    def execute_query_single(self, sql, dict_mark=False, args=()):
        """
        执行查询语句，获取单行结果

        Args:
            sql(str): sql语句，注意防注入
            dict_mark(bool): 是否以字典形式返回，默认为False
            args(list/tuple): 传入参数, 默认为(), 在某些sql中需设为None

        Returns:
            list: result-查询结果集，返回类型取决于数据库类型
        """
        result = []
        conn = self.__pool.connection()
        cur = conn.cursor()
        try:
            if dict_mark:
                cur.execute(sql, args)
                # name为description的第一个内容，表示为字段名
                fields = [desc[0] for desc in cur.description]
                rst = cur.fetchone()
                if rst:
                    result = dict(zip(fields, rst))
            else:
                cur.execute(sql, args)
                result = cur.fetchone()
        except Exception as e:
            # 将异常信息抛出
            self.e_log.error(e, exc_info=True)
            raise Exception("异常信息: " + str(e))
        cur.close()
        conn.close()
        return result

    def execute(self, sql, args=()):
        """
        执行增删改语句, 实际执行的是execute_iud

        Args:
            sql(str): sql语句，注意防注入
            args(list/tuple): 传入参数, 默认为(), 在某些sql中需设为None

        Returns:
            int: count-影响行数,mysql和sqlite有返回值
        """
        return self.execute_iud(sql, args)

    def execute_iud(self, sql, args=()):
        """
        执行增删改语句

        Args:
            sql(str): sql语句，注意防注入
            args(list/tuple): 传入参数, 默认为(), 在某些sql中需设为None

        Returns:
            int: count-影响行数,mysql和sqlite有返回值
        """
        conn = self.__pool.connection()
        cur = conn.cursor()
        count = 0
        try:
            if self.__db_type == "presto":
                cur.execute(sql, args)
                cur.fetchone()
            else:
                result = cur.execute(sql, args)
                conn.commit()
                if self.__db_type == "mysql":
                    count = result
                if self.__db_type == "sqlite3":
                    count = result.rowcount
        except Exception as e:
            if self.__db_type != "presto":
                conn.rollback()
            # 将异常信息抛出
            self.e_log.error(e, exc_info=True)
            raise Exception("异常信息: " + str(e))
        cur.close()
        conn.close()
        return count

    def executebatch(self, sql, args):
        """
        批量执行增删改语句，实际执行的是execute_many_iud

        Args:
            sql(str): sql语句，注意防注入
            args(list/tuple): 参数,内部大小与sql语句中参数数量一致

        Returns:
            int: count-影响行数,mysql和sqlite有返回值
        """
        return self.execute_many_iud(sql, args)

    def execute_many_iud(self, sql, args):
        """
        批量执行增删改语句

        Args:
            sql(str): sql语句，注意防注入
            args(list/tuple): 参数,内部大小与sql语句中参数数量一致

        Returns:
            int: count-影响行数,mysql和sqlite有返回值
        """
        conn = self.__pool.connection()
        cur = conn.cursor()
        count = 0
        loopK = 5000
        try:
            k = len(args)
            if k > loopK:
                n = k // loopK
                for i in range(n):
                    arg = args[(i * loopK): ((i + 1) * loopK)]
                    if self.__db_type == "presto":
                        cur.executemany(sql, arg)
                        cur.fetchone()
                    else:
                        cur.executemany(sql, arg)
                        conn.commit()
                arg = args[(n * loopK):]
                if len(arg) > 0:
                    if self.__db_type == "presto":
                        cur.executemany(sql, arg)
                        cur.fetchone()
                    else:
                        cur.executemany(sql, arg)
                        conn.commit()
            else:
                if self.__db_type == "presto":
                    cur.executemany(sql, args)
                    cur.fetchone()
                else:
                    result = cur.executemany(sql, args)
                    conn.commit()
                    if self.__db_type == "mysql":
                        count = result
                    if self.__db_type == "sqlite3":
                        count = result.rowcount
        except Exception as e:
            if self.__db_type != "presto":
                conn.rollback()
            # 将异常信息抛出
            self.e_log.error(e, exc_info=True)
            raise Exception("异常信息: " + str(e))
        cur.close()
        conn.close()
        return count

    def execute_proc(self, proc_name, args=()):
        """

        Parameters
        ----------
        proc_name: str
            存储过程/函数名
        args: list/tuple
            参数，默认为None

        Returns
        -------
        result: list
            结果集
        args_out: list
            参数最终结果（用于out，顺序与传参一致）
        """
        args_out = ()
        conn = self.__pool.connection()
        cur = conn.cursor()
        try:
            cur.callproc(proc_name, args)
            result = cur.fetchall()
            if args:
                sql = "select " + ",".join(["_".join(["@", proc_name, str(index)]) for index in range(len(args))])
                cur.execute(sql)
                args_out = cur.fetchone()
            conn.commit()
        except Exception as e:
            conn.rollback()
            # 将异常信息抛出
            self.e_log.error(e, exc_info=True)
            raise Exception("异常信息: " + str(e))
        cur.close()
        conn.close()
        return result, args_out

    def loop_row(self, obj, fun_name, sql, args=()):
        """
        执行查询语句，并且对游标每行结果反射调用某个处理方法
        主要是考虑一些表记录太大时，不能一次性取出,游标式取数据

        Args:
            obj(obj): 对象或者模块
            fun_name(str): 调用方法名
            sql(str): sql语句，注意防注入
            args(list/tuple): 传入参数默认为空

        Returns:
            Iterator: generator-迭代器，返回调用fun(row)获取的结果的生成器
        """
        fun = fun_name
        if obj is not None:
            fun = getattr(obj, fun_name)
        conn = self.__pool.connection()
        cur = conn.cursor()
        try:
            cur.execute(sql, args)
            while True:
                row = cur.fetchone()
                if row is None:
                    break
                fun(row)
        except Exception as e:
            # 将异常信息抛出
            self.e_log.error(e, exc_info=True)
            raise Exception("异常信息: " + str(e))
        cur.close()
        conn.close()

    def loop_row_custom(self, sql, args=()):
        """
        执行查询语句，并且对游标每行结果执行某些操作，由于需要内部修改，弃用
        主要是考虑一些表记录太大时，不能一次性取出,游标式取数据

        Args:
            sql(str): sql语句，注意防注入
            args(list/tuple): 传入参数
        """
        conn = self.__pool.connection()
        cur = conn.cursor()
        try:
            cur.execute(sql, args)
            while True:
                row = cur.fetchone()
                if row is None:
                    break
                # 在此编写你想做的操作
                print(row)
        except Exception as e:
            # 将异常信息抛出
            self.e_log.error(e, exc_info=True)
            raise Exception("异常信息: " + str(e))
        cur.close()
        conn.close()
