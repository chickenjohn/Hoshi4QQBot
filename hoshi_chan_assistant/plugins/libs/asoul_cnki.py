from logging import info
import requests, json
import time

async def asoul_cnki_mod(compos):
    url = "https://asoulcnki.asia/v1/api/check"

    text_req = {"text": compos}
    response = requests.post("https://asoulcnki.asia/v1/api/check", json=text_req)
    res = response.json()
    if res["message"] == "success":
        rate_res = float(res["data"]["rate"]) * 100.0
        text_res = f"总文字复制比：{rate_res:.2f}%"
        return text_res

    return None