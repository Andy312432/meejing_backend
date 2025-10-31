import requests
import json

url = "http://127.0.0.1:8000/api/"

#註冊帳號
def register():
    payload = {
        "username": "test1",
        "email": "abc@gmail.com"
    }
    try:
        response = requests.request("POST", url + "auth/register/", data=payload)
    except Exception as e:
        print("Error during register request:", e)
        return None

#登入帳號(取得token(access)), refresh 為刷新時使用
def login():
    payload = {
        "username": "root",
        "password": "root"
    }
    try:
        response = requests.request("POST", url + "auth/token/login/", data=payload)
    except Exception as e:
        print("Error during login request:", e)
        return None
    
    print(response)
    return response.json()

#取得使用者資料
def me(token):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    try:
        response = requests.request("GET", url + "auth/me/", headers=headers)
    except Exception as e:
        print("Error during me request:", e)
        return None
    
    print(response)
    return response.json()

#刷新token
def refresh(token):
    payload = {
        "refresh": token
    }
    try:
        response = requests.request("POST", url + "auth/token/refresh/", data=payload)
    except Exception as e:
        print("Error during refresh request:", e)
        return None
    print(response)
    return response.json()


token = login()
print(token)

token = refresh(token.get("refresh"))

me_data = me(token.get("access"))
print(me_data)
