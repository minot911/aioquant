# -*- coding:utf-8 -*-
import websocket
import json


def on_message(ws, message):  # 服务器有数据更新时，主动推送过来的数据
    ms=json.loads(message)
    print(message)


def on_error(ws, error):  # 程序报错时，就会触发on_error事件
    print(error)

def on_close(ws):
    print("Connection closed ……")


def on_open(ws):  # 连接到服务器之后就会触发on_open事件，这里用于send数据
    req = '{"event":"subscribe", "channel":"btc_usdt.deep"}'
    print(req)
    ws.send(req)

if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://api.zb.live/websocket",
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open
    ws.run_forever(ping_timeout=15)