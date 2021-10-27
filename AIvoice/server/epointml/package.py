# -*- coding: utf-8 -*-
import shutil
import os
import codecs
import sys

# replace string append
sysapd = ['.cp35-win_amd64',
          '.cp36-win_amd64',
          '.cp37-win_amd64',
          '.cpython-35m-x86_64-linux-gnu',
          '.cpython-36m-x86_64-linux-gnu',
          '.cpython-37m-x86_64-linux-gnu']


def copydir(dir, targetdir, ignorelst):
    """
    找到并复制文件

    :param str dir: 源目录
    :param str targetdir: 目标目录
    :param list ignorelst: 忽略文件列表
    """
    if not os.path.exists(targetdir):
        os.makedirs(targetdir)

    if os.path.isfile(dir):
        shutil.copy(dir, targetdir)
        return

    lst = os.listdir(dir)
    # print(lst)
    for item in lst:
        fp = "{0}/{1}".format(dir, item)
        tp = "{0}/{1}".format(targetdir, item)
        if item in ignorelst:
            continue
        elif os.path.isdir(fp):
            copydir(fp, tp, ignorelst)
        elif os.path.isfile(fp):
            # todo: test if append name works for importing.
            for i in range(len(sysapd)):
                # fp = fp.replace(sysapd[i], '')
                tp = tp.replace(sysapd[i], '')
            shutil.copy(fp, tp)
        else:
            print("unexpected file.")


def cleandir(dir, ignorelst):
    """
    清除目录

    Parameters
    ----------
    dir: str
        目录名称
    ignorelst: list
        忽略列表

    """
    lst = os.listdir(dir)
    for item in lst:
        if item in ignorelst:
            continue
        if os.path.isdir(dir + "/" + item):
            cleandir(dir + "/" + item, ignorelst)
        elif os.path.isfile(dir + "/" + item):
            if item.endswith('.pyd') or item.endswith('.so') or item.endswith('.c'):
                os.remove(dir + "/" + item)
                print(dir + "/" + item)


def scandir(dir, ignorelst, retlst):
    """
    用递归方法扫描目录，拿到所有py文件

    :param str dir: 目录
    :param list ignorelst: 忽略列表
    :param list retlst: 返回文件
    """
    lst = os.listdir(dir)
    for item in lst:
        if item in ignorelst:
            continue
        fp = "{0}/{1}".format(dir, item)
        if os.path.isdir(fp):
            scandir(fp, ignorelst, retlst)
        elif os.path.isfile(fp):
            if item.endswith('.py'):
                retlst.append(fp)


def move(rootpath, igl, pn):
    """
    移动目录

    Parameters
    ----------
    rootpath: str
        根目录
    igl: list
        忽略列表
    pn: str
        文件目录
    """
    ignorelst = ['target', '.project', '.idea', '.pydevproject', '.DS_Store',
                 'build', '__pycache__', 'gen', '.vscode']
    ignorelst += igl
    tp = "{0}/{1}".format(rootpath, 'target')
    copydir(rootpath + '/' + pn, tp, ignorelst)

    # for i in ignorelst1:
    #     copydir(rootpath + "/" + i, rootpath + '/target/' + i, [])
    # pygen(rootpath, ignorelst1)


def clean(rootpath, ignorelst, pn):
    """
    清除目录

    Parameters
    ----------
    rootpath: str
        根目录
    ignorelst: list
        忽略列表
    pn: str
        文件目录
    """
    ignorelst1 = ['target', '.project', '.idea', '.pydevproject', '.DS_Store',
                  'build', '__pycache__']
    ignorelst1 += ignorelst
    print("Start clean compiled files.")
    cleandir(rootpath, ignorelst1)

    bp = rootpath + "/" + "build"
    if os.path.exists(bp):
        shutil.rmtree(bp)
        print(bp)
    sp = rootpath + "/" + "setup.py"
    if os.path.exists(sp):
        os.remove(sp)
        print(bp)
    spn = rootpath + "/" + pn
    if os.path.exists(spn):
        shutil.rmtree(spn)
        print(spn)


def gen(rootpath, ignorelst1):
    """
    产生目录

    Parameters
    ----------
    rootpath: str
        根目录
    ignorelst1: list
        忽略列表
    """
    ignorelst = ['target', '.project', '.idea', '.evproject', '.DS_Store',
                 'build', '__pycache__', '__init__.py', 'setup.py', 'package.py']
    ignorelst += ignorelst1
    retlst = []
    scandir(rootpath, ignorelst, retlst)

    filename = 'setup.py'
    with codecs.open(filename, 'w', encoding='utf-8') as f:
        f.write("#-*- coding:utf-8 -*-\n")
        f.write("from distutils.core import setup\n")
        f.write("from Cython.Build import cythonize\n\n")
        f.write("setup(ext_modules = cythonize([\n")
        k = len(retlst)
        for i in range(k - 1):
            line = "'{0}',\n".format(retlst[i])
            f.write(line)
        if k > 0:
            line = "'{0}',\n".format(retlst[-1])
            f.write(line)
        f.write("]))\n")


def copy_init(rootpath, absolute_root, ignore=None):
    """
    将__init__文件拷贝进target目录

    :param str rootpath: 根目录
    :param str absolute_root: 绝对路径
    :param list ignore: 忽略列表
    :return:
    """
    if ignore is None:
        ignore = ['target', '__pycache__']
    dirlist = os.listdir(rootpath)
    for i in dirlist:
        if i in ignore:
            continue
        cp = rootpath + '/' + i
        if os.path.isdir(cp):
            ka = len(absolute_root)
            tp = cp[:ka] + '/target/' + cp[ka:]
            if not os.path.exists(tp):
                os.makedirs(tp)
            copy_init(cp, absolute_root, ignore)
        elif i == "__init__.py":
            ka = len(absolute_root)
            tp = cp[:ka] + '/target/' + cp[ka:]
            print(tp)
            shutil.copy(cp, tp)


if __name__ == "__main__":
    if sys.platform == 'win32':
        package_name = os.path.dirname(__file__).split('/')[-1]
    elif sys.platform == 'linux':
        package_name = os.path.realpath(__file__).split("/")[-2]
    else:
        package_name = os.path.realpath(__file__).split("/")[-2]

    rootpath = os.path.split(os.path.realpath(__file__))[0].replace("\\", "/")
    if len(sys.argv) > 1:
        package_name = sys.argv[1]
    print("rootpath=%s" % rootpath)
    print("package_name=%s" % package_name)

    ignorestr = "config"
    ignorelst = ignorestr.split(",")

    # 生成编译文件
    gen(rootpath, ignorelst)

    # 执行编译命令
    os.system("python setup.py build_ext -i")

    # 移动编译文件
    move(rootpath, ignorelst, pn=package_name)

    # 清理编译剩余文件
    clean(rootpath, ignorelst, pn=package_name)

    copy_init(rootpath, rootpath)
