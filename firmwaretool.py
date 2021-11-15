"""
固件工具，
可烧录固件，更新固件，配置固件
"""

import subprocess
import requests
import time
from scapy import VERSION
from zeroconf import ServiceBrowser, Zeroconf
import socket
import tempfile
import os
import datetime
import pathlib
import shutil
import pandas as pd 
import numpy as np
import json


# pip install winwifi   (https://pypi.org/project/winwifi/)
# 有个bug，带有密码的wifi连接失败，修改Lib\site-packages\winwifi
# gen_profile函数增加：
# else:
#     profile = profile.replace('{auth}', 'WPA2PSK')
#     profile = profile.replace('{encrypt}', 'AES')
#     profile = profile.replace('{passwd}', passwd)
# connect函数中，将if not passwd:注释掉


def scanWifi():
    '''
    扫描wifi信号源
    '''
    results = subprocess.check_output(["wifi", "scan"])
    results = results.decode("utf-8")
    results = results.replace("\r", "")
    ls = results.split("\n")
    result = []
    for i in range(len(ls)):
        if ls[i].startswith("SSID"):
            name = ls[i].split(":")[1].strip()
            tmp = [row.strip().split(":")[1].strip() for row in ls[i:i+8] if row.strip().startswith("Signal")]
            signal = int(tmp[0][:-1]) if len(tmp) > 0 else 0
            result.append([name, signal])
    # 根据信号强度排序
    result.sort(key=lambda x: x[1], reverse=True)
    return result


def arp_scan(ip):
    import scapy.all as scapy
    answer, uanswer = scapy.srp(scapy.Ether(dst="ff:ff:ff:ff:ff:ff") / scapy.ARP(pdst=ip), inter=0.1, timeout=2, verbose=False)
    mac_list = []
    for send, recv in answer:
        # if recv[scapy.ARP].op == 2:
        mac_list.append((recv[scapy.ARP].psrc, recv[scapy.Ether].hwsrc))
    return mac_list


def scanAllIps(target_ip):
    import scapy.all as scapy
    '''
    扫描局域网内所有的IP设备
    '''
    # 创建ARP包
    arp = scapy.ARP(pdst=target_ip)
    # 广播 ff:ff:ff:ff:ff:ff
    ether = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
    # stack them
    # packet =
    result = scapy.srp(ether / arp, timeout=3, verbose=0, inter=0.1,)[0]
    # result = scapy.srp(ether / arp, timeout=2, verbose=False, inter=0.1)[0]

    # a list of clients, we will fill this in the upcoming loop
    clients = []
    for sent, received in result:
        # for each response, append ip and mac address to `clients` list
        clients.append({'ip': received.psrc, 'mac': received.hwsrc})
    return clients


def getCurrentConnect():
    '''
    获取当前连接的wifi名称
    '''
    results = subprocess.check_output(["wifi", "connected"])
    results = results.decode("utf-8")
    current = results.replace("\r", "").replace("\n", "")
    return current


class MymDNSListener:
    def __init__(self) -> None:
        self.devices = []

    def remove_service(self, zeroconf, type, name):
        print("Service %s removed" % (name,))

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        address = socket.inet_ntoa(info.addresses[0])
        device = {"name": name.split('.')[0], "ip": address}
        self.devices.append(device)
        # print("Service %s added, service info: %s" % (name, info))


def getOnlineDevices():
    '''
    获取在线的所有设备列表
    '''
    zeroconf = Zeroconf()
    listener = MymDNSListener()
    browser = ServiceBrowser(zeroconf, "_arduino._tcp.local.", listener)
    time.sleep(1)
    zeroconf.close()
    for device in listener.devices:
        devicetype = autoTryCommit("http://" + device["ip"] + "/devicetype", "", 5)
        device["devicetype"] = devicetype.text
    ret = listener.devices
    
    #加载文件中保存的信息
    data = loadRecordDevices()
    for dev in ret:
        if dev["name"] in data:
            dev["note"] = data[dev["name"]][2]
            data[dev["name"]][1] = dev["devicetype"]
    return ret


