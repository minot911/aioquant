# -*- coding:utf-8 -*-

"""
Zb Trade module.
https://Zbapi.github.io/docs/spot/v1/cn

Author: HuangTao
Date:   2018/08/30
Email:  huangtao@ifclover.com
"""

import json
import hmac
import copy
import gzip
import base64
import urllib
import hashlib
import datetime,time
import struct
from urllib import parse
from urllib.parse import urljoin
from aioquant.error import Error
from aioquant.utils import logger
from aioquant.order import Order
from aioquant.tasks import SingleTask
from aioquant.utils.decorator import async_method_locker
from aioquant.utils.web import AsyncHttpRequests, Websocket
from aioquant.order import ORDER_ACTION_BUY, ORDER_ACTION_SELL
from aioquant.order import ORDER_TYPE_LIMIT, ORDER_TYPE_MARKET
from aioquant.order import ORDER_STATUS_SUBMITTED, ORDER_STATUS_PARTIAL_FILLED, ORDER_STATUS_FILLED, \
    ORDER_STATUS_CANCELED, ORDER_STATUS_FAILED
from aioquant.market import Orderbook, Trade, Kline
from aioquant.configure import config


__all__ = ("ZbRestAPI", "ZbTrade", "ZbMarket")


class ZbRestAPI:
    """Zb REST API client.

    Attributes:
        access_key: Account's ACCESS KEY.
        secret_key: Account's SECRET KEY.
        host: HTTP request host, default `http://api.zb.live`.
    """

    def __init__(self, access_key, secret_key, host=None):
        """Initialize REST API client."""
        self._host = host or "http://api.zb.today"        
        self._access_key = access_key
        self._secret_key = secret_key
        self._account_id = None

    async def get_exchange_info(self):
        """Get exchange information.

        Returns:
            success: Success results, otherwise it's None.
            error: Error information, otherwise it's None.
        """
        uri = "/data/v1/markets"
        success, error = await self.request("GET", uri)
        return success, error

    async def get_orderbook(self, symbol, depth=20, step="step0"):
        """Get latest orderbook information. GET http://api.zb.live/data/v1/depth?market=btc_usdt&size=3

        Args:
            symbol: Symbol name, e.g. `ethusdt`.
            depth: The number of market depth to return on each side, `5` / `10` / `20`, default is 10.
            step: Market depth aggregation level, `step0` / `step1` / `step2` / `step3` / `step4` / `step5`.

        Returns:
            success: Success results, otherwise it's None.
            error: Error information, otherwise it's None.

        Note:
            When type is set to `step0`, the default value of `depth` is 150 instead of 20.
        """
        symbol=symbol.replace("/", "_").lower()
        uri = "/data/v1/depth?market={symbol}&size={depth}".format(symbol=symbol,depth=depth)
        success, error = await self.request("GET", uri)
        return success, error

    async def get_trade(self, symbol):
        """Get latest trade information.http://api.zb.live/data/v1/ticker?market=btc_usdt

        Args:
            symbol: Symbol name, e.g. `ethusdt`.

        Returns:
            success: Success results, otherwise it's None.
            error: Error information, otherwise it's None.
        """
        symbol=symbol.replace("/", "-").lower
        uri = "/data/v1/ticker?market={}".format(symbol)
        success, error = await self.request("GET", uri)
        return success, error

    async def get_kline(self, symbol, interval="1min", limit=150):
        """Get kline information.http://api.zb.live/data/v1/kline?market=btc_usdt

        Args:
            symbol: Symbol name, e.g. `ethusdt`.
            interval: Kline interval type, `1min` / `5min` / `15min` / `30min` / `60min` / `4hour` / `1day` / `1mon` / `1week` / `1year`.
            limit: Number of results per request. (default 150, max 2000.)

        Returns:
            success: Success results, otherwise it's None.
            error: Error information, otherwise it's None.

        Notes:
            If start and end are not sent, the most recent klines are returned.
        """
        symbol=symbol.replace("/", "-").lower()
        uri = "/data/v1/kline?market={}".format(symbol)      
        success, error = await self.request("GET", uri)
        return success, error

    async def get_user_accounts(self):
        """This endpoint returns a list of accounts owned by this API user.
            https://trade.zb.live/api/getSubUserList?accesskey=youraccesskey&method=getSubUserList
                    &sign=请求加密签名串&reqTime=当前时间毫秒数
        Returns:
            success: Success results, otherwise it's None.
            error: Error information, otherwise it's None.
        """
        uri = "/api/getSubUserList"
        params = {
            "accesskey" : self._access_key,
            "method": "getSubUserList"
        }
        success, error = await self.request("GET", uri, auth=True)
        return success, error

    async def get_account_balance(self):
        """This endpoint returns the balance of an account specified by account id.
            GET https://trade.zb.live/api/getAccountInfo?accesskey=youraccesskey&method=getAccountInfo
                &sign=请求加密签名串&reqTime=当前时间毫秒数

        Returns:
            success: Success results, otherwise it's None.
            error: Error information, otherwise it's None.
        """
        uri = "/api/getAccountInfo"
        info = {
            "accesskey" : self._access_key,
            "method": "getAccountInfo"
        }
        success, error = await self.request("GET", uri, params=info, auth=True)
        return success, error

    async def get_balance_all(self):
        """This endpoint returns the balances of all the sub-account aggregated.

        Returns:
            success: Success results, otherwise it's None.
            error: Error information, otherwise it's None.
        """
        uri = "/api/getAccountInfo"
        params = {
            "accesskey" : self._access_key,
            "method": "getAccountInfo"
        }
        success, error = await self.request("GET", uri, auth=True)
        return success, error

    async def create_order(self, symbol, price, quantity, order_type, client_order_id=None):
        """Create an order.
        Args:
            symbol: Symbol name, e.g. `ethusdt`.
            price: Price of each contract.
            quantity: The buying or selling quantity.
            order_type: Order type, `buy-market` / `sell-market` / `buy-limit` / `sell-limit`.
            client_order_id: Client order id.
            GET https://trade.zb.live/api/order?accesskey=youraccesskey&acctType=0
                &amount=1.502&currency=qtum_usdt&method=order&price=1.9001&tradeType=1
                &sign=请求加密签名串&reqTime=当前时间毫秒数

        Returns:
            success: Success results, otherwise it's None.
            error: Error information, otherwise it's None.
        """
        uri = "/api/order"
        if order_type == "buy-limit":
            tradeType = 1
        elif order_type == "sell-limit":
            tradeType = 0
        else:
            logger.debug("orderTpye err:", order_type, caller=self)
            return None, False
        info = {
            "accesskey": self._access_key,
            "acctType": 0,
            "amount": quantity,
            "currency": symbol.replace('/','_').lower(),
            "method": "order",
            "price": price,
            "tradeType": tradeType
        }
        success, error = await self.request("POST", uri, params=info, auth=True)
        if success["code"] != 1000:
            error = True            
        return success, error

    async def revoke_order(self, symbol, order_id):
        """Cancelling an unfilled order.
           GET https://trade.zb.live/api/cancelOrder?accesskey=youraccesskey&currency=zb_qc&id=201710111625
                &method=cancelOrder&sign=请求加密签名串&reqTime=当前时间毫秒数

        Args:
            order_id: Order id.

        Returns:
            success: Success results, otherwise it's None.
            error: Error information, otherwise it's None.
        """
        uri = "/api/cancelOrder"
        params = {
            "accesskey" : self._access_key,
            "currency": symbol.replace('/','_').lower(),
            "method": "cancelOrder",
            "id": order_id
        }
        success, error = await self.request("POST", uri, params=params, auth=True)
        return success, error

    async def get_open_orders(self, symbol, limit=50):
        """Get all open order information.
        GET https://trade.zb.live/api/getUnfinishedOrdersIgnoreTradeType?accesskey=youraccesskey
            &currency=zb_qc&method=getUnfinishedOrdersIgnoreTradeType&pageIndex=1&pageSize=10
            &sign=请求加密签名串&reqTime=当前时间毫秒数
            
        Args:
            symbol: Symbol name, e.g. `ethusdt`.
            limit: The number of orders to return, [1, 500].

        Returns:
            success: Success results, otherwise it's None.
            error: Error information, otherwise it's None.
        """
        uri = "/api/getUnfinishedOrdersIgnoreTradeType"
        
        params = {
            "accesskey": self._access_key,
            "currency": symbol.replace('/','_').lower(),
            "method": "getUnfinishedOrdersIgnoreTradeType",
            "pageIndex": 1,
            "pageSize": limit
        }
        success, error = await self.request("GET", uri, params=params, auth=True)
        return success, error

    async def get_order_status(self, order_id, symbol = None):
        """Get order details by order id.
           GET https://trade.zb.live/api/getOrder?accesskey=youraccesskey&currency=zb_qc&id=201710122805
                &method=getOrder&sign=请求加密签名串&reqTime=当前时间毫秒数
        Args:
            order_id: Order id.

        Returns:
            success: Success results, otherwise it's None.
            error: Error information, otherwise it's None.
        """
        uri = "/api/getOrder"
        
        params = {
            "accesskey": self._access_key,
            "currency": symbol.replace('/','_').lower(),
            "method": "getOrder",
            "id": order_id            
        }
        success, error = await self.request("GET", uri, params=params, auth=True)
        return success, error


    async def request(self, method, uri, params=None, body=None, auth=False):
        """Do HTTP request.

        Args:
            method: HTTP request method. `GET` / `POST` / `DELETE` / `PUT`.
            uri: HTTP request uri.
            params: HTTP query params.
            body:   HTTP request body.
            auth: If this request requires authentication.

        Returns:
            success: Success results, otherwise it's None.
            error: Error information, otherwise it's None.

            &sign=请求加密签名串&reqTime=当前时间毫秒数
            reqTime = (int)(time.time()*1000)

            params += '&sign=%s&reqTime=%d'%(sign, reqTime)

        """

        url = urljoin(self._host, uri)

        if auth:
            url = urljoin(self._host.replace("api","trade"), uri)            
            query = "&".join(["{}={}".format(k, params[k]) for k in sorted(params.keys())])
            signature = self.generate_signature(query)
            reqTime = (int)(time.time()*1000)            
            sign = 'sign=%s&reqTime=%d'%(signature, reqTime)
            url +=  '?' + query + '&' + sign

        if method == "GET":
            headers = {
                "Content-type": "application/x-www-form-urlencoded",
                "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/39.0.2171.71 Safari/537.36"
            }
        else:
            headers = {
                "Accept": "application/json",
                "Content-type": "application/json"
            }
        _, success, error = await AsyncHttpRequests.fetch(method, url, data=body, headers=headers,
                                                          timeout=10)
        if error:
            return success, error
        if not isinstance(success, dict):
            success = json.loads(success) 
        return success, None

    def generate_signature(self,params):
        sha_secret = self.digest(self._secret_key)
        signature = self.hmacSign(params, sha_secret)        
        return signature


    def hmacSign(self, aValue, aKey):
        keyb   = struct.pack("%ds" % len(aKey), aKey.encode('utf-8'))
        value  = struct.pack("%ds" % len(aValue), aValue.encode('utf-8'))
        k_ipad = self.doXOr(keyb, 0x36)
        k_opad = self.doXOr(keyb, 0x5c)
        k_ipad = self.fill(k_ipad, 64, 54)
        k_opad = self.fill(k_opad, 64, 92)
        m = hashlib.md5()
        m.update(k_ipad.encode('utf-8'))
        m.update(value)
        dg = m.digest()
        
        m = hashlib.md5()
        m.update(k_opad.encode('utf-8'))
        subStr = dg[0:16]
        m.update(subStr)
        dg = m.hexdigest()
        return dg

    def digest(self, aValue):
        value  = struct.pack("%ds" % len(aValue), aValue.encode('utf-8'))        
        h = hashlib.sha1()
        h.update(value)
        dg = h.hexdigest()
        return dg

    def fill(self, value, lenght, fillByte):
        if len(value) >= lenght:
            return value
        else:
            fillSize = lenght - len(value)
        return value + chr(fillByte) * fillSize

    def doXOr(self, s, value):
        slist = list(s.decode('utf-8'))
        for index in range(len(slist)):
            slist[index] = chr(ord(slist[index]) ^ value)
        return "".join(slist)

