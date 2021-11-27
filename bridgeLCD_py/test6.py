
from requests import get

token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJlMzJkYmVjMTI4MTk0ZDAxODk1MDY2YTA0MWQ1NDNjNCIsImlhdCI6MTYzMDExODgyNCwiZXhwIjoxOTQ1NDc4ODI0fQ.aBRaWzvHyKixnX1MiCu3uqZ4W2De44n6TynsSjUY1DY"


url = "http://192.168.3.168:8123/api/lovelace/config/lovelace-led1"
headers = {
    "Authorization": "Bearer " + token,
    "content-type": "application/json",
}

response = get(url, headers=headers)
print(response.text)


