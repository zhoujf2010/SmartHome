# import paho.mqtt.client as mqtt
# import time

# url ="home/sonoff/MySonoff-8ed41d"


# def on_connect(client, userdata, flags, rc):
#     print(22)
#     print("Connected with result code "+str(rc))

#     # Subscribing in on_connect() means that if we lose the connection and
#     # reconnect then subscriptions will be renewed.
#     client.subscribe(url)
#     client.subscribe(url + "/stat")
#     client.subscribe(url + "/ip")
#     client.subscribe(url + "/Temperature")
#     client.subscribe(url + "/Humidity")

#     client.publish(url,"12")

# def on_message(client, userdata, msg):
#     print(msg.topic+" "+str(msg.payload.decode("utf-8")))

# client =mqtt.Client("testxxx")
# client.on_connect = on_connect
# client.on_message = on_message
# client.connect("192.168.3.168")
# print(1)
# time.sleep(5)
# client.disconnect()



pin = 0
print('pin：',pin)

cmd = 0
param = 0
serial_data = (cmd << 6) | (param << 4) | pin
print('设置',serial_data)


cmd = 1
param = 1
serial_data = (cmd << 6) | (param << 4) | pin
print('置高',serial_data)

param =0
serial_data = (cmd << 6) | (param << 4) | pin
print('置低',serial_data)



cmd = 0
param = 2
serial_data = (cmd << 6) | (param << 4) | pin
print('设置读',serial_data)


cmd = 2
param = 0
serial_data = (cmd << 6) | (param << 4) | pin
print('读值',serial_data)