def getOfflineDevices():
    '''
    获取未连接的设备
    '''
    # 扫描当前所有wifi信息
    result = scanWifi()
    # 筛选属于智能家居设备
    result = [{"name":row[0],"signal":row[1]} for row in result if row[0].startswith("MySmart-") or row[0].startswith("MySonoff-")]
    #加载文件中保存的信息
    hashdt = loadRecordDevices()
    for dev in result:
        if dev["name"] in hashdt:
            dev["devicetype"] = hashdt[dev["name"]][1]
            dev["note"] = hashdt[dev["name"]][2]
    return result


def autoTryCommit(url, pload, times):
    for i in range(times):
        try:
            return requests.post(url, data=pload, timeout=5)
        except Exception as ex:
            print("failed,try.. again,url:",url)
            time.sleep(2)
            continue
    raise("多次尝试失败")


def autoTryConnectWifi(sid, times, passwd=''):
    '''尝试多次连接wifi'''
    for i in range(times):
        try:
            subprocess.check_output(["wifi", "connect", sid, passwd])
            return
        except Exception as ex:
            print("try.. again")
            continue
    raise("多次尝试失败")


def chooseDevices(list):
    '''
    命令行挑选设备
    '''
    for i in range(len(list)):
        # if len(list[i]) == 2:  # 离线设备
        #     print("[%d] %s(%d)" % (i, list[i][0], list[i][1]))
        # else:  # 在线设备
        print("[%d]" % i, list[i])

    print("扫描到以上设备，请选择编号继续[0]：", end="")
    choose = input()
    choose = choose if choose != '' else '0'
    if choose not in [str(i) for i in range(len(list))]:
        print("输入序号不正确")
        exit(0)
    return int(choose)


def DoSetNewDev(wifisid, wifipassword, mqttIP):
    '''
    设置新的设备
    '''
    # 获取未消配置的设备
    result = getOfflineDevices()
    index = chooseDevices(result)
    if index >= len(result):
        return

    sid = result[index]["name"]
    print("准备处理设备：%s" % sid)

    currentWifi = getCurrentConnect()
    print("当前连接wifi信号：%s" % currentWifi)

    # 扫描网段中所有设备
    devices = getOnlineDevices()

    # 切换到设备的wifi
    print("准备切换wifi设备")
    subprocess.check_output(["wifi", "forget", sid])
    autoTryConnectWifi(sid, 5, '12345678')

    # 读取设备相关信息
    print("获取设备相关信息……")
    autoTryCommit('http://192.168.4.1/version', "", 10)
    version = requests.get('http://192.168.4.1/version').text
    devicetype = requests.get('http://192.168.4.1/devicetype').text
    devicename = requests.get('http://192.168.4.1/name').text
    print("已连接到设备上，devicetype:%s,devicename:%s,version:%s" % (devicetype, devicename, version))

    print("准备设置设备信息")
    # 设置SID 密码
    pload = {'id': '', 'newssid': wifisid, 'newpass': wifipassword, 'mqttIP': mqttIP}
    autoTryCommit('http://192.168.4.1/APsubmit', pload, 5)
    # 重启
    autoTryCommit('http://192.168.4.1/esprestart', pload, 5)
    print("设置完成")

    print("连接回至:%s……" % currentWifi)
    autoTryConnectWifi(currentWifi, 5)
    print("切回成功")
    subprocess.check_output(["wifi", "forget", sid])

    # 扫描网段中所有IP
    print("扫描网段中所有设备")
    while True:
        allips2 = getOnlineDevices()
        for i in devices:
            if i in allips2:
                allips2.remove(i)
        if len(allips2) > 0:
            break
    newindex = 0
    for i in range(len(allips2)):
        if allips2[i]["name"] == devicename:
            newindex = i
            break

    newip = allips2[newindex]["ip"]
    devicename2 = requests.get('http://'+newip+'/name').text

    print("---------finish-----------------")
    print("新上线设备信息：", devicename2)
    print("新设备IP：%s，设备名：%s，设备类型：%s，固件版本：%s" % (newip, devicename, devicetype, version))

    print("请输入设备用途：",end="")
    note = input()
    #加载文件中保存的信息
    hashdt = loadRecordDevices()
    hashdt[devicename2][1] = devicetype
    hashdt[devicename2][2] = note
    saveRecoredDevices(hashdt)


