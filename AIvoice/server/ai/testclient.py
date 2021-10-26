# -*- coding: UTF-8 -*-
import requests
import json
import datetime

a = datetime.datetime.now()
url2 = 'http://localhost:9042/nlu/predict'
data = {
    "text": "打开东门摄像头"
}
json_data2 = json.dumps(data)
r2 = requests.post(url=url2, data=json_data2, headers={'content-type': 'application/json'})
print(json.loads(r2.text, encoding="utf-8"))
print(datetime.datetime.now() - a)
