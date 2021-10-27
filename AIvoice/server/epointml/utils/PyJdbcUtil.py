# -*- coding:utf-8 -*-
"""
Description: 使用jar包驱动的方式连接数据库
可能有人要问了，为什么不用继承，和JBDCUtil类统一起来，我觉得这个只是终极备胎，大部分情况不应该露面所以宁愿重复代码也不把他独立
实际上修改时，代码除了建立连接部分外，只需要从JBDCUtil复制过来即可
额外依赖py2jdbc>=0.0.6，且环境已有jdk

@author: WangLeAi

@date: 2021/6/18
"""
import importlib

from DBUtils.PooledDB import PooledDB

from .logger import elog


class DbPoolUtil(object):

    def __init__(self, jdbcurl="", username="", password="", classpath=None):
        """
        数据库连接初始化

        Args:
            jdbcurl(str): 标准jdbc连接字符串，和java连接时使用一致
            username(str): 用户名，如果需要的话
            password(str): 密码，如果需要的话
            classpath(list): java驱动包依赖，示例["path/to/presto-jdbc-0.217.jar"]
        """
        self.e_log = elog()
        parts = jdbcurl.split(":", 2)
        self.__db_type = parts[1]
        kwargs = {
            "classpath": classpath
        }
        db_creator = importlib.import_module("py2jdbc")
        if username and password:
            self.__pool = PooledDB(db_creator, 0, 50, 0, 1000, False, None, None, True, None, 1,
                                   jdbcurl, username, password, **kwargs)
        else:
            self.__pool = PooledDB(db_creator, 0, 50, 0, 1000, False, None, None, True, None, 1,
                                   jdbcurl, **kwargs)

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