def InitDevice():
    # 获取未消配置的设备
    result = getOnlineDevices()
    index = chooseDevices(result)

    device = result[index]
    print("准备处理设备：%s" % device["name"])
    autoTryCommit('http://' + device["ip"] + '/cleareeprom', '', 5)
    print("清除成功!")


def UpdataFirm():
    '''更新线上设备固件'''
    devices = getOnlineDevices()
    index = chooseDevices(devices)
    device = devices[index]
    devName = device["name"]
    print("\r\n准备处理设备：%s" % devName, end="")
    devicetype = autoTryCommit("http://" + device["ip"] + "/devicetype", "", 5).text
    version = autoTryCommit("http://" + device["ip"] + "/version", "", 5).text
    newver = "1.0"
    print("设备类型：%s，当前版本：%s" % (devicetype, version))
    print("\r\n确认是否要升级?(Y/N)", end="")
    choose = input()
    if choose != "Y":
        print("未选择升级，结束")
        return

    dir_path = os.path.dirname(os.path.realpath(__file__))
    binfilelst = []
    for path in os.listdir(dir_path + "\\bins"):
        if not path.endswith("ino.bin"):
            continue
        dt = [path]
        dt.append(path.split('_')[0])
        v = path.split('_')[1].replace('.ino.bin', '').replace('v', '').strip()
        dt.append(v)
        fname = pathlib.Path(dir_path + "/bins/" + path)
        dt.append(datetime.datetime.fromtimestamp(fname.stat().st_ctime))
        binfilelst.append(dt)

    print("\r\n确定类型?(%s)" % devicetype, end="")
    choose = input()
    devicetype = choose if choose != "" else devicetype
    print("准备写入类型：%s" % devicetype)
    binlst = [i for i in binfilelst if i[1] == devicetype]
    if len(binlst) == 0:
        print("未找到相应类型的bin，结束")
        return

    binlst.sort(key=lambda x: x[2], reverse=True)
    print("查到版本有：")
    for i in range(len(binlst)):
        print("[%d] %s,构建时间:%s" % (i, binlst[i][0],binlst[i][3]))
    print("选择版本[0]:", end="")
    index = input()
    index = 0 if index == "" else int(index)
    chooseName = binlst[index][0]

    print("选择bin文件为%s,准备写入" % chooseName)

    toolPath = "C:\\Users\\zjf\\AppData\\Local\\Arduino15\\packages\\esp8266\\hardware\\esp8266\\3.0.2\\tools\\espota.py"
    binpath = dir_path + "/bins/" + chooseName#E:\\3.杂代码\\智能家居\\MySmartHome\\bins\\commonlib.ino.bin"
    subprocess.check_output(["python", toolPath, "-i", device["ip"], "-p", "8266", "--auth=", "-f", binpath])
    print("升级成功，等待设备上线")
    newdevinfo = []
    while True:
        devices = getOnlineDevices()
        ret = [i for i in devices if i["name"] == devName]
        if len(ret) > 0:
            newdevinfo = ret[0]
            break
    print("设备已上线：", newdevinfo)
    version = autoTryCommit("http://" + newdevinfo["ip"] + "/version", "", 5).text
    print("固件版本：%s" % version)


def ScanBin():
    '''扫描新生成的bin，复制到bins文件夹内'''
    tmpdir = tempfile.gettempdir()
    binfilelst = []
    for path in os.listdir(tmpdir):
        if path.startswith("arduino_build_"):
            dt = []
            dt.append(path)
            fname = pathlib.Path(tmpdir + "/" + path)
            dt.append(datetime.datetime.fromtimestamp(fname.stat().st_mtime))
            binlst = [i for i in os.listdir(tmpdir + "/" + path) if i.endswith(".bin")]
            if len(binlst) == 0:
                continue
            dt.append(binlst[0])
            dt.append(tmpdir + "/" + path + "/" + binlst[0])
            binfilelst.append(dt)
    binfilelst.sort(key=lambda x: x[1], reverse=True)
    lastbinfile = binfilelst[0][3]
    filename = lastbinfile.split('/')[-1]
    projectName = filename[:-8]
    dir_path = os.path.dirname(os.path.realpath(__file__))
    srcfile = dir_path + "/" + projectName + "/" + projectName + ".ino"
    ver = ""
    devname = ""
    for row in pathlib.Path(srcfile).read_text(encoding="utf-8").split('\n'):
        if row.startswith("String firmversion"):
            ver = row[len("String firmversion"):].strip()
            ver = ver.replace("=", "").replace(";", "").replace("\"", "").strip()
        if row.startswith("String DEVICE"):
            devname = row[len("String DEVICE"):].strip()
            devname = devname.replace("=", "").replace(";", "").replace("\"", "").strip()

    print("获取版本：%s，设备名：%s" % (ver, devname))
    destfile = dir_path + "/bins/" + devname + "_v" + ver + ".ino.bin"
    shutil.copyfile(lastbinfile, destfile)
    print(lastbinfile)


