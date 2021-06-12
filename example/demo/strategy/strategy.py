# -*- coding:utf-8 -*-

# 策略实现

from aioquant import const
from aioquant.utils import logger
from aioquant.configure import config
from aioquant.market import Market
from aioquant.trade import Trade
from aioquant.const import BINANCE
from aioquant.order import Order
from aioquant.market import Orderbook
from aioquant.order import ORDER_ACTION_BUY, ORDER_ACTION_SELL, ORDER_STATUS_FAILED, ORDER_STATUS_CANCELED, ORDER_STATUS_FILLED
from aioquant.utils.decorator import async_method_locker
from aioquant.error import Error


class MyStrategy:

    def __init__(self):
        """ 初始化
        """
        self.strategy = "my_strategy"
        self.platform = config.accounts[0]["platform"]
        self.account = config.accounts[0]["account"]
        self.access_key = config.accounts[0]["access_key"]
        self.secret_key = config.accounts[0]["secret_key"]
        self.symbol = "EOS/QC"
        self.passphrase = config.accounts[0]["passphrase"]
        self.order_id = None  # 创建订单的id
        self.create_order_price = "0.0"  # 创建订单的价格
        self.rawsymbol = self.symbol.replace("/","").lower()
        # 交易模块
        cc = {
            "strategy": self.strategy,
            "platform": self.platform,
            "symbol": self.symbol,
            "account": self.account,
            "access_key": self.access_key,
            "secret_key": self.secret_key,
            "passphrase": self.passphrase,
            "order_update_callback": self.on_event_order_update,
            "init_callback": self.on_init_callback,
            "error_callback": self.on_order_callback,
            "asset_update_callback": self.on_asset_update_callback
        }
        self.trader = Trade(**cc)
        self.buyflag = 0
        #请求行情
        #self.trader._t.request_market_by_websocket("orderbook")    
        # 订阅行情 
       # 市场模块
        ma = {
            "strategy": self.strategy,
            "platform": self.platform,
            "symbol": self.symbol,
            "market_type": "orderbook",     
            "init_callback": self.on_market_init_callback,     
            "update_callback": self.on_event_orderbook_update            
        }
        Market(**ma)

    @async_method_locker("MyStrategy.init_callback.locker")  
    async def on_init_callback(self, success: bool, **kwagrs): 
        logger.debug("inint err:", success, caller=self)  
    
    
    @async_method_locker("MyStrategy.on_event_orderbook_update.locker")  
    async def on_event_orderbook_update(self, orderbook: Orderbook):
        """ 订单薄更新
        """
        logger.debug("orderbook_recived:", orderbook, caller=self)
        bid3_price = orderbook.bids[2][0]  # 买三价格
        bid4_price = orderbook.bids[3][0]  # 买四价格

        ask3_price = orderbook.asks[7][0]  # 卖三价格
        ask4_price = orderbook.asks[10][0]  # 卖四价格

        # 判断是否需要撤单
        if self.order_id:
             if float(self.create_order_price) > float(ask4_price) or float(self.create_order_price) < float(ask3_price):
                 return
             _, error = await self.trader.revoke_order(self.order_id)
             if error:
                 logger.error("revoke order error! error:", error, caller=self)
                 return
             self.order_id = None             
        else:
            # # 创建新订单
            price = (float(ask3_price) + float(ask4_price)) /2.0
            quantity = "1.5"  # 假设委托数量为0.1
            action = ORDER_ACTION_BUY     
            order_id, error = await self.trader.create_order(action, price, quantity)            
            if error:
                logger.error("create order error! error:", error, caller=self)
                return
            self.order_id = order_id
            self.create_order_price = price           
    async def on_event_order_update(self, order: Order):
        """ 订单状态更新
        """
        #logger.debug("order id:", self.order_id, caller=self)
        if order.order_id == self.order_id:
            logger.debug("order update:", order, caller=self)                 
         # 如果订单失败、订单取消、订单完成交易
        #if order.status in [ORDER_STATUS_FAILED, ORDER_STATUS_CANCELED, ORDER_STATUS_FILLED]:
            #self.order_id = None


    async def on_order_callback(self, error: Error, **kwagrs):
        logger.debug("order error:", error, caller=self)

    async def on_asset_update_callback(self, info, **kwagrs):        
        ques,base = self.symbol.split("/")
        if info["showName"] == ques or info["showName"] == base:
            logger.debug("asset info:", info, caller=self)
    @async_method_locker("MyStrategy.market_init_callback.locker")  
    async def on_market_init_callback(self, success: bool, **kwagrs): 
        logger.debug("inint market:", success, caller=self)  