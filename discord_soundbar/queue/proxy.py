import json


try:
    proxies = json.load(open("proxy.json"))
except FileNotFoundError:
    proxies = {}