def loadRecordDevices():#加载记录文件的设备信息
    file ="./devices.csv"
    if not os.path.exists(file):
        np_data=[]
        save = pd.DataFrame(np_data, columns = ['name', 'type', 'note']) 
        save.to_csv(file,index=False,header=True)  #index=False,header=False表示不保存行索引和列标题

    data = pd.read_csv(file, header=None,encoding="ansi")
    data = list(data.values[1:])
    
    hashdt ={}
    for item in data:
        hashdt[item[0]] = item
    return hashdt

def saveRecoredDevices(hashdt):
    data = []
    for key in hashdt:
        data.append(hashdt[key])

    file ="./devices.csv"
    save = pd.DataFrame(np.array(data), columns = ['name', 'type', 'note']) 
    save.to_csv(file,index=False,header=True,encoding="ansi")  #index=False,header=False表示不保存行索引和列标题

def scanDevice():
    #加载文件中保存的信息
    hashdt = loadRecordDevices()
    olddt = hashdt.copy()
    notfound = []
    # mDNS扫描设备
    devices1 = getOnlineDevices()
    print("\r\n在线设备：", len(devices1))
    for dev in devices1:
        if dev["name"] in hashdt:
            hashdt.pop(dev["name"])
        else:
            notfound.append([dev["name"],dev["devicetype"],"unknown"])
        print(dev)
    devices2 = getOfflineDevices()
    print("\r\n离线设备：", len(devices2))
    for dev in devices2:
        if dev["name"] in hashdt:
            hashdt.pop(dev["name"])
        else:
            notfound.append([dev["name"],"unknown","unknown"])
        print(dev)
    print("\r\n未扫描设备：", len(hashdt))
    for key in hashdt:
        print(hashdt[key])
    
    for item in notfound:
        olddt[item[0]] = item
    saveRecoredDevices(olddt)
    

if __name__ == '__main__':
    while True:
        print("功能：")
        print("[0] 扫描设备")
        print("[1] 扫描网络IP")
        print("[2] 初使化设备")
        print("[3] 重置设备")
        print("[4] 更新设备固件")
        print("[5] 复制新生成固件")
        print("[6] 退出")
        print("请选择执行命令[0]：", end="")
        index = input()
        index = index if index != '' else '0'

        if index not in ["0", "1", "2", "3", "4", "5","6"]:
            print("输入命令不正确")
            exit(0)

        if index == "0":
            scanDevice()
        elif index == "1":
            # IP扫描
            # dt = arp_scan("192.168.3.1/24")
            dt = scanAllIps("192.168.3.1/24")
            for i in dt:
                print(i)
        elif index == "2":
            tmpfile = tempfile.gettempdir()+"/firmwaretool.json"
            data =""
            if os.path.exists(tmpfile):
                data = open(tmpfile).read()
            print("请确认信息：\r\nSSID,password,mqttip")
            print(data,end="")
            ip = input()
            if ip == "":
                ip = data
            open(tmpfile,"w").write(ip)
            ip = ip.strip()
            print("准备烧写信息："+ ip)
            DoSetNewDev(ip.split(",")[0],ip.split(",")[1],ip.split(",")[2])
        elif index == "3":
            InitDevice()
        elif index == "4":
            UpdataFirm()
        elif index == "5":
            ScanBin()
        elif index == "6":
            break
        print("\r\n----------------------------")
        # print("\r\n按任意键结束……")
        # input()
