from exceptiongroup import catch
from okx.websocket.WsUtils import getServerTime
import time

while True:
    try:
        ts = int(getServerTime()) / 1000
        print( ts)
        time.sleep(5)
    except Exception as e:
        print(e)
