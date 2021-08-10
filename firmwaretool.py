"""
固件工具，
可烧录固件，更新固件，配置固件
"""

import subprocess
import requests
import scapy.all as scapy
import time
from zeroconf import ServiceBrowser, Zeroconf
import socket

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
    answer, uanswer = scapy.srp(scapy.Ether(dst="ff:ff:ff:ff:ff:ff") / scapy.ARP(pdst=ip), inter=0.1, timeout=2, verbose=False)
    mac_list = []
    for send, recv in answer:
        # if recv[scapy.ARP].op == 2:
        mac_list.append((recv[scapy.ARP].psrc, recv[scapy.Ether].hwsrc))
    return mac_list


def scanAllIps(target_ip):
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
        device = {name.split('.')[0]: address}
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
    return listener.devices

def getOfflineDevices():
    '''
    获取未连接的设备
    '''
    # 扫描当前所有wifi信息
    result = scanWifi()
    # 筛选属于智能家居设备
    result = [row for row in result if row[0].startswith("MySmart-") or row[0].startswith("MySonoff-")]
    return result

def autoTryCommit(url, pload, times):
    for i in range(times):
        try:
            return requests.post(url, data=pload, timeout=5)
        except Exception as ex:
            print("try.. again")
            continue
    raise("多次尝试失败")

def chooseDevices(list):
    '''
    命令行挑选设备
    '''
    pass

def DoSetNewDev(wifisid, wifipassword, mqttIP):
    '''
    设置新的设备
    '''
    # 获取未消配置的设备
    result = getOfflineDevices()

    for i in range(len(result)):
        print("[%d] %s(%d)" % (i, result[i][0], result[i][1]))
    print("扫描到以上设备，请选择编号继续[0]：",end="")
    choose = input()
    if choose == "-1":
        exit(0)

    sid = result[int(choose)][0]
    print("准备处理设备：%s" % sid)

    currentWifi = getCurrentConnect()
    print("当前连接wifi信号：%s" % currentWifi)

    # 扫描网段中所有设备
    devices = getOnlineDevices()

    # 切换到设备的wifi
    print("准备切换wifi设备")
    subprocess.check_output(["wifi", "forget", sid])
    subprocess.check_output(["wifi", "connect", sid, "12345678"])

    # 读取设备相关信息
    print("获取设备相关信息……")
    autoTryCommit('http://192.168.4.1/version', "", 10)
    version = requests.get('http://192.168.4.1/version').text
    devicetype = requests.get('http://192.168.4.1/devicetype').text
    devicename = requests.get('http://192.168.4.1/name').text
    print("已连接到设备上，devicetype:%s,devicename:%s,version:%s" % (devicetype, devicename, version))

    print("准备设置设备信息")
    # 设置SID 密码
    pload = {'id': sid, 'newssid': wifisid, 'newpass': wifipassword, 'mqttIP': mqttIP}
    autoTryCommit('http://192.168.4.1/APsubmit', pload, 5)
    # 重启
    autoTryCommit('http://192.168.4.1/esprestart', pload, 5)
    print("设置完成")

    print("连接回至:%s……" % currentWifi)
    subprocess.check_output(["wifi", "connect", currentWifi])
    print("切回成功")
    subprocess.check_output(["wifi", "forget", sid])

    # 扫描网段中所有IP
    print("扫描网段中所有IP")
    while True:
        allips2 = getOnlineDevices()
        for i in devices:
            if i in allips2:
                allips2.remove(i)
        # print(allips2)
        if len(allips2) > 0:
            break
    newip = allips2[0][devicename]
    devicename2 = requests.get('http://'+newip+'/name').text
    print(devicename2)

    print("---------finish-----------------")
    print("新设备IP：%s，设备名：%s，设备类型：%s，固件版本：%s" % (allips2[0], devicename, devicetype, version))


if __name__ == '__main__':
    print("功能：")
    print("[0] 扫描设备")
    print("[1] 配置设备")
    print("[2] 初使化设备")
    print("[3] 更新设备固件")
    print("请选择执行命令：",end="")
    index = input()
    
    if index not in ["0","1","2","3"]:
        print("输入命令不正确")
        exit(0)
    
    if index =="0":
        #mDNS扫描设备
        devices = getOnlineDevices()
        print(devices)
        #IP扫描
        # dt = arp_scan("192.168.3.1/24")
        # for i in dt:
        #     print(i[0])

    elif index =="1":
        # DoSetNewDev('qinhh','58766730','192.168.3.168')
        DoSetNewDev('Epoint_Tech', 'epointtech', '')

