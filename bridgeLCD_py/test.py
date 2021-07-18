import paho.mqtt.client as mqtt
import time

#url = 'home/mylightsensor/MySonoff-df62df' #太阳能
# url = 'home/myhcsr/MySonoff-e37fff' #人体感应
# url = 'home/mydht11/MySonoff-e7236f' #温度
url = "home/myirdev/myIR1"
url ="#"
# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    # client.subscribe(url + "/stat")
    # client.subscribe(url + "/ip")
    # client.subscribe(url + "/Temperature")
    # client.subscribe(url + "/Humidity")
    client.subscribe(url)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload.decode("utf-8")))


print("---")
client =mqtt.Client("test")
client.on_connect = on_connect
client.on_message = on_message
client.connect("192.168.3.168")
print("22")

time.sleep(3)
# client.publish("home/myirdev/MySonoff-f15525","29,0xD5F2A,24")
# client.publish(url,"stat")
# print("33")
# client.publish(url,"ip")


# time.sleep(3)
# client.publish("home/myirdev/MySonoff-f15525","FF02FD")
# print("33")


# time.sleep(5)

client.loop_forever()


client.disconnect()