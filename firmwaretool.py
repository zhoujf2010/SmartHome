"""
固件工具，
可烧录固件，更新固件，配置固件
"""

import subprocess
import requests
import scapy.all as scapy
import time

# pip install winwifi   (https://pypi.org/project/winwifi/)
# 有个bug，带有密码的wifi连接失败，修改Lib\site-packages\winwifi
#gen_profile函数增加：
# else:
#     profile = profile.replace('{auth}', 'WPA2PSK')
#     profile = profile.replace('{encrypt}', 'AES')
#     profile = profile.replace('{passwd}', passwd)
#connect函数中，将if not passwd:注释掉

#扫描wifi信号源
def scanWifi():
    results = subprocess.check_output(["wifi", "scan"])
    results = results.decode("utf-8") 
    results = results.replace("\r","")
    ls = results.split("\n")
    result =[]
    for i in range(len(ls)):
        if ls[i].startswith("SSID"):
            name = ls[i].split(":")[1].strip()
            tmp = [row.strip().split(":")[1].strip() for row in ls[i:i+8] if row.strip().startswith("Signal")]
            signal = int(tmp[0][:-1]) if len(tmp) >0 else 0
            result.append([name,signal])
    #根据信息强度排序
    result.sort(key=lambda x: x[1],reverse=True)
    return result


def arp_scan(ip):
    answer, uanswer = scapy.srp(scapy.Ether(dst="ff:ff:ff:ff:ff:ff") / scapy.ARP(pdst=ip), inter=0.1, timeout=2, verbose=False)
    mac_list = []
    for send, recv in answer:
        # if recv[scapy.ARP].op == 2:
        mac_list.append((recv[scapy.ARP].psrc, recv[scapy.Ether].hwsrc))
    return mac_list

#扫描局域网内所有的IP设备
def scanAllIps(target_ip):
    # 创建ARP包
    arp = scapy.ARP(pdst=target_ip)
    # 广播 ff:ff:ff:ff:ff:ff
    ether = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
    # stack them
    # packet = 
    result = scapy.srp(ether / arp, timeout=3, verbose=0,inter=0.1,)[0]
    # result = scapy.srp(ether / arp, timeout=2, verbose=False, inter=0.1)[0]

    # a list of clients, we will fill this in the upcoming loop
    clients = []
    for sent, received in result:
        # for each response, append ip and mac address to `clients` list
        clients.append({'ip': received.psrc, 'mac': received.hwsrc})
    return clients

#获取当前连接的wifi名称
def getCurrentConnect():
    results = subprocess.check_output(["wifi", "connected"])
    results = results.decode("utf-8")
    current = results.replace("\r","").replace("\n","")
    return current


#设置新的设备
def DoSetNewDev(wifisid,wifipassword,mqttIP):
    #扫描当前所有wifi信息
    result = scanWifi()
    #筛选属于智能家居设备
    result = [row for row in result if row[0].startswith("MySmart-") or row[0].startswith("MySonoff-")]

    for i in range(len(result)):
        print("[%d] %s(%d)"%(i,result[i][0],result[i][1]))
    print("扫描到以上设备，请选择编号继续[0]：")
    choose = input()
    
    sid = result[int(choose)][0]
    print("准备处理设备：%s" % sid)

    #扫描网段中所有IP
    clients = scanAllIps("192.168.3.1/24")
    allips = [row['ip'] for row in clients]
    print(allips)

    currentWifi = getCurrentConnect()
    print("当前连接wifi信号：%s" % currentWifi)

    #切换到设备的wifi
    print("准备切换wifi设备")
    subprocess.check_output(["wifi", "forget",sid])
    subprocess.check_output(["wifi", "connect",sid,"12345678"])
    time.sleep(3)

    #读取设备相关信息
    version = requests.post('http://192.168.4.1/version').text
    devicetype = requests.post('http://192.168.4.1/devicetype').text
    devicename = requests.post('http://192.168.4.1/name').text
    print("已连接到设备上，devicetype:%s,devicename:%s,version:%s"%(devicetype,devicename,version))

    print("准备设置设备信息")
    #设置SID 密码
    pload = {'id':sid,'newssid':wifisid,'newpass':wifipassword,'mqttIP':mqttIP}
    print(requests.post('http://192.168.4.1/APsubmit',data = pload))
    #重启
    print(requests.post('http://192.168.4.1/esprestart'))
    print("设置完成")
    
    print("连接回至:%s"%currentWifi)

    subprocess.check_output(["wifi", "connect",currentWifi])
    print("切回成功")

    #扫描网段中所有IP
    clients = scanAllIps("192.168.3.1/24")
    allips2 = [row['ip'] for row in clients]
    print(allips2)

    for i in allips:
        if i in allips2:
            allips2.remove(i)
    print(allips2)


if __name__ == '__main__':
    DoSetNewDev('qinhh','58766730','192.168.3.168')
    # dt = arp_scan("192.168.3.182/24")
    # print(len(dt))
    # print(dt)
    # dt = scanAllIps("192.168.3.1/24")
    # print(len(dt))
    # print(dt)