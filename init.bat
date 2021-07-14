@echo off
set rarPath=D:\WinRAR;C:\Program Files (x86)\WinRAR
set Path=%PATH%;C:\Windows\System32\inetsrv;
::win7、win8环境下以管理员模式运行，获取的当前目录（%cd%）为C:\Windows\System32，需执行如下命令才能到当前目录（非管理员模式执行也没问题）
cd /d %~dp0
::跳转父目录作为根目录




mklink /D %CD%\myIRdev\src\commonlib %CD%\commonlib


mklink /D %CD%\bridgeLCD\src\commonlib %CD%\commonlib


pause