class ZbTrade:
    """Zb Trade module. You can initialize trade object with some attributes in kwargs.

    Attributes:
        account: Account name for this trade exchange.
        strategy: What's name would you want to created for your strategy.
        symbol: Symbol name for your trade.
        host: HTTP request host. (default "https://api.Zb.pro")
        wss: Websocket address. (default "wss://api.Zb.pro")
        access_key: Account's ACCESS KEY.
        secret_key Account's SECRET KEY.
        order_update_callback: You can use this param to specify a async callback function when you initializing Trade
            module. `order_update_callback` is like `async def on_order_update_callback(order: Order): pass` and this
            callback function will be executed asynchronous when some order state updated.
        init_callback: You can use this param to specify a async callback function when you initializing Trade
            module. `init_callback` is like `async def on_init_callback(success: bool, **kwargs): pass`
            and this callback function will be executed asynchronous after Trade module object initialized done.
        error_callback: You can use this param to specify a async callback function when you initializing Trade
            module. `error_callback` is like `async def on_error_callback(error: Error, **kwargs): pass`
            and this callback function will be executed asynchronous when some error occur while trade module is running.
    """

    def __init__(self, **kwargs):
        """Initialize Trade module."""
        e = None

        if not kwargs.get("account"):
            e = Error("param account miss")
        if not kwargs.get("strategy"):
            e = Error("param strategy miss")
        if not kwargs.get("symbol"):
            e = Error("param symbol miss")
        if not kwargs.get("host"):
            kwargs["host"] = "https://api.zb.today"
        if not kwargs.get("wss"):
            kwargs["wss"] = "wss://api.zb.today/websocket"
        if not kwargs.get("access_key"):
            e = Error("param access_key miss")
        if not kwargs.get("secret_key"):
            e = Error("param secret_key miss")
        if e:
            logger.error(e, caller=self)
            self._error_callback = kwargs.get("error_callback")
            SingleTask.run(self._error_callback, e)
            SingleTask.run(kwargs["init_callback"], False)
            return


        self._account = kwargs["account"]
        self._strategy = kwargs["strategy"]
        self._platform = kwargs["platform"]
        self._symbol = kwargs["symbol"]
        self._host = kwargs["host"]
        self._wss = kwargs["wss"]
        self._access_key = kwargs["access_key"]
        self._secret_key = kwargs["secret_key"]
        self._order_update_callback = kwargs.get("order_update_callback")
        self._init_callback = kwargs.get("init_callback")
        self._error_callback = kwargs.get("error_callback")
        self._asset_update_callback = kwargs.get("asset_update_callback")

        self._raw_symbol = self._symbol.replace("/", "").lower() 
        self._assets = {}
        self._orders = {}
        self.markets = config.markets
        # Initialize our REST API client.
        self._rest_api = ZbRestAPI(self._access_key, self._secret_key, self._host, )

        url = self._wss 
        self._ws = Websocket(url, self.connected_callback, process_binary_callback=self.process_binary, process_callback=self.process_callback)

    @property
    def orders(self):
        return copy.copy(self._orders)

    @property
    def rest_api(self):
        return self._rest_api 

    async def connected_callback(self):
        """After websocket connection created successfully, we will send a message to server for authentication."""        
        SingleTask.run(self._init_callback, True)
        await self.requestorderstatus()
        await self.requestpositiontatus()
       # await self._ws.send(params)
       # await self.markt_connected_callback()

    async def _auth_success_callback(self):
        # Get current open orders.
        pass
    @async_method_locker("ZbTrade.process_callback.locker")      
    async def process_callback(self, raw):
        msg=raw        
        #logger.debug("msg:", msg, caller=self)

        channel = msg.get("channel")
        type = channel.split('_')        
        if type[-1] == "depth":
            asks = msg["asks"]
            bids = msg["bids"]
            timestamp = msg["timestamp"]
            symbols = type[-2]
            asks.reverse()
            from aioquant.event import EventOrderbook
            EventOrderbook(Orderbook(self._platform, symbols, asks, bids, timestamp)).publish()
        if type[-1] == "getordersignoretradetype":
            if msg["code"] != 1000:
                logger.error("msg:", msg, caller=self)
                return
            
            for data in msg["data"]:          
                self._update_order(data)
        if type[-1] == "record":            
            for data in msg["record"]:          
                self._update_order(data)
            for data in msg["hrecord"]:          
                self._update_order(data)
        if type[-1] == "asset":
            for data in  msg["coins"]:
                self._update_asset(data)
   
    @async_method_locker("ZbTrade.process_binary.locker")
    async def process_binary(self, raw):
        """Process binary message that received from websocket.

        Args:
            raw: Binary message received from websocket.

        Returns:
            None.
        """
        pass

    async def create_order(self, action, price, quantity, *args, **kwargs):
        """Create an order.

        Args:
            action: Trade direction, `BUY` or `SELL`.
            price: Price of each order.
            quantity: The buying or selling quantity.
            kwargs:
                order_type: Order type, `LIMIT` / `MARKET`, default is `LIMIT`.

        Returns:
            order_id: Order id if created successfully, otherwise it's None.
            error: Error information, otherwise it's None.
        """
        order_type = kwargs.get("order_type", ORDER_TYPE_LIMIT)
        client_order_id = kwargs.get("client_order_id")
        if action == ORDER_ACTION_BUY:
            if order_type == ORDER_TYPE_LIMIT:
                t = "buy-limit"
            elif order_type == ORDER_TYPE_MARKET:
                t = "buy-market"
            else:
                e = Error("order_type error! order_type: {}".format(order_type))
                logger.error(e, caller=self)
                SingleTask.run(self._error_callback, e)
                return None, "order type error"
        elif action == ORDER_ACTION_SELL:
            if order_type == ORDER_TYPE_LIMIT:
                t = "sell-limit"
            elif order_type == ORDER_TYPE_MARKET:
                t = "sell-market"
            else:
                e = Error("order_type error! order_type:: {}".format(order_type))
                logger.error(e, caller=self)
                SingleTask.run(self._error_callback, e)
                return None, "order type error"
        else:
            logger.error("action error! action:", action, caller=self)
            e = Error("action error! action:: {}".format(action))
            logger.error(e, caller=self)
            SingleTask.run(self._error_callback, e)
            return None, "action error"
        result, error = await self._rest_api.create_order(self._symbol, price, quantity, t, client_order_id)
        if error:
            errinfo = "action:{},symbol:{},quantily:{},price:{},err:{}".format(action,self._symbol,quantity,price,result)
            e = Error(errinfo)
            SingleTask.run(self._error_callback, e)  
            return None, e
        order_id = result["id"]
        return order_id, None

    async def revoke_order(self, *order_ids):
        """Revoke (an) order(s).

        Args:
            order_ids: Order id list, you can set this param to 0 or multiple items. If you set 0 param, you can cancel
                all orders for this symbol(initialized in Trade object). If you set 1 param, you can cancel an order.
                If you set multiple param, you can cancel multiple orders. Do not set param length more than 100.

        Returns:
            Success or error, see bellow.

        NOTEs:
            DO NOT INPUT MORE THAT 10 ORDER IDs, you can invoke many times.
        """
        # If len(order_ids) == 0, you will cancel all orders for this symbol(initialized in Trade object).
        if len(order_ids) == 0:
            order_infos, error = await self._rest_api.get_open_orders(self._symbol)
            if error:
                SingleTask.run(self._error_callback, error)
                return False, error
            for order_info in order_infos:
                _, error = await self._rest_api.revoke_order(self._symbol, order_info["Id"])
                if error:
                    SingleTask.run(self._error_callback, error)
                    return False, error
            return True, None

        # If len(order_ids) == 1, you will cancel an order.
        if len(order_ids) == 1:
            success, error = await self._rest_api.revoke_order(self._symbol, order_ids[0])
            if error:
                SingleTask.run(self._error_callback, error)
                return order_ids[0], error
            else:
                return order_ids[0], None

        # If len(order_ids) > 1, you will cancel multiple orders.
        if len(order_ids) > 1:
            success, error = [], []
            for order_id in order_ids:
                _, e = await self._rest_api.revoke_order(self._symbol, order_id)
                if e:
                    SingleTask.run(self._error_callback, e)
                    error.append((order_id, e))
                else:
                    success.append(order_id)
            return success, error

    async def get_open_order_ids(self):
        """Get open order id list.

        Args:
            None.

        Returns:
            order_ids: Open order id list, otherwise it's None.
            error: Error information, otherwise it's None.
        """
        success, error = await self._rest_api.get_open_orders(self._symbol)
        if error:
            SingleTask.run(self._error_callback, error)
            return None, error
        else:
            order_infos = success
            if len(order_infos) > 100:
                logger.warn("order length too long! (more than 100)", caller=self)
            order_ids = []
            for order_info in order_infos:
                order_ids.append(str(order_info["id"]))
            return order_ids, None

    def _update_order(self, order_info):
        """Order update.

        Args:
            order_info: Order information.

        Returns:
            None.
        Note:
            order-state: Order status, `submitting` / `submitted` / `partial-filled` / `partial-canceled` / `filled` / `canceled`
        """
        order_id = str(order_info[0])
        action = ORDER_ACTION_BUY if order_info[5] == 1 else ORDER_ACTION_SELL
        state = order_info[7]
        remain = "%.8f" % (float(order_info[2]) - float(order_info[3]))
        if float(order_info[4]) != 0:
            avg_price = "%.8f" % (float(order_info[4])/float(order_info[3]))
        else:
            avg_price = 0
        ctime = order_info[6]
        utime = order_info[6]

        if state == 1:
            status = ORDER_STATUS_CANCELED
        elif state == 0:
            status = ORDER_STATUS_PARTIAL_FILLED
        elif state == 3:
            status = ORDER_STATUS_SUBMITTED
        elif state == 2:            
            status = ORDER_STATUS_FILLED
        else:
            e = Error("status error! order_info: {}".format(order_info))
            logger.error(e, caller=self)
            SingleTask.run(self._error_callback, e)
            return None

        order = self._orders.get(order_id)
        if not order:
            info = {
                "platform": self._platform,
                "account": self._account,
                "strategy": self._strategy,
                "order_id": order_id,
                "action": action,
                "symbol": self._symbol,
                "price": "%.8f" % float(order_info[1]),
                "quantity": "%.8f" % float(order_info[2]),
                "remain": remain,
                "status": status
            }
            order = Order(**info)
            self._orders[order_id] = order
        order.remain = remain
        order.status = status
        order.avg_price = avg_price
        order.ctime = ctime
        order.utime = utime

        SingleTask.run(self._order_update_callback, copy.copy(order))
        if status in [ORDER_STATUS_FAILED, ORDER_STATUS_CANCELED, ORDER_STATUS_FILLED]:
            self._orders.pop(order_id)
    async def requestorderstatus(self):
        """{
            "accesskey": "ceb1569d-7c17-xxxx-b4a1-xxxxxxxxx",
            "binary": "false",
            "channel": "push_user_record",
            "event": "addChannel",
            "isZip": "false",
            "market": "zbqcdefault",
            "sign":"签名"
            }
        """
        reqchannel = "%sdefault" % self._raw_symbol 
        param = {
            "accesskey":self._access_key,
            "binary": "false",
            "channel": "push_user_record",
            "event": "addChannel",
            "isZip": "false",
            "market": reqchannel         
        }
        l = []
        for key in sorted(param.keys()):
            l.append('"%s":"%s"' %(key, param[key]))
        sign = ','.join(l)
        sign = '{' + sign + '}' 
        SHA_secret = self._rest_api.digest(self._secret_key)
        signature = self._rest_api.hmacSign(sign, SHA_secret)       
        param["sign"] = signature
        info = json.dumps(param)
        await self._ws.send(info)
    async def requestpositiontatus(self):     
        param = {
            "accesskey":self._access_key,
            "binary": "false",
            "channel": "push_user_asset",
            "event": "addChannel",
            "isZip": "false"                 
        }
        l = []
        for key in sorted(param.keys()):
            l.append('"%s":"%s"' %(key, param[key]))
        sign = ','.join(l)
        sign = '{' + sign + '}' 
        SHA_secret = self._rest_api.digest(self._secret_key)
        signature = self._rest_api.hmacSign(sign, SHA_secret)       
        param["sign"] = signature
        info = json.dumps(param)
        await self._ws.send(info)
    def _update_asset(self, asset_info):
        """asset update.
        Args:
            order_info: asset information.
        Returns:
            None.
        Note:
            asset-state: asset status, `available` / `freez` / `total`
        """
        pos_info = {               
                "available": asset_info["available"],
                "freez": asset_info["freez"],
                "total": float(asset_info["freez"]) + float(asset_info["available"]),
                "showName": asset_info["showName"]              
        }
        SingleTask.run(self._asset_update_callback, pos_info)

class ZbMarket:
    def __init__(self, **kwargs):
        """Initialize Trade module."""   
        e = None
        if not kwargs.get("symbol"):
            e = Error("param symbol miss")
        if not kwargs.get("host"):
            kwargs["host"] = "https://api.zb.today"
        if not kwargs.get("wss"):
            kwargs["wss"] = "wss://api.zb.today/websocket"
        if e:
            logger.error(e, caller=self)
            return
        self._init_callback = kwargs["init_callback"]
        self._platform = kwargs["platform"]
        self._symbol = kwargs["symbol"]
        self._host = kwargs["host"]
        self._wss = kwargs["wss"]     

        self._raw_symbol = self._symbol.replace("/", "").lower() 
        url = self._wss 
        self._ws = Websocket(url, self.connected_callback, process_binary_callback=self.process_binary, process_callback=self.process_callback)
    @async_method_locker("ZbMarket.process_binary.locker")
    async def process_binary(self, raw):
        """Process binary message that received from websocket.

        Args:
            raw: Binary message received from websocket.

        Returns:
            None.
        """
        msg=raw        
        #logger.debug("msg:", msg, caller=self)
        
    async def connected_callback(self):
        """After websocket connection created successfully, we will send a message to server for authentication."""
        SingleTask.run(self._init_callback, True)
        logger.debug("market web connect", caller=self)

    @async_method_locker("ZbMarket.process_callback.locker")      
    async def process_callback(self, raw):
        msg=raw
        channel = msg.get("channel")
        type = channel.split('_')        
        if type[-1] == "depth":
            asks = msg["asks"]
            bids = msg["bids"]
            timestamp = msg["timestamp"]
            symbols = type[-2]
            asks.reverse()
            if self._raw_symbol == symbols:
                symbols = self._symbol
            from aioquant.event import EventOrderbook
            EventOrderbook(Orderbook(self._platform, symbols, asks, bids, timestamp)).publish()
    @async_method_locker("ZbMarket.request_market_by_websocket.locker")
    async def request_market_by_websocket(self, channelType):         
        if channelType == "orderbook":
            req = "{'event':'addChannel','channel':'%s_depth'}" % self._raw_symbol                    
        if channelType == "trade":
            req = "{'event':'addChannel','channel':'%s_trades'}" % self._raw_symbol  
        if channelType == "kline":
            req = "{'event':'addChannel','channel':'%s_ticker'}" % self._raw_symbol        
        await self._ws.send(req)
        #logger.debug("req:", req, caller=self)
        return True, None